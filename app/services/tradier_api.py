import requests
from flask_login import current_user

class TradierAPI:
    """
    A client class to interact with the Tradier API.
    """
    def __init__(self, api_key, account_number):
        self._base_url = "https://sandbox.tradier.com/v1"
        self._api_key = api_key
        self._account_number = account_number
        self._headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Accept': 'application/json'
        }

    def _get(self, endpoint, params=None):
        """
        Private helper method to perform a GET request.
        """
        if not self._api_key:
            return None
        
        try:
            url = f"{self._base_url}{endpoint}"
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making GET request to Tradier API: {e}")
            return None

    def _post(self, endpoint, payload):
        """
        Private helper method to perform a POST request.
        """
        if not self._api_key:
            return None
        
        try:
            url = f"{self._base_url}{endpoint}"
            response = requests.post(url, headers=self._headers, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making POST request to Tradier API: {e}")
            try:
                return response.json()
            except ValueError:
                return {'error': str(e)}

    def get_account_balances(self):
        """Fetches account balance information."""
        endpoint = f'/accounts/{self._account_number}/balances'
        return self._get(endpoint)

    def get_positions(self):
        """Fetches all positions in the account."""
        endpoint = f'/accounts/{self._account_number}/positions'
        return self._get(endpoint)

    def get_quotes(self, symbols):
        """Fetches quote data for a list of symbols."""
        if not symbols:
            return None
        params = {'symbols': ','.join(symbols)}
        return self._get('/markets/quotes', params=params)
    
    def get_option_expirations(self, symbol): # <-- ADDED NEW METHOD
        """
        Fetches all available option expiration dates for a given symbol.
        Corresponds to: /v1/markets/options/expirations
        """
        params = {'symbol': symbol}
        return self._get('/markets/options/expirations', params=params)
        
    def place_order(self, order_payload):
        """
        Places a trade order for stocks, single options, or multi-leg options.
        """
        endpoint = f'/accounts/{self._account_number}/orders'
        return self._post(endpoint, payload=order_payload)

# --- Helper Function ---
def get_api_for_current_user():
    """
    A factory function that creates a TradierAPI instance
    for the currently logged-in user.
    """
    if current_user.is_authenticated and current_user.tradier_api_key:
        return TradierAPI(
            api_key=current_user.tradier_api_key,
            account_number=current_user.tradier_account_number
        )
    return None