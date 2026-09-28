"""
Módulo seeds.
Exporta dados de mock e engine de povoamento de dados.
"""

from seeds.mock_data import (
    ContribuinteMock,
    ImovelMock,
    DividaMock,
    ProcessoMock,
    CONTRIBUINTES_SEED,
    IMOVEIS_SEED,
    DIVIDAS_SEED,
    PROCESSOS_SEED,
    obter_contribuintes_mock,
    obter_imoveis_mock,
    obter_dividas_mock,
    obter_processos_mock,
    obter_dados_consolidados,
    BancoSimuladoEmMemoria,
    executar_seed,
)

__all__ = [
    "ContribuinteMock",
    "ImovelMock",
    "DividaMock",
    "ProcessoMock",
    "CONTRIBUINTES_SEED",
    "IMOVEIS_SEED",
    "DIVIDAS_SEED",
    "PROCESSOS_SEED",
    "obter_contribuintes_mock",
    "obter_imoveis_mock",
    "obter_dividas_mock",
    "obter_processos_mock",
    "obter_dados_consolidados",
    "BancoSimuladoEmMemoria",
    "executar_seed",
]
