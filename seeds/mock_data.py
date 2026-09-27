"""
Módulo de Seeds e Dados Mockados (SITRIB - Projeto Integrador UFT).

Responsável: Adriel Morais (PO / Dev)
Finalidade: Fornecer massa de dados realistas e funções mockadas/preparadas de inserção
para as 4 entidades centrais do sistema:
  1. Contribuinte (Pessoa Física e Jurídica)
  2. Imóvel (Inscrição Municipal / CCI)
  3. Dívida (Débitos Tributários Ativos e Ajuizados)
  4. Processo (Execuções Fiscais e Ações de Cobrança)

Nota de Integração:
Este módulo não cria tabelas ou esquemas no banco de dados (responsabilidade de Rayssa).
Ele fornece estruturas desacopladas e prontas para instanciar as models e popular o
banco assim que as classes/tabelas finais forem entregues.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger("sitrib.seeds")


# ==============================================================================
# 1. Estruturas Tipadas de Dados (DTOs / Mocks)
# ==============================================================================

@dataclass
class ContribuinteMock:
    nome: str
    cpf_cnpj: str
    email: str
    telefone: str
    tipo_pessoa: str = "FISICA"  # "FISICA" ou "JURIDICA"


@dataclass
class ImovelMock:
    inscricao_cci: str
    endereco: str
    tipo_imovel: str  # "RESIDENCIAL", "COMERCIAL", "TERRENO", "MISTO"
    valor_venal: float
    cpf_cnpj_proprietario: str
    bairro: str = "Plano Diretor"
    cep: str = "77000-000"


@dataclass
class DividaMock:
    codigo_debito: str
    ano_exercicio: int
    valor_original: float
    juros_multa: float
    status: str  # "ATIVO" ou "AJUIZADO"
    inscricao_cci: str
    cpf_cnpj_contribuinte: str
    tipo_tributo: str = "IPTU"  # "IPTU", "ISS", "TAXA_LIXO"

    @property
    def valor_total(self) -> float:
        return round(self.valor_original + self.juros_multa, 2)


@dataclass
class ProcessoMock:
    numero_processo: str
    vara: str
    data_autuacao: str  # Formato ISO: YYYY-MM-DD
    codigo_debito: str
    cpf_cnpj_contribuinte: str
    status_processo: str = "EM_ANDAMENTO"  # "EM_ANDAMENTO", "SUSPENSO", "QUITADO"


# ==============================================================================
# 2. Massa de Dados Realistas (Palmas / TO)
# ==============================================================================

CONTRIBUINTES_SEED: List[Dict[str, Any]] = [
    {
        "nome": "Carlos Eduardo Siqueira",
        "cpf_cnpj": "123.456.789-01",
        "email": "carlos.siqueira@email.com",
        "telefone": "(63) 98111-2030",
        "tipo_pessoa": "FISICA",
    },
    {
        "nome": "Maria Auxiliadora Fernandes",
        "cpf_cnpj": "987.654.321-09",
        "email": "maria.fernandes@email.com",
        "telefone": "(63) 99222-3040",
        "tipo_pessoa": "FISICA",
    },
    {
        "nome": "Tocantins Engenharia e Serviços Ltda",
        "cpf_cnpj": "12.345.678/0001-90",
        "email": "contato@toengenharia.com.br",
        "telefone": "(63) 3215-4000",
        "tipo_pessoa": "JURIDICA",
    },
    {
        "nome": "Araguaia Comércio de Alimentos Eireli",
        "cpf_cnpj": "98.765.432/0001-10",
        "email": "financeiro@araguaiaalimentos.com.br",
        "telefone": "(63) 3218-9900",
        "tipo_pessoa": "JURIDICA",
    },
    {
        "nome": "Juliana Ribeiro Prado",
        "cpf_cnpj": "456.789.012-34",
        "email": "juliana.prado@email.com",
        "telefone": "(63) 98455-1234",
        "tipo_pessoa": "FISICA",
    },
]

IMOVEIS_SEED: List[Dict[str, Any]] = [
    {
        "inscricao_cci": "CCI-104-NORTE-01",
        "endereco": "Quadra 104 Norte, Alameda 02, Lote 15",
        "tipo_imovel": "RESIDENCIAL",
        "valor_venal": 280000.00,
        "cpf_cnpj_proprietario": "123.456.789-01",
        "bairro": "Plano Diretor Norte",
        "cep": "77006-020",
    },
    {
        "inscricao_cci": "CCI-208-SUL-42",
        "endereco": "Quadra 208 Sul, Avenida LO-05, Lote 08",
        "tipo_imovel": "RESIDENCIAL",
        "valor_venal": 395000.00,
        "cpf_cnpj_proprietario": "123.456.789-01",
        "bairro": "Plano Diretor Sul",
        "cep": "77020-510",
    },
    {
        "inscricao_cci": "CCI-COMERCIAL-JK-10",
        "endereco": "Avenida JK, Quadra 103 Sul, Bloco AC, Sala 204",
        "tipo_imovel": "COMERCIAL",
        "valor_venal": 750000.00,
        "cpf_cnpj_proprietario": "12.345.678/0001-90",
        "bairro": "Centro Comercial",
        "cep": "77015-012",
    },
    {
        "inscricao_cci": "CCI-LOTE-INDUSTRIAL-07",
        "endereco": "Distrito Industrial de Palmas, Quadra 04, Módulo 12",
        "tipo_imovel": "TERRENO",
        "valor_venal": 520000.00,
        "cpf_cnpj_proprietario": "98.765.432/0001-10",
        "bairro": "Distrito Industrial",
        "cep": "77060-100",
    },
    {
        "inscricao_cci": "CCI-GRACIOSA-LAGO-88",
        "endereco": "Orla 14, Alameda dos Ipês, Lote 22",
        "tipo_imovel": "RESIDENCIAL",
        "valor_venal": 640000.00,
        "cpf_cnpj_proprietario": "987.654.321-09",
        "bairro": "Graciosa",
        "cep": "77001-140",
    },
]

DIVIDAS_SEED: List[Dict[str, Any]] = [
    {
        "codigo_debito": "DEB-2023-IPTU-104",
        "ano_exercicio": 2023,
        "valor_original": 2450.00,
        "juros_multa": 380.50,
        "status": "ATIVO",
        "inscricao_cci": "CCI-104-NORTE-01",
        "cpf_cnpj_contribuinte": "123.456.789-01",
        "tipo_tributo": "IPTU",
    },
    {
        "codigo_debito": "DEB-2022-IPTU-104",
        "ano_exercicio": 2022,
        "valor_original": 2200.00,
        "juros_multa": 650.00,
        "status": "AJUIZADO",
        "inscricao_cci": "CCI-104-NORTE-01",
        "cpf_cnpj_contribuinte": "123.456.789-01",
        "tipo_tributo": "IPTU",
    },
    {
        "codigo_debito": "DEB-2024-ISS-JK10",
        "ano_exercicio": 2024,
        "valor_original": 14800.00,
        "juros_multa": 1250.75,
        "status": "ATIVO",
        "inscricao_cci": "CCI-COMERCIAL-JK-10",
        "cpf_cnpj_contribuinte": "12.345.678/0001-90",
        "tipo_tributo": "ISS",
    },
    {
        "codigo_debito": "DEB-2021-TX-IND07",
        "ano_exercicio": 2021,
        "valor_original": 8300.00,
        "juros_multa": 2400.00,
        "status": "AJUIZADO",
        "inscricao_cci": "CCI-LOTE-INDUSTRIAL-07",
        "cpf_cnpj_contribuinte": "98.765.432/0001-10",
        "tipo_tributo": "TAXA_LIXO",
    },
]

PROCESSOS_SEED: List[Dict[str, Any]] = [
    {
        "numero_processo": "0012345-67.2023.8.27.2729",
        "vara": "1ª Vara de Execução Fiscal e Tributária de Palmas",
        "data_autuacao": "2023-04-18",
        "codigo_debito": "DEB-2022-IPTU-104",
        "cpf_cnpj_contribuinte": "123.456.789-01",
        "status_processo": "EM_ANDAMENTO",
    },
    {
        "numero_processo": "0098765-43.2022.8.27.2729",
        "vara": "2ª Vara de Execução Fiscal de Palmas",
        "data_autuacao": "2022-11-05",
        "codigo_debito": "DEB-2021-TX-IND07",
        "cpf_cnpj_contribuinte": "98.765.432/0001-10",
        "status_processo": "EM_ANDAMENTO",
    },
]


# ==============================================================================
# 3. Funções Utilitárias para Consumo dos Mocks
# ==============================================================================

def obter_contribuintes_mock() -> List[Dict[str, Any]]:
    """Retorna a lista de dicionários dos contribuintes mockados."""
    return [dict(item) for item in CONTRIBUINTES_SEED]


def obter_imoveis_mock() -> List[Dict[str, Any]]:
    """Retorna a lista de dicionários dos imóveis mockados."""
    return [dict(item) for item in IMOVEIS_SEED]


def obter_dividas_mock() -> List[Dict[str, Any]]:
    """Retorna a lista de dicionários das dívidas mockadas."""
    return [dict(item) for item in DIVIDAS_SEED]


def obter_processos_mock() -> List[Dict[str, Any]]:
    """Retorna a lista de dicionários dos processos fiscais mockados."""
    return [dict(item) for item in PROCESSOS_SEED]


def obter_dados_consolidados() -> Dict[str, List[Dict[str, Any]]]:
    """Retorna todos os dados de seed organizados por entidade."""
    return {
        "contribuintes": obter_contribuintes_mock(),
        "imoveis": obter_imoveis_mock(),
        "dividas": obter_dividas_mock(),
        "processos": obter_processos_mock(),
    }


# ==============================================================================
# 4. Engine Preparada para Injeção com as Models de Rayssa
# ==============================================================================

class BancoSimuladoEmMemoria:
    """
    Armazena em memória os dados mockados, simulando um banco de dados relacional
    com índices rápidos de busca por CPF/CNPJ e Inscrição CCI.
    Permite testes isolados antes da implementação final do banco pela Rayssa.
    """

    def __init__(self) -> None:
        self.contribuintes: Dict[str, Dict[str, Any]] = {}
        self.imoveis: Dict[str, Dict[str, Any]] = {}
        self.dividas: List[Dict[str, Any]] = []
        self.processos: List[Dict[str, Any]] = []

    def carregar_dados_iniciais(self) -> None:
        """Povoa as tabelas em memória com a massa de dados padrão."""
        for c in CONTRIBUINTES_SEED:
            self.contribuintes[c["cpf_cnpj"]] = dict(c)
        for i in IMOVEIS_SEED:
            self.imoveis[i["inscricao_cci"]] = dict(i)
        self.dividas = [dict(d) for d in DIVIDAS_SEED]
        self.processos = [dict(p) for p in PROCESSOS_SEED]

    def buscar_contribuinte(self, cpf_cnpj: str) -> Optional[Dict[str, Any]]:
        """Busca contribuinte por CPF ou CNPJ formatado ou apenas dígitos."""
        if not cpf_cnpj:
            return None
        alvo = cpf_cnpj.strip()
        # Busca exata
        if alvo in self.contribuintes:
            return dict(self.contribuintes[alvo])
        # Busca por dígitos desconsiderando pontuação
        alvo_digitos = "".join(filter(str.isdigit, alvo))
        for key, val in self.contribuintes.items():
            if "".join(filter(str.isdigit, key)) == alvo_digitos:
                return dict(val)
        return None

    def buscar_imovel(self, inscricao_cci: str) -> Optional[Dict[str, Any]]:
        """Busca imóvel por inscrição cadastral (CCI)."""
        if not inscricao_cci:
            return None
        return self.imoveis.get(inscricao_cci.strip())

    def listar_dividas_por_imovel(self, inscricao_cci: str) -> List[Dict[str, Any]]:
        """Retorna lista de débitos associados ao imóvel informado."""
        if not inscricao_cci:
            return []
        cci = inscricao_cci.strip()
        return [dict(d) for d in self.dividas if d["inscricao_cci"] == cci]

    def listar_processos_por_imovel(self, inscricao_cci: str) -> List[Dict[str, Any]]:
        """
        Retorna processos judiciais decorrentes de débitos do imóvel.
        Faz o cruzamento Imóvel -> Dívida -> Processo.
        """
        if not inscricao_cci:
            return []
        cci = inscricao_cci.strip()
        codigos_debito = {d["codigo_debito"] for d in self.dividas if d["inscricao_cci"] == cci}
        return [dict(p) for p in self.processos if p["codigo_debito"] in codigos_debito]

    def listar_imoveis_por_contribuinte(self, cpf_cnpj: str) -> List[Dict[str, Any]]:
        """Retorna os imóveis vinculados a um contribuinte."""
        contribuinte = self.buscar_contribuinte(cpf_cnpj)
        if not contribuinte:
            return []
        cpf_padrao = contribuinte["cpf_cnpj"]
        return [dict(im) for im in self.imoveis.values() if im["cpf_cnpj_proprietario"] == cpf_padrao]


def executar_seed(
    model_registry: Optional[Dict[str, Any]] = None,
    db_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Função plug-and-play para povoar o banco.

    Modos de Operação:
    1. Modo Simulado (Fallback): Se model_registry ou db_session forem None,
       retorna um `BancoSimuladoEmMemoria` devidamente carregado.
    2. Modo Integrado (Rayssa): Quando Rayssa definir as models:
       model_registry = {
           "Contribuinte": Contribuinte,
           "Imovel": Imovel,
           "Divida": Divida,
           "Processo": Processo
       }
       A função instanciará as classes fornecidas e as persistirá na db_session.
    """
    if model_registry and db_session:
        logger.info("Executando seed integrado com models do banco de dados...")
        registros_criados: Dict[str, int] = {
            "contribuintes": 0,
            "imoveis": 0,
            "dividas": 0,
            "processos": 0,
        }

        # 1. Contribuintes
        classe_contribuinte = model_registry.get("Contribuinte")
        if classe_contribuinte:
            for item in CONTRIBUINTES_SEED:
                instancia = classe_contribuinte(**item)
                db_session.add(instancia)
                registros_criados["contribuintes"] += 1

        # 2. Imóveis
        classe_imovel = model_registry.get("Imovel")
        if classe_imovel:
            for item in IMOVEIS_SEED:
                instancia = classe_imovel(**item)
                db_session.add(instancia)
                registros_criados["imoveis"] += 1

        # 3. Dívidas
        classe_divida = model_registry.get("Divida")
        if classe_divida:
            for item in DIVIDAS_SEED:
                instancia = classe_divida(**item)
                db_session.add(instancia)
                registros_criados["dividas"] += 1

        # 4. Processos
        classe_processo = model_registry.get("Processo")
        if classe_processo:
            for item in PROCESSOS_SEED:
                instancia = classe_processo(**item)
                db_session.add(instancia)
                registros_criados["processos"] += 1

        db_session.commit()
        return {
            "status": "sucesso",
            "modo": "integrado",
            "registros": registros_criados,
        }

    logger.info("Executando seed em modo simulado (em memória)...")
    banco_simulado = BancoSimuladoEmMemoria()
    banco_simulado.carregar_dados_iniciais()
    return {
        "status": "sucesso",
        "modo": "simulado",
        "banco_simulado": banco_simulado,
        "total_contribuintes": len(banco_simulado.contribuintes),
        "total_imoveis": len(banco_simulado.imoveis),
        "total_dividas": len(banco_simulado.dividas),
        "total_processos": len(banco_simulado.processos),
    }


if __name__ == "__main__":
    resultado = executar_seed()
    print("Seed executado com sucesso!")
    print(f"Modo: {resultado['modo']}")
    print(f"Contribuintes: {resultado['total_contribuintes']}")
    print(f"Imóveis: {resultado['total_imoveis']}")
    print(f"Dívidas: {resultado['total_dividas']}")
    print(f"Processos: {resultado['total_processos']}")
