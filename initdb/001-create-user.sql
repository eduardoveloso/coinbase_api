-- os valores para nome e senha do usuário serão fornecidos via variáveis de ambiente definidas no docker-compose.override.yml ou no .env
-- variáveis de ambiente: OLTP_USER e OLTP_PASSWORD

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'OLTP_USER') THEN
    CREATE ROLE :'OLTP_USER' LOGIN PASSWORD :'OLTP_PASSWORD';
  END IF;
END$$;

-- garante CONNECT no banco (já criado via POSTGRES_DB)
GRANT CONNECT ON DATABASE coinbase_oltp TO :'OLTP_USER';

-- no banco alvo, conceda privilégios de uso no schema e padrões para objetos futuros
\connect coinbase_oltp

GRANT USAGE ON SCHEMA public TO :'OLTP_USER';

-- privilégios atuais
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :'OLTP_USER';
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO :'OLTP_USER';

-- privilégios padrão para objetos que forem criados depois
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :'OLTP_USER';

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO :'OLTP_USER';