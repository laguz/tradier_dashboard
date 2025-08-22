import pandas as pd
from flask import render_template, redirect, url_for, flash, Blueprint
from flask_login import login_required

from app.services.tradier_api import get_api_for_current_user
# Re-using the analysis function from our research blueprint
from app.research.routes import find_support_resistance, custom_round
from .forms import AutoTradeForm

# Create a Blueprint for autotrade routes
autotrade = Blueprint('autotrade', __name__)

@autotrade.route('/autotrade', methods=['GET', 'POST'])
@login_required
def autotrade_page():
    form = AutoTradeForm()
    proposed_trades = {}
    
    if form.validate_on_submit():
        api = get_api_for_current_user()
        if not api:
            flash('Cannot perform analysis. Please check your API credentials.', 'danger')
            return redirect(url_for('autotrade.autotrade_page'))

        try:
            # --- 1. Fetch Data and Perform Analysis ---
            symbol = 'TSLA'
            
            # Get current quote
            quote_data = api.get_quotes([symbol])
            if not quote_data or not quote_data.get('quotes'):
                raise ValueError(f"Could not fetch current price for {symbol}.")
            current_price = quote_data['quotes']['quote']['last']

            # Get historical data for S/R levels
            history_data = api.get_historical_prices(symbol)
            if not history_data or not history_data.get('history') or history_data['history'] == 'null':
                 raise ValueError(f"No historical data found for {symbol}.")
            day_data = history_data['history']['day']
            stock_df = pd.DataFrame(day_data)
            stock_df.rename(columns={'close': 'Close'}, inplace=True)

            support, resistance = find_support_resistance(stock_df)
            
            # Get option expirations
            exp_data = api.get_option_expirations(symbol)
            if not exp_data or not exp_data.get('expirations'):
                raise ValueError(f"Could not fetch option expirations for {symbol}.")
            expirations = exp_data['expirations']['date']
            
            # --- 2. Determine Trade Parameters based on your rules ---
            
            # PUT SPREAD LOGIC
            valid_supports = [s for s in reversed(support) if s < current_price]
            if valid_supports:
                sell_put_strike = custom_round(valid_supports[0])
                buy_put_strike = sell_put_strike - 5
                proposed_trades['put_spread'] = {
                    'sell_strike': sell_put_strike,
                    'buy_strike': buy_put_strike
                }

            # CALL SPREAD LOGIC
            valid_resistances = [r for r in resistance if r > current_price]
            if valid_resistances:
                sell_call_strike = custom_round(valid_resistances[0])
                buy_call_strike = sell_call_strike + 5
                proposed_trades['call_spread'] = {
                    'sell_strike': sell_call_strike,
                    'buy_strike': buy_call_strike
                }

            # Get the target expiration date (index 4)
            if len(expirations) > 4:
                proposed_trades['expiration'] = expirations[4]
            else:
                flash('Not enough expiration dates to select the one at index 4.', 'warning')

            proposed_trades['current_price'] = current_price
            flash('Analysis complete. Review the proposed trades below.', 'success')

        except Exception as e:
            flash(f"An error occurred during analysis: {e}", 'danger')

    return render_template('autotrade/autotrade.html', 
                           title='AutoTrade TSLA', 
                           form=form, 
                           trades=proposed_trades)