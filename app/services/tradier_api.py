import requests
from flask_login import current_user
from datetime import date, timedelta 

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
        # ... (This helper method is unchanged) ...
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
        # ... (This helper method is unchanged) ...
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
            
    def get_historical_prices(self, symbol, period_days=185):
        """
        Fetches historical price data for a given symbol.
        Corresponds to: /v1/markets/history
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        params = {
            'symbol': symbol,
            'interval': 'daily',
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
        return self._get('/markets/history', params=params)

    def get_account_balances(self):
        # ... (This method is unchanged) ...
        endpoint = f'/accounts/{self._account_number}/balances'
        return self._get(endpoint)

    def get_positions(self):
        # ... (This method is unchanged) ...
        endpoint = f'/accounts/{self._account_number}/positions'
        return self._get(endpoint)

    def get_quotes(self, symbols):
        # ... (This method is unchanged) ...
        if not symbols:
            return None
        params = {'symbols': ','.join(symbols)}
        return self._get('/markets/quotes', params=params)
    
    def get_option_expirations(self, symbol):
        # ... (This method is unchanged) ...
        params = {'symbol': symbol}
        return self._get('/markets/options/expirations', params=params)
    
    def get_option_chain(self, symbol, expiration): # <-- ADDED NEW METHOD
        """
        Fetches the option chain for a given symbol and expiration date.
        Corresponds to: /v1/markets/options/chains
        """
        params = {'symbol': symbol, 'expiration': expiration}
        return self._get('/markets/options/chains', params=params)
        
    def place_order(self, order_payload):
        # ... (This method is unchanged) ...
        endpoint = f'/accounts/{self._account_number}/orders'
        return self._post(endpoint, payload=order_payload)

# --- Helper Function ---
def get_api_for_current_user():
    # ... (This function is unchanged) ...
    if current_user.is_authenticated and current_user.tradier_api_key:
        return TradierAPI(
            api_key=current_user.tradier_api_key,
            account_number=current_user.tradier_account_number
        )
    return None