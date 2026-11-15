"""
Repositório Relacional Híbrido PostgreSQL / SQLite (SITRIB).

Conecta prioritariamente ao PostgreSQL via `DATABASE_URL` (SQLAlchemy + psycopg2).
Caso o servidor PostgreSQL não esteja acessível no ambiente de teste local,
opera em fallback transparente com SQLite (`sitrib.db`), mantendo 100% de
compatibilidade com toda a suíte de testes e com o BuscaService.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import create_engine, text
from src.repositories.sqlite_repository import RepositorioSQLite

SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS contribuinte (
    id_contribuinte SERIAL PRIMARY KEY,
    cpf_cnpj VARCHAR(18) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    tipo_pessoa VARCHAR(10) DEFAULT 'FISICA',
    email VARCHAR(100),
    telefone VARCHAR(20),
    endereco_correspondencia VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS imovel (
    id_imovel SERIAL PRIMARY KEY,
    inscricao_imobiliaria VARCHAR(50) NOT NULL UNIQUE,
    id_contribuinte INT NOT NULL REFERENCES contribuinte(id_contribuinte) ON DELETE CASCADE,
    endereco VARCHAR(255) NOT NULL,
    bairro VARCHAR(100),
    cep VARCHAR(10),
    tipo_imovel VARCHAR(20) DEFAULT 'RESIDENCIAL',
    valor_venal NUMERIC(12, 2),
    area_terreno NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS divida (
    id_divida SERIAL PRIMARY KEY,
    id_imovel INT NOT NULL REFERENCES imovel(id_imovel) ON DELETE CASCADE,
    exercicio_ano INT NOT NULL,
    valor_original NUMERIC(10, 2) NOT NULL,
    valor_atualizado NUMERIC(10, 2) NOT NULL,
    tipo_tributo VARCHAR(50) DEFAULT 'IPTU',
    status_divida VARCHAR(30) DEFAULT 'EM_ABERTO',
    data_vencimento DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processo (
    id_processo SERIAL PRIMARY KEY,
    numero_processo VARCHAR(50) NOT NULL UNIQUE,
    id_divida INT NOT NULL REFERENCES divida(id_divida) ON DELETE CASCADE,
    vara_judicial VARCHAR(100),
    status_processo VARCHAR(50) DEFAULT 'EM_ANDAMENTO',
    data_ajuizamento DATE NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class RepositorioPostgreSQL:
    """Camada de persistência oficial PostgreSQL (com fallback automático para RepositorioSQLite)."""

    def __init__(self, database_url: Optional[str] = None, caminho_sqlite: Optional[Union[str, Path]] = None) -> None:
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/sitrib",
        )
        self.engine = None
        self.modo_ativo = "PostgreSQL"
        self._fallback_sqlite: Optional[RepositorioSQLite] = None

        try:
            eng = create_engine(self.database_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
            with eng.begin() as conn:
                for stmt in [s.strip() for s in SCHEMA_POSTGRES.split(";") if s.strip()]:
                    conn.execute(text(stmt))
            self.engine = eng
        except Exception:
            self.modo_ativo = "SQLite (Fallback — configure DATABASE_URL para PostgreSQL ativo)"
            caminho_padrao = Path(caminho_sqlite or Path(__file__).resolve().parent.parent.parent / "sitrib.db")
            if not caminho_padrao.exists():
                from scripts.popular_banco import criar_banco, popular_banco
                con = criar_banco()
                popular_banco(con)
                con.close()
            self._fallback_sqlite = RepositorioSQLite(caminho_padrao)

    def buscar_contribuinte(self, cpf_cnpj: str) -> Optional[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.buscar_contribuinte(cpf_cnpj)
        if not cpf_cnpj:
            return None
        alvo_digitos = "".join(filter(str.isdigit, cpf_cnpj))
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM contribuinte")).mappings().all()
            for row in rows:
                if "".join(filter(str.isdigit, row["cpf_cnpj"])) == alvo_digitos:
                    return dict(row)
        return None

    def buscar_imovel(self, inscricao_cci: str) -> Optional[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.buscar_imovel(inscricao_cci)
        if not inscricao_cci:
            return None
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    """SELECT imovel.*, contribuinte.cpf_cnpj AS cpf_cnpj_proprietario
                       FROM imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte
                       WHERE imovel.inscricao_imobiliaria = :cci"""
                ),
                {"cci": inscricao_cci.strip()},
            ).mappings().first()
            if not row:
                return None
            return {
                "inscricao_cci": row["inscricao_imobiliaria"],
                "endereco": row["endereco"],
                "tipo_imovel": row["tipo_imovel"],
                "valor_venal": float(row["valor_venal"] or 0),
                "cpf_cnpj_proprietario": row["cpf_cnpj_proprietario"],
                "bairro": row["bairro"],
                "cep": row["cep"],
            }

    def listar_dividas_por_imovel(self, inscricao_cci: str) -> List[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.listar_dividas_por_imovel(inscricao_cci)
        if not inscricao_cci:
            return []
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT divida.*, imovel.inscricao_imobiliaria, contribuinte.cpf_cnpj AS cpf_cnpj_contribuinte
                       FROM divida
                       JOIN imovel ON imovel.id_imovel = divida.id_imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte
                       WHERE imovel.inscricao_imobiliaria = :cci"""
                ),
                {"cci": inscricao_cci.strip()},
            ).mappings().all()
            return [
                {
                    "codigo_debito": f"DIVIDA-{r['id_divida']}",
                    "ano_exercicio": r["exercicio_ano"],
                    "valor_original": float(r["valor_original"]),
                    "juros_multa": round(float(r["valor_atualizado"]) - float(r["valor_original"]), 2),
                    "status": r["status_divida"],
                    "inscricao_cci": r["inscricao_imobiliaria"],
                    "cpf_cnpj_contribuinte": r["cpf_cnpj_contribuinte"],
                    "tipo_tributo": r["tipo_tributo"],
                }
                for r in rows
            ]

    def listar_processos_por_imovel(self, inscricao_cci: str) -> List[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.listar_processos_por_imovel(inscricao_cci)
        if not inscricao_cci:
            return []
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT processo.*, divida.id_divida AS id_divida_origem,
                              contribuinte.cpf_cnpj AS cpf_cnpj_contribuinte
                       FROM processo
                       JOIN divida ON divida.id_divida = processo.id_divida
                       JOIN imovel ON imovel.id_imovel = divida.id_imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte
                       WHERE imovel.inscricao_imobiliaria = :cci"""
                ),
                {"cci": inscricao_cci.strip()},
            ).mappings().all()
            return [
                {
                    "numero_processo": r["numero_processo"],
                    "vara": r["vara_judicial"],
                    "data_autuacao": str(r["data_ajuizamento"]),
                    "codigo_debito": f"DIVIDA-{r['id_divida_origem']}",
                    "cpf_cnpj_contribuinte": r["cpf_cnpj_contribuinte"],
                    "status_processo": r["status_processo"],
                }
                for r in rows
            ]

    def listar_debitos_completos(self) -> List[Dict[str, Any]]:
        """Retorna visão consolidada (LEFT JOIN) de todas as dívidas com imóvel, contribuinte e processo para auditoria."""
        if self._fallback_sqlite:
            return self._fallback_sqlite.listar_debitos_completos()
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT
                           d.id_divida,
                           d.exercicio_ano,
                           d.valor_original,
                           d.valor_atualizado,
                           d.tipo_tributo,
                           d.status_divida,
                           d.data_vencimento,
                           i.inscricao_imobiliaria,
                           i.endereco AS endereco_imovel,
                           i.bairro,
                           i.cep,
                           i.tipo_imovel,
                           i.valor_venal,
                           c.cpf_cnpj AS cpf_cnpj_contribuinte,
                           c.nome AS nome_contribuinte,
                           c.tipo_pessoa,
                           c.email AS email_contribuinte,
                           c.telefone AS telefone_contribuinte,
                           p.numero_processo,
                           p.vara_judicial,
                           p.status_processo,
                           p.data_ajuizamento
                       FROM divida d
                       JOIN imovel i ON i.id_imovel = d.id_imovel
                       JOIN contribuinte c ON c.id_contribuinte = i.id_contribuinte
                       LEFT JOIN processo p ON p.id_divida = d.id_divida"""
                )
            ).mappings().all()
            resultado: List[Dict[str, Any]] = []
            for r in rows:
                data_venc = str(r["data_vencimento"] or f"{r['exercicio_ano']}-12-31")
                partes_data = data_venc.split("-")
                mes_venc = int(partes_data[1]) if len(partes_data) >= 2 and partes_data[1].isdigit() else 12
                val_orig = float(r["valor_original"] or 0.0)
                val_atual = float(r["valor_atualizado"] or val_orig)
                tributo = (r["tipo_tributo"] or "IPTU").upper()
                origem_api = "portal_novo" if int(r["exercicio_ano"]) >= 2024 or tributo == "ISS" else "api_antiga"
                resultado.append({
                    "id_divida": r["id_divida"],
                    "codigo_debito": f"DIVIDA-{r['id_divida']}",
                    "origem_api": origem_api,
                    "exercicio_ano": int(r["exercicio_ano"]),
                    "data_vencimento": data_venc,
                    "mes_vencimento": mes_venc,
                    "valor_original": round(val_orig, 2),
                    "juros_multa": round(val_atual - val_orig, 2),
                    "valor_atualizado": round(val_atual, 2),
                    "tipo_tributo": r["tipo_tributo"],
                    "status_divida": r["status_divida"],
                    "inscricao_cci": r["inscricao_imobiliaria"],
                    "endereco_imovel": r["endereco_imovel"],
                    "bairro": r["bairro"] or "Plano Diretor",
                    "cep": r["cep"] or "77000-000",
                    "tipo_imovel": r["tipo_imovel"] or "RESIDENCIAL",
                    "valor_venal": float(r["valor_venal"] or 0.0),
                    "cpf_cnpj_contribuinte": r["cpf_cnpj_contribuinte"],
                    "nome_contribuinte": r["nome_contribuinte"],
                    "tipo_pessoa": r["tipo_pessoa"] or "FISICA",
                    "email_contribuinte": r["email_contribuinte"],
                    "telefone_contribuinte": r["telefone_contribuinte"],
                    "tem_processo": bool(r["numero_processo"]),
                    "numero_processo": r["numero_processo"],
                    "vara_judicial": r["vara_judicial"],
                    "status_processo": r["status_processo"],
                    "data_ajuizamento": str(r["data_ajuizamento"]) if r["data_ajuizamento"] else None,
                })
            return resultado

    def obter_opcoes_filtros_auditoria(self) -> Dict[str, Any]:
        """Extrai dinamicamente do banco todas as categorias e valores únicos das colunas para filtros do Auditor."""
        if self._fallback_sqlite:
            return self._fallback_sqlite.obter_opcoes_filtros_auditoria()
        debitos = self.listar_debitos_completos()
        anos = sorted({d["exercicio_ano"] for d in debitos} | {2026}, reverse=True)
        meses = sorted({d["mes_vencimento"] for d in debitos})
        tributos = sorted({d["tipo_tributo"] for d in debitos if d.get("tipo_tributo")})
        status_div = sorted({d["status_divida"] for d in debitos if d.get("status_divida")})
        bairros = sorted({d["bairro"] for d in debitos if d.get("bairro")} | {im.get("bairro", "") for im in self.imoveis.values() if im.get("bairro")})
        tipos_imovel = sorted({d["tipo_imovel"] for d in debitos if d.get("tipo_imovel")} | {im.get("tipo_imovel", "") for im in self.imoveis.values() if im.get("tipo_imovel")})
        tipos_pessoa = sorted({c.get("tipo_pessoa", "FISICA") for c in self.contribuintes.values()})
        status_proc = sorted({d["status_processo"] for d in debitos if d.get("status_processo")})
        varas = sorted({d["vara_judicial"] for d in debitos if d.get("vara_judicial")})

        return {
            "exercicios_ano": anos,
            "meses_vencimento_ativos": meses,
            "tipos_tributo": tributos,
            "status_divida": status_div,
            "bairros": bairros,
            "tipos_imovel": tipos_imovel,
            "tipos_pessoa": tipos_pessoa,
            "status_processo": status_proc,
            "varas_judiciais": varas,
            "fontes_coleta": ["dual", "portal_novo", "api_antiga"],
            "colunas_banco": {
                "contribuinte": ["id_contribuinte", "cpf_cnpj", "nome", "tipo_pessoa", "email", "telefone", "endereco_correspondencia"],
                "imovel": ["id_imovel", "inscricao_imobiliaria", "id_contribuinte", "endereco", "bairro", "cep", "tipo_imovel", "valor_venal", "area_terreno"],
                "divida": ["id_divida", "id_imovel", "exercicio_ano", "valor_original", "valor_atualizado", "tipo_tributo", "status_divida", "data_vencimento"],
                "processo": ["id_processo", "numero_processo", "id_divida", "vara_judicial", "status_processo", "data_ajuizamento", "observacoes"],
            },
        }

    def listar_imoveis_por_contribuinte(self, cpf_cnpj: str) -> List[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.listar_imoveis_por_contribuinte(cpf_cnpj)
        c = self.buscar_contribuinte(cpf_cnpj)
        if not c:
            return []
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT imovel.* FROM imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte
                       WHERE contribuinte.cpf_cnpj = :cpf"""
                ),
                {"cpf": c["cpf_cnpj"]},
            ).mappings().all()
            return [
                {
                    "inscricao_cci": r["inscricao_imobiliaria"],
                    "endereco": r["endereco"],
                    "tipo_imovel": r["tipo_imovel"],
                    "valor_venal": float(r["valor_venal"] or 0),
                    "cpf_cnpj_proprietario": c["cpf_cnpj"],
                    "bairro": r["bairro"],
                    "cep": r["cep"],
                }
                for r in rows
            ]

    @property
    def contribuintes(self) -> Dict[str, Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.contribuintes
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM contribuinte")).mappings().all()
            return {r["cpf_cnpj"]: dict(r) for r in rows}

    @property
    def imoveis(self) -> Dict[str, Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.imoveis
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT imovel.*, contribuinte.cpf_cnpj AS cpf_cnpj_proprietario
                       FROM imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte"""
                )
            ).mappings().all()
            return {
                r["inscricao_imobiliaria"]: {
                    "inscricao_cci": r["inscricao_imobiliaria"],
                    "endereco": r["endereco"],
                    "tipo_imovel": r["tipo_imovel"],
                    "valor_venal": float(r["valor_venal"] or 0),
                    "cpf_cnpj_proprietario": r["cpf_cnpj_proprietario"],
                    "bairro": r["bairro"],
                    "cep": r["cep"],
                }
                for r in rows
            }

    @property
    def dividas(self) -> List[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.dividas
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT divida.*, imovel.inscricao_imobiliaria, contribuinte.cpf_cnpj AS cpf_cnpj_contribuinte
                       FROM divida
                       JOIN imovel ON imovel.id_imovel = divida.id_imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte"""
                )
            ).mappings().all()
            return [
                {
                    "codigo_debito": f"DIVIDA-{r['id_divida']}",
                    "ano_exercicio": r["exercicio_ano"],
                    "valor_original": float(r["valor_original"]),
                    "juros_multa": round(float(r["valor_atualizado"]) - float(r["valor_original"]), 2),
                    "status": r["status_divida"],
                    "inscricao_cci": r["inscricao_imobiliaria"],
                    "cpf_cnpj_contribuinte": r["cpf_cnpj_contribuinte"],
                    "tipo_tributo": r["tipo_tributo"],
                }
                for r in rows
            ]

    @property
    def processos(self) -> List[Dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.processos
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT processo.*, divida.id_divida AS id_divida_origem,
                              contribuinte.cpf_cnpj AS cpf_cnpj_contribuinte
                       FROM processo
                       JOIN divida ON divida.id_divida = processo.id_divida
                       JOIN imovel ON imovel.id_imovel = divida.id_imovel
                       JOIN contribuinte ON contribuinte.id_contribuinte = imovel.id_contribuinte"""
                )
            ).mappings().all()
            return [
                {
                    "numero_processo": r["numero_processo"],
                    "vara": r["vara_judicial"],
                    "data_autuacao": str(r["data_ajuizamento"]),
                    "codigo_debito": f"DIVIDA-{r['id_divida_origem']}",
                    "cpf_cnpj_contribuinte": r["cpf_cnpj_contribuinte"],
                    "status_processo": r["status_processo"],
                }
                for r in rows
            ]

    def listar_debitos_completos(self) -> List[Dict[str, Any]]:
        """Retorna visão consolidada (LEFT JOIN) de todas as dívidas com imóvel, contribuinte e processo para auditoria."""
        if self._fallback_sqlite:
            return self._fallback_sqlite.listar_debitos_completos()
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT
                           d.id_divida,
                           d.exercicio_ano,
                           d.valor_original,
                           d.valor_atualizado,
                           d.tipo_tributo,
                           d.status_divida,
                           d.data_vencimento,
                           i.inscricao_imobiliaria,
                           i.endereco AS endereco_imovel,
                           i.bairro,
                           i.cep,
                           i.tipo_imovel,
                           i.valor_venal,
                           c.cpf_cnpj AS cpf_cnpj_contribuinte,
                           c.nome AS nome_contribuinte,
                           c.tipo_pessoa,
                           c.email AS email_contribuinte,
                           c.telefone AS telefone_contribuinte,
                           p.numero_processo,
                           p.vara_judicial,
                           p.status_processo,
                           p.data_ajuizamento
                       FROM divida d
                       JOIN imovel i ON i.id_imovel = d.id_imovel
                       JOIN contribuinte c ON c.id_contribuinte = i.id_contribuinte
                       LEFT JOIN processo p ON p.id_divida = d.id_divida"""
                )
            ).mappings().all()
            resultado: List[Dict[str, Any]] = []
            for r in rows:
                data_venc = str(r["data_vencimento"] or f"{r['exercicio_ano']}-12-31")
                partes_data = data_venc.split("-")
                mes_venc = int(partes_data[1]) if len(partes_data) >= 2 and partes_data[1].isdigit() else 12
                val_orig = float(r["valor_original"] or 0.0)
                val_atual = float(r["valor_atualizado"] or val_orig)
                tributo = (r["tipo_tributo"] or "IPTU").upper()
                origem_api = "portal_novo" if int(r["exercicio_ano"]) >= 2024 or tributo == "ISS" else "api_antiga"
                resultado.append({
                    "id_divida": r["id_divida"],
                    "codigo_debito": f"DIVIDA-{r['id_divida']}",
                    "origem_api": origem_api,
                    "exercicio_ano": int(r["exercicio_ano"]),
                    "data_vencimento": data_venc,
                    "mes_vencimento": mes_venc,
                    "valor_original": round(val_orig, 2),
                    "juros_multa": round(val_atual - val_orig, 2),
                    "valor_atualizado": round(val_atual, 2),
                    "tipo_tributo": r["tipo_tributo"],
                    "status_divida": r["status_divida"],
                    "inscricao_cci": r["inscricao_imobiliaria"],
                    "endereco_imovel": r["endereco_imovel"],
                    "bairro": r["bairro"] or "Plano Diretor",
                    "cep": r["cep"] or "77000-000",
                    "tipo_imovel": r["tipo_imovel"] or "RESIDENCIAL",
                    "valor_venal": float(r["valor_venal"] or 0.0),
                    "cpf_cnpj_contribuinte": r["cpf_cnpj_contribuinte"],
                    "nome_contribuinte": r["nome_contribuinte"],
                    "tipo_pessoa": r["tipo_pessoa"] or "FISICA",
                    "email_contribuinte": r["email_contribuinte"],
                    "telefone_contribuinte": r["telefone_contribuinte"],
                    "tem_processo": bool(r["numero_processo"]),
                    "numero_processo": r["numero_processo"],
                    "vara_judicial": r["vara_judicial"],
                    "status_processo": r["status_processo"],
                    "data_ajuizamento": str(r["data_ajuizamento"]) if r["data_ajuizamento"] else None,
                })
            return resultado

    def obter_opcoes_filtros_auditoria(self) -> Dict[str, Any]:
        """Extrai dinamicamente do banco todas as categorias e valores únicos das colunas para filtros do Auditor."""
        if self._fallback_sqlite:
            return self._fallback_sqlite.obter_opcoes_filtros_auditoria()
        debitos = self.listar_debitos_completos()
        anos = sorted({d["exercicio_ano"] for d in debitos} | {2026}, reverse=True)
        meses = sorted({d["mes_vencimento"] for d in debitos})
        tributos = sorted({d["tipo_tributo"] for d in debitos if d.get("tipo_tributo")})
        status_div = sorted({d["status_divida"] for d in debitos if d.get("status_divida")})
        bairros = sorted({d["bairro"] for d in debitos if d.get("bairro")} | {im.get("bairro", "") for im in self.imoveis.values() if im.get("bairro")})
        tipos_imovel = sorted({d["tipo_imovel"] for d in debitos if d.get("tipo_imovel")} | {im.get("tipo_imovel", "") for im in self.imoveis.values() if im.get("tipo_imovel")})
        tipos_pessoa = sorted({c.get("tipo_pessoa", "FISICA") for c in self.contribuintes.values()})
        status_proc = sorted({d["status_processo"] for d in debitos if d.get("status_processo")})
        varas = sorted({d["vara_judicial"] for d in debitos if d.get("vara_judicial")})

        return {
            "exercicios_ano": anos,
            "meses_vencimento_ativos": meses,
            "tipos_tributo": tributos,
            "status_divida": status_div,
            "bairros": bairros,
            "tipos_imovel": tipos_imovel,
            "tipos_pessoa": tipos_pessoa,
            "status_processo": status_proc,
            "varas_judiciais": varas,
            "fontes_coleta": ["dual", "portal_novo", "api_antiga"],
            "colunas_banco": {
                "contribuinte": ["id_contribuinte", "cpf_cnpj", "nome", "tipo_pessoa", "email", "telefone", "endereco_correspondencia"],
                "imovel": ["id_imovel", "inscricao_imobiliaria", "id_contribuinte", "endereco", "bairro", "cep", "tipo_imovel", "valor_venal", "area_terreno"],
                "divida": ["id_divida", "id_imovel", "exercicio_ano", "valor_original", "valor_atualizado", "tipo_tributo", "status_divida", "data_vencimento"],
                "processo": ["id_processo", "numero_processo", "id_divida", "vara_judicial", "status_processo", "data_ajuizamento", "observacoes"],
            },
        }
