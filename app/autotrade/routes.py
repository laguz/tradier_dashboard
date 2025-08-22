import pandas as pd
from flask import render_template, redirect, url_for, flash, Blueprint, request
from flask_login import login_required

from app.services.tradier_api import get_api_for_current_user
from app.research.routes import find_support_resistance
from app.trade.utils import generate_occ_symbol
from .forms import AutoTradeForm, ExecuteTradeForm

autotrade = Blueprint('autotrade', __name__)

def round_to_nearest_five(price):
    """Rounds a given price to the nearest number ending in 0 or 5."""
    return round(price / 5) * 5

@autotrade.route('/autotrade', methods=['GET', 'POST'])
@login_required
def autotrade_page():
    form = AutoTradeForm()
    put_exec_form = ExecuteTradeForm(prefix='put')
    call_exec_form = ExecuteTradeForm(prefix='call')
    proposed_trades = {}

    # --- EXECUTION LOGIC FOR PUT SPREAD ---
    if 'submit_put' in request.form:
        if put_exec_form.validate_on_submit():
            api = get_api_for_current_user()
            if not api:
                flash('Cannot place order. Please check your API credentials.', 'danger')
                return redirect(url_for('autotrade.autotrade_page'))

            short_put_symbol = generate_occ_symbol(put_exec_form.underlying_symbol.data, put_exec_form.expiration_date.data, 'put', put_exec_form.strike_short.data)
            long_put_symbol = generate_occ_symbol(put_exec_form.underlying_symbol.data, put_exec_form.expiration_date.data, 'put', put_exec_form.strike_long.data)
            
            payload = {
                'class': 'multileg', 'symbol': put_exec_form.underlying_symbol.data.upper(), 'type': 'credit', 'duration': 'day',
                'price': f"{put_exec_form.limit_price.data:.2f}",
                'option_symbol[0]': short_put_symbol, 'side[0]': 'sell_to_open', 'quantity[0]': str(put_exec_form.quantity.data),
                'option_symbol[1]': long_put_symbol, 'side[1]': 'buy_to_open', 'quantity[1]': str(put_exec_form.quantity.data)
            }
            response = api.place_order(payload)
            if response and response.get('order'):
                flash('Put Credit Spread order submitted successfully!', 'success')
            else:
                flash(f"Put Credit Spread order failed: {response.get('errors', 'Unknown error')}", 'danger')
            return redirect(url_for('autotrade.autotrade_page'))
        else:
            flash(f"Execution form was invalid. Errors: {put_exec_form.errors}", 'danger')

    # --- EXECUTION LOGIC FOR CALL SPREAD ---
    elif 'submit_call' in request.form:
        if call_exec_form.validate_on_submit():
            api = get_api_for_current_user()
            if not api:
                flash('Cannot place order. Please check your API credentials.', 'danger')
                return redirect(url_for('autotrade.autotrade_page'))

            short_call_symbol = generate_occ_symbol(call_exec_form.underlying_symbol.data, call_exec_form.expiration_date.data, 'call', call_exec_form.strike_short.data)
            long_call_symbol = generate_occ_symbol(call_exec_form.underlying_symbol.data, call_exec_form.expiration_date.data, 'call', call_exec_form.strike_long.data)

            payload = {
                'class': 'multileg', 'symbol': call_exec_form.underlying_symbol.data.upper(), 'type': 'credit', 'duration': 'day',
                'price': f"{call_exec_form.limit_price.data:.2f}",
                'option_symbol[0]': short_call_symbol, 'side[0]': 'sell_to_open', 'quantity[0]': str(call_exec_form.quantity.data),
                'option_symbol[1]': long_call_symbol, 'side[1]': 'buy_to_open', 'quantity[1]': str(call_exec_form.quantity.data)
            }
            response = api.place_order(payload)
            if response and response.get('order'):
                flash('Call Credit Spread order submitted successfully!', 'success')
            else:
                flash(f"Call Credit Spread order failed: {response.get('errors', 'Unknown error')}", 'danger')
            return redirect(url_for('autotrade.autotrade_page'))
        else:
            flash(f"Execution form was invalid. Errors: {call_exec_form.errors}", 'danger')
    
    # --- ANALYSIS LOGIC ---
    if form.validate_on_submit():
        api = get_api_for_current_user()
        if not api:
            flash('Cannot perform analysis. Please check your API credentials.', 'danger')
            return redirect(url_for('autotrade.autotrade_page'))
        try:
            symbol = 'TSLA'
            quote_data = api.get_quotes([symbol])
            current_price = quote_data['quotes']['quote']['last']
            history_data = api.get_historical_prices(symbol)
            day_data = history_data['history']['day']
            stock_df = pd.DataFrame(day_data)
            stock_df.rename(columns={'close': 'Close'}, inplace=True)
            support, resistance = find_support_resistance(stock_df)
            exp_data = api.get_option_expirations(symbol)
            expirations = exp_data['expirations']['date']
            
            valid_supports = [s for s in reversed(support) if s < current_price]
            if valid_supports:
                sell_put_strike = round_to_nearest_five(valid_supports[0])
                buy_put_strike = sell_put_strike - 5
                proposed_trades['put_spread'] = {'sell_strike': sell_put_strike, 'buy_strike': buy_put_strike}
            
            valid_resistances = [r for r in resistance if r > current_price]
            if valid_resistances:
                sell_call_strike = round_to_nearest_five(valid_resistances[0])
                buy_call_strike = sell_call_strike + 5
                proposed_trades['call_spread'] = {'sell_strike': sell_call_strike, 'buy_strike': buy_call_strike}

            if len(expirations) > 3:
                proposed_trades['expiration'] = expirations[3]
            elif expirations:
                proposed_trades['expiration'] = expirations[-1]
            
            proposed_trades['current_price'] = current_price

            # --- NEW: Pre-populate form data ---
            if proposed_trades.get('expiration'):
                # Populate Put Form
                if proposed_trades.get('put_spread'):
                    put_exec_form.underlying_symbol.data = symbol
                    put_exec_form.expiration_date.data = proposed_trades['expiration']
                    put_exec_form.spread_type.data = 'put'
                    put_exec_form.credit_debit.data = 'credit'
                    put_exec_form.strike_short.data = proposed_trades['put_spread']['sell_strike']
                    put_exec_form.strike_long.data = proposed_trades['put_spread']['buy_strike']
                # Populate Call Form
                if proposed_trades.get('call_spread'):
                    call_exec_form.underlying_symbol.data = symbol
                    call_exec_form.expiration_date.data = proposed_trades['expiration']
                    call_exec_form.spread_type.data = 'call'
                    call_exec_form.credit_debit.data = 'credit'
                    call_exec_form.strike_short.data = proposed_trades['call_spread']['sell_strike']
                    call_exec_form.strike_long.data = proposed_trades['call_spread']['buy_strike']

            flash('Analysis complete. Review and execute the proposed trades below.', 'success')
        except Exception as e:
            flash(f"An error occurred during analysis: {e}", 'danger')

    return render_template('autotrade/autotrade.html', 
                           title='AutoTrade TSLA', 
                           form=form, 
                           trades=proposed_trades,
                           put_exec_form=put_exec_form,
                           call_exec_form=call_exec_form)