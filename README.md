# Coinbase API ETL com Airflow

Projeto de ETL com Apache Airflow que busca o preço spot do Bitcoin na Coinbase e grava em um Postgres OLTP. O ambiente local usa Astronomer Runtime (Docker) com um Postgres acoplado via `docker-compose.override.yml`.

## Visão Geral

- DAG `coinbase_api_request` roda a cada 1 minuto.
- Cria a tabela se não existir e insere um registro de preço.
- Conexão do Airflow: `postgres_oltp`.
- Endpoint configurável via `.env` (`COINBASE_ENDPOINT`).

## Arquitetura

- **DAG:** `dags/coinbase_api_request.py`
- **Tarefas:**
  `start → log_postgres_connection → create_table → fetch_and_print_coinbase_price → load_into_postgres → end`
- **Agendamento:** `* * * * *` (a cada minuto)
  `catchup=False, start_date=2025-09-28`
- **Extração:** `src/extract.py`
  Função `get_coinbase_price(endpoint: str) -> dict` retorna `base`, `currency`, `amount`.
- **Conexões/variáveis do Airflow (dev local):** `airflow_settings.yaml`
  Define `postgres_oltp` apontando para o serviço Docker `oltp_postgres`.
- **Banco OLTP (Docker):** `docker-compose.override.yml` + `initdb/001-create-user.sql`
  Sobe Postgres em localhost:5433 (host) e cria usuário/esquema/permissões.
- **Dependências:**
  - `pyproject.toml` (Poetry, Python >=3.12,< 3.14)
  - `requirements.txt` (pip)

## Requisitos

- Docker e Docker Compose
- Astronomer CLI (para `astro dev start`)
- Opcional: Python 3.12+ e poetry ou pip para executar `src/extract.py` e testes fora do container

## Configuração

### Variáveis de ambiente (arquivo `.env`):

```
COINBASE_ENDPOINT=https://api.coinbase.com/v2/prices/spot
OLTP_USER={user}
OLTP_PASSWORD={password}
OLTP_DB=coinbase_oltp
OLTP_PORT=5433
```

### Conexão do Airflow (apenas dev local):

- `airflow_settings.yaml` já inclui a conexão `postgres_oltp`.
- Em produção, crie a conexão via UI do Airflow ou Secrets Backend.

## Execução

- Subir o ambiente:

  ```
  astro dev start
  ```

- Airflow UI:

  ```
  http://localhost:8080
  ```

- DAG:

  `coinbase_api_request` (tags: `coinbase`, `api`, `bitcoin`)

- Acione manualmente (Trigger) ou aguarde o agendamento por minuto.

- Parar:

  ```
  astro dev stop
  ```


## Banco de Dados

- Serviço Postgres no host: `localhost:5433`
- Dentro da rede do Docker/Compose (pelos containers Airflow): host `oltp_postgres`, porta `5432`.
- Conectar via psql no host:

  ```
  psql -h localhost -p 5433 -U $${OLTP_USER} -d $${OLTP_DB}
  ```

- Tabela criada automaticamente:

  ```sql
  CREATE TABLE IF NOT EXISTS coinbase_prices (
    id SERIAL PRIMARY KEY,
    base VARCHAR(10),
    currency VARCHAR(10),
    amount FLOAT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

## Estrutura do Projeto

```
.
├─ dags/
│  └─ coinbase_api_request.py
├─ src/
│  ├─ __init__.py
│  └─ extract.py
├─ initdb/
│  └─ 001-create-user.sql
├─ .astro/
│  ├─ config.yaml
│  ├─ dag_integrity_exceptions.txt
│  └─ test_dag_integrity_default.py
├─ airflow_settings.yaml
├─ docker-compose.override.yml
├─ Dockerfile
├─ pyproject.toml
├─ requirements.txt
├─ .env
└─ README.md
```

## Problemas Comuns

- **Conexão `postgres_oltp` ausente:**
  Garanta que `airflow_settings.yaml` foi carregado (suba com `astro dev start`).

- **Falha de conexão ao Postgres:**
  Verifique se a porta 5433 está livre no host e as variáveis do `.env`.

- **Erro ao buscar preço:**
  Confirme o `COINBASE_ENDPOINT` e a conectividade de rede.

## Notas

- O endpoint `https://api.coinbase.com/v2/prices/spot` retorna o preço spot; por padrão em USD, a menos que especificado por parâmetro (`?currency=BRL`, por exemplo).
- A DAG define retries nas tasks críticas; ajuste conforme necessidade.
