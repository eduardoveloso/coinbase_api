import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_coinbase_price(endpoint: str) -> dict:
    """
        Fetches the current Bitcoin price from the Coinbase API.
        Args:
            endpoint (str): The Coinbase API endpoint URL.
        Returns: A dictionary containing the JSON response from the API.
        Raises: requests.exceptions.RequestException if the request fails.
    """
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        data = response.json().get('data', {})
        return {
            "base": data.get("base"),
            "currency": data.get("currency"),
            "amount": float(data.get("amount")) if data.get("amount") else None,
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Coinbase API: {e}")
        return {}

if __name__ == "__main__":
    url = os.getenv("COINBASE_ENDPOINT")
    dados = get_coinbase_price(endpoint=url)
    print(dados)
