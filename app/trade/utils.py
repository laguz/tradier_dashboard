from datetime import datetime

def generate_occ_symbol(underlying, expiration_str, option_type, strike):
    """
    Generates a 21-character OCC-compliant option symbol.
    
    Args:
        underlying (str): The stock ticker, e.g., 'AAPL'.
        expiration_str (str): The expiration date in 'YYYY-MM-DD' format.
        option_type (str): 'call' or 'put'.
        strike (Decimal or float): The strike price of the option.
        
    Returns:
        str: The OCC option symbol, e.g., 'AAPL  251219C00175000'.
    """
    # 1. Underlying symbol, padded to 6 characters with spaces on the right
    symbol_padded = underlying.upper().ljust(6)

    # 2. Expiration date in YYMMDD format
    dt_obj = datetime.strptime(expiration_str, '%Y-%m-%d')
    date_formatted = dt_obj.strftime('%y%m%d')

    # 3. Option Type ('C' for call, 'P' for put)
    type_char = 'C' if option_type.lower() == 'call' else 'P'

    # 4. Strike Price, formatted as an 8-digit integer with 3 decimal places
    # Example: 175.50 -> 175500 -> "00175500"
    strike_in_thousandths = int(float(strike) * 1000)
    strike_formatted = f"{strike_in_thousandths:08d}"

    return f"{symbol_padded}{date_formatted}{type_char}{strike_formatted}"