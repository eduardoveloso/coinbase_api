from src.extract import get_coinbase_price
from datetime import datetime
import os
from airflow.decorators import task, dag

@dag(
    dag_id="coinbase_api_request",
    schedule_interval="*/2 * * * *",
    start_date=datetime(2025, 9, 28),
    catchup=False,
    tags=["coinbase", "api", "bitcoin"],
)
def coinbase_api_request_dag():
    @task
    def fetch_and_print_coinbase_price():
        url = os.getenv("COINBASE_ENDPOINT")
        dados = get_coinbase_price(endpoint=url)
        print(dados)

    fetch_and_print_coinbase_price()
coinbase_api_request_dag = coinbase_api_request_dag()