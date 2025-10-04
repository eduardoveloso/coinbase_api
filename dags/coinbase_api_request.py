from src.extract import get_coinbase_price
from datetime import datetime, timedelta
import os
import logging
from airflow.decorators import task, dag
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.empty import EmptyOperator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dag(
    dag_id="coinbase_api_request",
    schedule_interval="* * * * *",
    start_date=datetime(2025, 9, 28),
    catchup=False,
    tags=["coinbase", "api", "bitcoin"],
)
def coinbase_api_dag():

    logger.info("DAG started")
    start_task = EmptyOperator(
        task_id="start_task",
    )

    @task(task_id="log_postgres_connection")
    def log_postgres_connection():
        try:
            from airflow.hooks.base import BaseHook
            conn = BaseHook.get_connection("postgres_oltp")
            logger.info(
                "Postgres conn resolved -> host=%s port=%s schema=%s login=%s",
                conn.host,
                conn.port,
                conn.schema,
                conn.login,
            )
        except Exception as e:
            logger.exception("Failed to load Airflow connection: %s", e)

    @task(task_id="fetch_and_print_coinbase_price", retries=5, retry_delay=timedelta(seconds=20))
    def fetch_and_print_coinbase_price():
        url = os.getenv("COINBASE_ENDPOINT")
        logger.info(f"Fetching data from {url}")
        data = get_coinbase_price(endpoint=url)
        return data

    @task(retries=2, retry_delay=timedelta(seconds=20))
    def create_table():
        create_table_query = """
        CREATE TABLE IF NOT EXISTS coinbase_prices (
            id SERIAL PRIMARY KEY,
            base VARCHAR(10),
            currency VARCHAR(10),
            amount FLOAT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        hook = PostgresHook(postgres_conn_id="postgres_oltp")
        logger.info("Creating table if not exists")
        hook.run(create_table_query)

    @task(retries=5, retry_delay=timedelta(seconds=20))
    def load_into_postgres(data):
        insert_query = (
            """
            INSERT INTO coinbase_prices (base, currency, amount, fetched_at)
            VALUES (%s, %s, %s, %s);
            """
        )
        hook = PostgresHook(postgres_conn_id="postgres_oltp")
        logger.info(f"Inserting data into Postgres: {data}")
        hook.run(
            insert_query,
            parameters=(
                data["base"],
                data["currency"],
                float(data["amount"]),
                datetime.now(),
            ),
        )

    logger.info("DAG finished")
    end_task = EmptyOperator(
        task_id="end_task",
    )

    t_conn = log_postgres_connection()
    t1 = create_table()
    t2 = fetch_and_print_coinbase_price()
    t3 = load_into_postgres(t2)

    start_task >> t_conn >> t1 >> t2 >> t3 >> end_task

coinbase_api_request_dag = coinbase_api_dag()
