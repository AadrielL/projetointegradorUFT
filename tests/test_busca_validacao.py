"""
Suíte de Testes de Busca, Validação e Povoamento de Dados (Seeds).

Responsável: Adriel Morais (PO / Dev)
Módulo: tests/test_busca_validacao.py

Cobre os requisitos de:
  - Busca de Contribuinte por CPF e CNPJ (com e sem máscara).
  - Tratamento de erros para contribuinte/débito não encontrado e documentos inválidos.
  - Listagem de dívidas e processos de execução fiscal vinculados ao imóvel.
  - Funcionamento da engine de seeds tanto no modo simulado quanto com injeção de models.
"""

import unittest
from unittest.mock import MagicMock

from seeds.mock_data import (
    BancoSimuladoEmMemoria,
    CONTRIBUINTES_SEED,
    IMOVEIS_SEED,
    DIVIDAS_SEED,
    PROCESSOS_SEED,
    executar_seed,
    obter_contribuintes_mock,
    obter_imoveis_mock,
    obter_dividas_mock,
    obter_processos_mock,
    obter_dados_consolidados,
)
from src.services.busca_service import (
    BuscaService,
    ContribuinteNaoEncontradoError,
    DocumentoInvalidoError,
    ImovelNaoEncontradoError,
    normalizar_documento,
)


class TestBuscaEValidacaoContribuinte(unittest.TestCase):
    """Testes unitários e de integração simulada para busca de contribuintes."""

    def setUp(self) -> None:
        self.servico = BuscaService()

    def test_busca_contribuinte_por_cpf_com_mascara(self) -> None:
        """Verifica se encontra contribuinte buscando pelo CPF formatado."""
        resultado = self.servico.buscar_contribuinte("123.456.789-01")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["nome"], "Carlos Eduardo Siqueira")
        self.assertEqual(resultado["cpf_cnpj"], "123.456.789-01")
        self.assertEqual(resultado["email"], "carlos.siqueira@email.com")

    def test_busca_contribuinte_por_cpf_apenas_digitos(self) -> None:
        """Verifica se encontra contribuinte buscando apenas pelos dígitos do CPF."""
        resultado = self.servico.buscar_contribuinte("12345678901")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["nome"], "Carlos Eduardo Siqueira")

    def test_busca_contribuinte_por_cnpj(self) -> None:
        """Verifica se encontra pessoa jurídica por CNPJ (formatado ou desformatado)."""
        cnpj_formatado = "12.345.678/0001-90"
        resultado = self.servico.buscar_contribuinte(cnpj_formatado)
        self.assertEqual(resultado["nome"], "Tocantins Engenharia e Serviços Ltda")
        self.assertEqual(resultado["tipo_pessoa"], "JURIDICA")

        cnpj_limpo = "12345678000190"
        resultado_limpo = self.servico.buscar_contribuinte(cnpj_limpo)
        self.assertEqual(resultado_limpo["nome"], "Tocantins Engenharia e Serviços Ltda")

    def test_busca_contribuinte_nao_encontrado(self) -> None:
        """Verifica se lança ContribuinteNaoEncontradoError para documento inexistente."""
        cpf_inexistente = "000.111.222-33"
        with self.assertRaises(ContribuinteNaoEncontradoError) as ctx:
            self.servico.buscar_contribuinte(cpf_inexistente)
        self.assertIn("não foi encontrado", str(ctx.exception))

    def test_busca_contribuinte_documento_invalido(self) -> None:
        """Verifica se rejeita documentos com tamanho incorreto ou caracteres impróprios."""
        casos_invalidos = ["123", "abc", "123456789", "1234567890123456"]
        for caso in casos_invalidos:
            with self.subTest(caso=caso):
                with self.assertRaises(DocumentoInvalidoError):
                    self.servico.buscar_contribuinte(caso)

    def test_busca_contribuinte_documento_vazio(self) -> None:
        """Verifica se rejeita entradas nulas ou vazias."""
        for vazio in ["", "   ", None]:
            with self.subTest(vazio=vazio):
                with self.assertRaises(DocumentoInvalidoError):
                    self.servico.buscar_contribuinte(vazio)  # type: ignore


