from flask import render_template, redirect, url_for, flash, Blueprint, request, jsonify
from flask_login import login_required
from app.services.tradier_api import get_api_for_current_user
from app.trade.forms import StockOrderForm, OptionOrderForm, VerticalSpreadForm, IronCondorForm
from app.trade.utils import generate_occ_symbol

trade = Blueprint('trade', __name__)

@trade.route('/trade', methods=['GET', 'POST'])
@login_required
def trading_page():
    stock_form = StockOrderForm(prefix='stock')
    option_form = OptionOrderForm(prefix='option')
    vertical_form = VerticalSpreadForm(prefix='vertical')
    condor_form = IronCondorForm(prefix='condor')

    # --- MODIFIED STOCK ORDER LOGIC ---
    if 'submit_stock' in request.form:
        if stock_form.validate_on_submit():
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
            
            if response and response.get('order'):
                flash(f"Stock order submitted! Status: {response['order'].get('status', 'N/A')}", 'success')
            elif response and response.get('errors'):
                flash(f"Order failed: {', '.join(response['errors']['error'])}", 'danger')
            else:
                flash('An unknown error occurred while placing the order.', 'danger')
            
            return redirect(url_for('trade.trading_page'))
        else:
            # ADDED THIS BLOCK TO SHOW ERRORS
            flash(f"Stock form validation failed. Errors: {stock_form.errors}", 'danger')
    # --- END MODIFIED LOGIC ---

    elif 'submit_option' in request.form:
        # ... (option logic remains unchanged) ...
        return redirect(url_for('trade.trading_page'))

    elif 'submit_vertical' in request.form:
        # ... (vertical spread logic remains unchanged) ...
        return redirect(url_for('trade.trading_page'))

    elif 'submit_condor' in request.form:
        # ... (iron condor logic remains unchanged) ...
        return redirect(url_for('trade.trading_page'))

    return render_template('trade/trade.html', 
                           title='Trade', stock_form=stock_form, option_form=option_form,
                           vertical_form=vertical_form, condor_form=condor_form)

# ... (get_expirations and get_strikes routes are unchanged) ...
@trade.route('/get_expirations/<string:symbol>')
@login_required
def get_expirations(symbol):
    api = get_api_for_current_user()
    if not api: return jsonify({'error': 'API client not available. Check profile.'}), 400
    data = api.get_option_expirations(symbol.upper())
    if data and data.get('expirations') and data['expirations'].get('date'):
        dates = data['expirations']['date']
        if not isinstance(dates, list): dates = [dates]
        return jsonify(dates=dates)
    else: return jsonify({'error': 'Could not fetch expiration dates for this symbol.'}), 404


@trade.route('/get_strikes/<string:symbol>/<string:expiration>')
@login_required
def get_strikes(symbol, expiration):
    api = get_api_for_current_user()
    if not api: return jsonify({'error': 'API client not available.'}), 400
    data = api.get_option_chain(symbol.upper(), expiration)
    if data and data.get('options') and data['options'].get('option'):
        options_list = data['options']['option']
        if not isinstance(options_list, list): options_list = [options_list]
        strikes = sorted(list(set(opt['strike'] for opt in options_list)))
        return jsonify(strikes=strikes)
    else: return jsonify({'error': 'Could not fetch strike prices.'}), 404