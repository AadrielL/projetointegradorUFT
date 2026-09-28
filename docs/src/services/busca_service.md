# BuscaService

**Código:** [services/busca_service.py](../../../src/services/busca_service.py) · **Requisitos:** RF01, RF02, RF03, RF06 (Sprint 2)

## Estado atual
Implementado e testado com suíte de testes unitários e de integração simulada em `tests/test_busca_validacao.py`.

## Responsabilidade e conteúdo
Camada de serviço responsável pela busca, normalização e validação de contribuintes e imóveis tributários:
- `buscar_contribuinte(cpf_cnpj)`: normaliza o documento, valida formato (11 dígitos para CPF, 14 para CNPJ) e realiza a busca na base.
- `buscar_imovel(inscricao_cci)`: valida a inscrição cadastral imobiliária e retorna a ficha cadastral do imóvel.
- `listar_dividas_e_processos_imovel(inscricao_cci)`: consolida o dossiê fiscal do imóvel, relacionando débitos em aberto/ajuizados e processos de execução fiscal decorrentes.

Exceções especializadas:
- `DocumentoInvalidoError`: formato, máscara incorreta ou quantidade de dígitos inválida.
- `ContribuinteNaoEncontradoError`: contribuinte ausente na base cadastral.
- `ImovelNaoEncontradoError`: inscrição imobiliária não encontrada.

## Com quem trabalha
Trabalha com o repositório em memória (`BancoSimuladoEmMemoria` do módulo `seeds.mock_data`) ou com o repositório/banco de dados real quando implementado pela equipe.

## Limites e cuidados
Preserva a imutabilidade dos dados cadastrais e rejeita documentos vazios ou mal formatados antes de consultar a camada de dados.

## Veja também
[Integração com a Prefeitura](../../integracao_prefeitura.md) · [Documentação de Seeds](../seeds.md) · [Arquitetura](../../arquitetura.md) · [Índice do código](../README.md)