class TestBuscaDividasEProcessosImovel(unittest.TestCase):
    """Testes para listagem de débitos e processos associados ao imóvel."""

    def setUp(self) -> None:
        self.servico = BuscaService()

    def test_listagem_dividas_e_processos_imovel_com_debitos(self) -> None:
        """
        Verifica se um imóvel com pendências retorna a lista correta de dívidas
        e o processo de execução fiscal ajuizado correspondente.
        """
        cci = "CCI-104-NORTE-01"
        dossie = self.servico.listar_dividas_e_processos_imovel(cci)

        self.assertEqual(dossie["imovel"]["inscricao_cci"], cci)
        self.assertEqual(dossie["total_dividas"], 2)
        # Débito 2023 (2450 + 380.50) + Débito 2022 (2200 + 650.00) = 2830.50 + 2850.00 = 5680.50
        self.assertAlmostEqual(dossie["valor_total_devido"], 5680.50, places=2)

        # Processo de execução fiscal associado ao débito de 2022
        self.assertEqual(dossie["total_processos"], 1)
        processo = dossie["processos"][0]
        self.assertEqual(processo["numero_processo"], "0012345-67.2023.8.27.2729")
        self.assertIn("Execução Fiscal", processo["vara"])

    def test_listagem_imovel_adimplente_sem_dividas_nem_processos(self) -> None:
        """Imóvel sem dívidas cadastradas deve retornar listas vazias e total zerado."""
        cci_limpo = "CCI-GRACIOSA-LAGO-88"
        dossie = self.servico.listar_dividas_e_processos_imovel(cci_limpo)

        self.assertEqual(dossie["total_dividas"], 0)
        self.assertEqual(dossie["valor_total_devido"], 0.0)
        self.assertEqual(dossie["total_processos"], 0)
        self.assertEqual(dossie["dividas"], [])
        self.assertEqual(dossie["processos"], [])

    def test_busca_imovel_inexistente(self) -> None:
        """Lança ImovelNaoEncontradoError ao consultar CCI inexistente."""
        with self.assertRaises(ImovelNaoEncontradoError):
            self.servico.listar_dividas_e_processos_imovel("CCI-INEXISTENTE-999")

    def test_busca_imovel_cci_vazia(self) -> None:
        """Lança ValueError ao consultar inscrição vazia."""
        with self.assertRaises(ValueError):
            self.servico.listar_dividas_e_processos_imovel("   ")


class TestSeedEngineEIntegracao(unittest.TestCase):
    """Testes da infraestrutura de Seeds e do mecanismo de injeção das models da Rayssa."""

    def test_executar_seed_modo_simulado(self) -> None:
        """Verifica a carga padrão de dados simulados em memória."""
        res = executar_seed()
        self.assertEqual(res["status"], "sucesso")
        self.assertEqual(res["modo"], "simulado")
        self.assertGreaterEqual(res["total_contribuintes"], 5)
        self.assertGreaterEqual(res["total_imoveis"], 5)
        self.assertGreaterEqual(res["total_dividas"], 4)
        self.assertGreaterEqual(res["total_processos"], 2)

    def test_obter_dados_consolidados(self) -> None:
        """Valida que todos os conjuntos de dados foram povoados com integridade."""
        dados = obter_dados_consolidados()
        self.assertIn("contribuintes", dados)
        self.assertIn("imoveis", dados)
        self.assertIn("dividas", dados)
        self.assertIn("processos", dados)
        self.assertEqual(len(dados["contribuintes"]), len(CONTRIBUINTES_SEED))
        self.assertEqual(len(dados["imoveis"]), len(IMOVEIS_SEED))

    def test_executar_seed_com_model_registry_mockado(self) -> None:
        """
        Simula a entrega das models pela Rayssa.
        Garante que a função executar_seed instancia as classes e persiste na sessão.
        """
        # Cria classes simuladas imitando SQLAlchemy / Dataclasses
        mock_contribuinte_cls = MagicMock(side_effect=lambda **kw: MagicMock(**kw))
        mock_imovel_cls = MagicMock(side_effect=lambda **kw: MagicMock(**kw))
        mock_divida_cls = MagicMock(side_effect=lambda **kw: MagicMock(**kw))
        mock_processo_cls = MagicMock(side_effect=lambda **kw: MagicMock(**kw))

        model_registry = {
            "Contribuinte": mock_contribuinte_cls,
            "Imovel": mock_imovel_cls,
            "Divida": mock_divida_cls,
            "Processo": mock_processo_cls,
        }

        mock_db_session = MagicMock()

        resultado = executar_seed(model_registry=model_registry, db_session=mock_db_session)

        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["modo"], "integrado")
        self.assertEqual(resultado["registros"]["contribuintes"], len(CONTRIBUINTES_SEED))
        self.assertEqual(resultado["registros"]["imoveis"], len(IMOVEIS_SEED))
        self.assertEqual(resultado["registros"]["dividas"], len(DIVIDAS_SEED))
        self.assertEqual(resultado["registros"]["processos"], len(PROCESSOS_SEED))

        # Garante que db_session.add foi chamado para cada item e db_session.commit foi chamado
        total_esperado = (
            len(CONTRIBUINTES_SEED)
            + len(IMOVEIS_SEED)
            + len(DIVIDAS_SEED)
            + len(PROCESSOS_SEED)
        )
        self.assertEqual(mock_db_session.add.call_count, total_esperado)
        mock_db_session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
