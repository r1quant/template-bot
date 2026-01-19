import requests

DERIBIT_API = "https://www.deribit.com/api/v2"


class DeribitAPI:
    def get_underlying_price():
        """Get current BTC price from Deribit"""
        try:
            url = f"{DERIBIT_API}/public/get_index_price"
            params = {"index_name": "btc_usd"}
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            return data.get("result", {}).get("index_price")
        except Exception:
            return 0
