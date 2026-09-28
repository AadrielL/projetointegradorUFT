# Módulo de Seeds e Massa de Dados (Sprint 2)

**Código:** [seeds/mock_data.py](../../seeds/mock_data.py) · [seeds/__init__.py](../../seeds/__init__.py) · **Responsável:** Adriel Morais

## Estado atual
Implementado e pronto para consumo imediato nos testes e futura integração com o banco de dados da Rayssa.

## Responsabilidade e conteúdo
Fornece estruturas tipadas (DTOs / Dataclasses) e massa de dados realistas de Palmas/TO para 4 entidades do domínio fiscal:
- **`ContribuinteMock`**: pessoas físicas e jurídicas com CPF, CNPJ, e-mail e telefone.
- **`ImovelMock`**: imóveis identificados por Inscrição Municipal / CCI, tipo (residencial, comercial, terreno), valor venal, endereço e vínculo com o contribuinte.
- **`DividaMock`**: débitos fiscais de IPTU, ISS e taxas com exercício, valor principal, juros/multa e status (`ATIVO` e `AJUIZADO`).
- **`ProcessoMock`**: processos judiciais de execução fiscal com número CNJ, vara competente e data de autuação.

### Engine de Injeção e Povoamento
- **`BancoSimuladoEmMemoria`**: emulador de repositório em memória com índices rápidos para buscas por CPF/CNPJ e CCI.
- **`executar_seed(model_registry, db_session)`**:
  - *Modo Simulado:* quando chamada sem argumentos, retorna o `BancoSimuladoEmMemoria` preenchido.
  - *Modo Integrado:* recebe as classes SQLAlchemy/ORM da Rayssa via `model_registry` e a sessão do banco `db_session`, realizando a inserção e commit automático dos registros.

## Veja também
[BuscaService](services/busca_service.md) · [Integração com a Prefeitura](../integracao_prefeitura.md) · [Arquitetura](../arquitetura.md)
