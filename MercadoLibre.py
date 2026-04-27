import time
from typing import Any, Dict, Iterator, List, Optional
import requests
import json

class MercadoLibreClient:
    access_token = None
    refresh_token = None
    expires_in = None
    user_id = None


    def __init__(self, client_id, client_secret, redirect_uri, auth_code):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_code = auth_code
        self.access_token = None

    def authenticate(self):
        TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
        
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri,
            },
            timeout=60,
        )
        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            raise Exception("Failed to authenticate with MercadoLibre API")

        tokens = response.json()

        print("ACCESS TOKEN:", tokens["access_token"])
        print("REFRESH TOKEN:", tokens["refresh_token"])
        print("EXPIRES IN:", tokens["expires_in"])
        print("USER ID:", tokens["user_id"])

        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        self.expires_in = tokens["expires_in"]
        self.user_id = tokens["user_id"]

    def get_refresh_token(self):
        response = requests.post(
            "https://api.mercadolibre.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
            timeout=60,
        )
        response.raise_for_status()
        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        self.expires_in = tokens["expires_in"]
        self.user_id = tokens["user_id"]
        return tokens

    def get_me(self) -> dict:
        BASE = "https://api.mercadolibre.com"
        r = requests.get(
            f"{BASE}/users/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=60,
        )
        r.raise_for_status()
        m = r.json()
        self.seller_id = m["id"]
        return m

    def search_orders(
        self,
        *,
        status: Optional[str] = None,     # e.g. "paid"
        offset: int = 0,
        limit: int = 50,
        date_from_iso: Optional[str] = None,  # ISO-8601
        date_to_iso: Optional[str] = None,    # ISO-8601
    ) -> Dict[str, Any]:
        BASE = "https://api.mercadolibre.com/marketplace"

        params: Dict[str, Any] = {
            "seller": self.seller_id,
            "offset": offset,
            "limit": limit,
        }
        if status:
            params["order.status"] = status

        # Some ML docs mention ISO-8601 date filters for order creation date comparisons
        # (exact param names vary by feature/doc version)
        if date_from_iso:
            params["date_created.from"] = date_from_iso
        if date_to_iso:
            params["date_created.to"] = date_to_iso

        max_attempts = 6

        for attempt in range(max_attempts + 1):

            r = requests.get(
                f"{BASE}/orders/search",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params,
                timeout=60,
            )

            if r.status_code == 429:
                if attempt == max_attempts:
                    print(f"Max retries reached. Failed to search orders with params: {params}")
                    r.raise_for_status()
                    return None
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time} seconds before retrying... (Attempt {attempt + 1}/{max_attempts})")
                time.sleep(wait_time)
            else:
                break

        # print(json.dumps(r.json(), indent=2))
        r.raise_for_status()
        return r.json()

    def search_orders_all(
        self,
        *,
        status: Optional[str] = None,
        date_from_iso: Optional[str] = None,
        date_to_iso: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        orders: List[Dict[str, Any]] = []
        offset = 0

        while True:
            page = self.search_orders(
                status=status,
                offset=offset,
                limit=limit,
                date_from_iso=date_from_iso,
                date_to_iso=date_to_iso,
            )

            results = page.get("results", [])
            paging = page.get("paging", {})
            total = paging.get("total", 0)

            if not results:
                break

            orders.extend(results)
            offset += limit

            if offset >= total:
                break

        return orders

    def get_order(self, order_id: int) -> Dict[str, Any]:
        BASE = "https://api.mercadolibre.com/marketplace"
        r = requests.get(
            f"{BASE}/orders/{order_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    
    def get_order_gross(self, order_id: int) -> float:
        BASE = "https://api.mercadolibre.com"
        r = requests.get(
            f"{BASE}/orders/{order_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=60,
        )
        r.raise_for_status()
        order_data = r.json()
        return order_data

    def iter_orders(self, *, status: str = "paid", page_size: int = 50) -> Iterator[Dict[str, Any]]:
        BASE = "https://api.mercadolibre.com"
        offset = 0
        while True:
            page = self.search_orders(self.access_token, self.seller_id, status=status, offset=offset, limit=page_size)
            results = page.get("results") or []
            if not results:
                return

            for row in results:
                oid = int(row["id"])
                yield self.get_order(self.access_token, oid)

            offset += page_size
    
    def get_shippment_info(self, shipment_id):
        BASE = "https://api.mercadolibre.com/marketplace"

        max_retries = 5
        for attempt in range(max_retries):
            r = requests.get(
                f"{BASE}/shipments/{shipment_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=60,
            )

            if r.status_code == 429:
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)

            try:
                r.raise_for_status()
                return r.json()
            except Exception as e:
                print(f"Attempt {attempt + 1} failed to get shipment info for ID {shipment_id}: {e}")
        return None
    
    def get_billing_info(self, order_id):
        BASE = "https://api.mercadolibre.com/marketplace"
        url = f"{BASE}/orders/{order_id}/billing_info"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        max_retries = 3

        for attempt in range(max_retries):
            try:
                r = requests.get(url, headers=headers, timeout=60)

                # Retry temporary Mercado Libre/server issues
                if r.status_code in (429, 500, 502, 503, 504):
                    wait = 2 ** attempt
                    print(
                        f"Temporary error {r.status_code} while fetching billing info "
                        f"for order {order_id}. Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                    continue

                r.raise_for_status()
                return r.json()

            except requests.exceptions.Timeout:
                wait = 2 ** attempt
                print(f"Timeout fetching billing info for order {order_id}. Retrying in {wait}s...")
                time.sleep(wait)

            except requests.exceptions.HTTPError as e:
                print(f"HTTP error fetching billing info for order {order_id}")
                print(f"Status code: {r.status_code}")
                print(f"Response body: {r.text}")
                raise e

            except requests.exceptions.RequestException as e:
                print(f"Request error fetching billing info for order {order_id}: {e}")
                raise e

        raise Exception(
            f"Failed to fetch billing info for order {order_id} after {max_retries} retries"
        )
    
    def publish_item(self, data):
        BASE = "https://api.mercadolibre.com/marketplace"
        item_data = {
            
        }
        r = requests.get(
            f"{BASE}/users/{self.user_id}/items",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=item_data,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    
    def get_item_with_sku(self, sku):
        BASE = "https://api.mercadolibre.com/marketplace"
        params = {
            "seller_sku": sku
        }
        r = requests.get(
            f"{BASE}/users/{self.user_id}/items/search",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    
    def get_item(self, item_id: str):
        r = requests.get(
            f"https://api.mercadolibre.com/items/{item_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    
    def update_item(self, item_id: str, data: Dict[str, Any]):
        r = requests.put(
            f"https://api.mercadolibre.com/global/items/{item_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=data,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    
