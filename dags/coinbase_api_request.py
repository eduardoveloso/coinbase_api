from src.extract import get_coinbase_price
from datetime import datetime
import os
from airflow.decorators import task, dag
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.empty import EmptyOperator

@dag(
    dag_id="coinbase_api_request",
    schedule_interval="*/2 * * * *",
    start_date=datetime(2025, 9, 28),
    catchup=False,
    tags=["coinbase", "api", "bitcoin"],
)
def coinbase_api_dag():

    start_task = EmptyOperator(
        task_id="start_task",
    )

    @task(task_id="fetch_and_print_coinbase_price")
    def fetch_and_print_coinbase_price():
        url = os.getenv("COINBASE_ENDPOINT")
        data = get_coinbase_price(endpoint=url)
        return data

    @task
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
        PostgresOperator(
            task_id="create_table_task",
            postgres_conn_id="postgres_oltp",
            sql=create_table_query,
        ).execute({})

    @task
    def load_into_postgres(data):
        insert_query = f"""
        INSERT INTO coinbase_prices (base, currency, amount, fetched_at)
        VALUES ({data['base']}, {data['currency']}, {data['amount']}, '{datetime.now()}');
        """

        PostgresOperator(
            task_id="insert_data_task",
            postgres_conn_id="postgres_oltp",
            sql=insert_query,
        ).execute({})

    end_task = EmptyOperator(
        task_id="end_task",
    )

    t1 = create_table()
    t2 = fetch_and_print_coinbase_price()
    t3 = load_into_postgres(t2)

    start_task >> t1 >> t2 >> t3 >> end_task

coinbase_api_request_dag = coinbase_api_dag()
