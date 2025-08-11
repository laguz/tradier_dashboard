from flask import render_template, redirect, url_for, flash, Blueprint, request, jsonify
from flask_login import login_required
from app.services.tradier_api import get_api_for_current_user
from app.trade.forms import StockOrderForm, OptionOrderForm, VerticalSpreadForm, IronCondorForm
from app.trade.utils import generate_occ_symbol

trade = Blueprint('trade', __name__)

@trade.route('/trade', methods=['GET', 'POST'])
@login_required
def trading_page():
    # --- ADDED PREFIXES TO EACH FORM ---
    stock_form = StockOrderForm(prefix='stock')
    option_form = OptionOrderForm(prefix='option')
    vertical_form = VerticalSpreadForm(prefix='vertical')
    condor_form = IronCondorForm(prefix='condor')

    if 'submit_stock' in request.form and stock_form.validate_on_submit():
        # ... (stock submission logic remains unchanged)
        api = get_api_for_current_user()
        if not api:
            flash('Cannot place order. Please check your API credentials in your profile.', 'danger')
            return redirect(url_for('trade.trading_page'))
        order_payload = {
            'class': 'equity', 'symbol': stock_form.symbol.data.upper(), 'duration': stock_form.duration.data,
            'side': stock_form.side.data, 'quantity': str(stock_form.quantity.data), 'type': stock_form.order_type.data
        }
        if stock_form.limit_price.data is not None: order_payload['price'] = f"{stock_form.limit_price.data:.2f}"
        if stock_form.stop_price.data is not None: order_payload['stop'] = f"{stock_form.stop_price.data:.2f}"
        response = api.place_order(order_payload)
        if response and response.get('order'): flash(f"Stock order submitted! Status: {response['order'].get('status', 'N/A')}", 'success')
        elif response and response.get('errors'): flash(f"Order failed: {', '.join(response['errors']['error'])}", 'danger')
        else: flash('An unknown error occurred while placing the order.', 'danger')
        return redirect(url_for('trade.trading_page'))

    elif 'submit_option' in request.form and option_form.validate_on_submit():
        # ... (option submission logic remains unchanged)
        api = get_api_for_current_user()
        if not api:
            flash('Cannot place order. Please check your API credentials in your profile.', 'danger')
            return redirect(url_for('trade.trading_page'))
        order_payload = {
            'class': 'option', 'symbol': option_form.underlying_symbol.data.upper(), 'option_symbol': option_form.option_symbol.data.upper(),
            'side': option_form.side.data, 'quantity': str(option_form.quantity.data), 'type': option_form.order_type.data, 'duration': option_form.duration.data
        }
        if option_form.limit_price.data is not None: order_payload['price'] = f"{option_form.limit_price.data:.2f}"
        response = api.place_order(order_payload)
        if response and response.get('order'): flash(f"Option order submitted! Status: {response['order'].get('status', 'N/A')}", 'success')
        elif response and response.get('errors'): flash(f"Order failed: {', '.join(response['errors']['error'])}", 'danger')
        else: flash('An unknown error occurred while placing the option order.', 'danger')
        return redirect(url_for('trade.trading_page'))

    elif 'submit_vertical' in request.form and vertical_form.validate_on_submit():
        # ... (vertical spread submission logic remains unchanged)
        api = get_api_for_current_user()
        if not api:
            flash('Cannot place order. Please check your API credentials in your profile.', 'danger')
            return redirect(url_for('trade.trading_page'))
        short_leg_symbol = generate_occ_symbol(underlying=vertical_form.underlying_symbol.data, expiration_str=vertical_form.expiration_date.data, option_type=vertical_form.spread_type.data, strike=vertical_form.strike_short.data)
        long_leg_symbol = generate_occ_symbol(underlying=vertical_form.underlying_symbol.data, expiration_str=vertical_form.expiration_date.data, option_type=vertical_form.spread_type.data, strike=vertical_form.strike_long.data)
        order_payload = {
            'class': 'multileg', 'symbol': vertical_form.underlying_symbol.data.upper(), 'type': vertical_form.credit_debit.data,
            'duration': vertical_form.duration.data, 'price': f"{vertical_form.limit_price.data:.2f}",
            'option_symbol[0]': short_leg_symbol, 'side[0]': 'sell_to_open', 'quantity[0]': str(vertical_form.quantity.data),
            'option_symbol[1]': long_leg_symbol, 'side[1]': 'buy_to_open', 'quantity[1]': str(vertical_form.quantity.data)
        }
        response = api.place_order(order_payload)
        if response and response.get('order'): flash(f"Vertical spread order submitted successfully! Status: {response['order'].get('status', 'N/A')}", 'success')
        elif response and response.get('errors'): flash(f"Order failed: {', '.join(response['errors']['error'])}", 'danger')
        else: flash('An unknown error occurred while placing the spread order.', 'danger')
        return redirect(url_for('trade.trading_page'))

    elif 'submit_condor' in request.form and condor_form.validate_on_submit():
        # ... (iron condor submission logic remains unchanged)
        api = get_api_for_current_user()
        if not api:
            flash('Cannot place order. Please check your API credentials in your profile.', 'danger')
            return redirect(url_for('trade.trading_page'))
        long_put = generate_occ_symbol(condor_form.underlying_symbol.data, condor_form.expiration_date.data, 'put', condor_form.long_put_strike.data)
        short_put = generate_occ_symbol(condor_form.underlying_symbol.data, condor_form.expiration_date.data, 'put', condor_form.short_put_strike.data)
        short_call = generate_occ_symbol(condor_form.underlying_symbol.data, condor_form.expiration_date.data, 'call', condor_form.short_call_strike.data)
        long_call = generate_occ_symbol(condor_form.underlying_symbol.data, condor_form.expiration_date.data, 'call', condor_form.long_call_strike.data)
        order_payload = {
            'class': 'multileg', 'symbol': condor_form.underlying_symbol.data.upper(), 'type': 'credit', 'duration': condor_form.duration.data,
            'price': f"{condor_form.limit_price.data:.2f}",
            'option_symbol[0]': long_put, 'side[0]': 'buy_to_open', 'quantity[0]': str(condor_form.quantity.data),
            'option_symbol[1]': short_put, 'side[1]': 'sell_to_open', 'quantity[1]': str(condor_form.quantity.data),
            'option_symbol[2]': short_call, 'side[2]': 'sell_to_open', 'quantity[2]': str(condor_form.quantity.data),
            'option_symbol[3]': long_call, 'side[3]': 'buy_to_open', 'quantity[3]': str(condor_form.quantity.data),
        }
        response = api.place_order(order_payload)
        if response and response.get('order'): flash(f"Iron Condor order submitted successfully! Status: {response['order'].get('status', 'N/A')}", 'success')
        elif response and response.get('errors'): flash(f"Order failed: {', '.join(response['errors']['error'])}", 'danger')
        else: flash('An unknown error occurred while placing the condor order.', 'danger')
        return redirect(url_for('trade.trading_page'))

    return render_template('trade/trade.html', 
                           title='Trade',
                           stock_form=stock_form,
                           option_form=option_form,
                           vertical_form=vertical_form,
                           condor_form=condor_form)

@trade.route('/get_expirations/<string:symbol>')
@login_required
def get_expirations(symbol):
    api = get_api_for_current_user()
    if not api:
        return jsonify({'error': 'API client not available. Check profile.'}), 400
    data = api.get_option_expirations(symbol.upper())
    if data and data.get('expirations') and data['expirations'].get('date'):
        dates = data['expirations']['date']
        if not isinstance(dates, list):
            dates = [dates]
        return jsonify(dates=dates)
    else:
        return jsonify({'error': 'Could not fetch expiration dates for this symbol.'}), 404