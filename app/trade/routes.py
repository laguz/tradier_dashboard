from flask import render_template, redirect, url_for, flash, Blueprint, request, jsonify
from flask_login import login_required
from app.services.tradier_api import get_api_for_current_user
from app.trade.forms import StockOrderForm, OptionOrderForm, VerticalSpreadForm, IronCondorForm
from .trade_manager import (
    StockTradeHandler, OptionTradeHandler,
    VerticalSpreadTradeHandler, IronCondorTradeHandler
)

trade = Blueprint('trade', __name__)

def handle_trade_request(form, handler_class):
    """
    Handles the trade request process for a given form and handler.
    """
    api = get_api_for_current_user()
    if not api:
        flash('Cannot place order. Please check your API credentials in your profile.', 'danger')
        return redirect(url_for('trade.trading_page'))

    # Special handling for dynamically populated select fields
    if isinstance(form, (OptionOrderForm, VerticalSpreadForm, IronCondorForm)):
        submitted_expiration = request.form.get(f'{form._prefix}-expiration_date')
        if submitted_expiration:
            form.expiration_date.choices = [(submitted_expiration, submitted_expiration)]
    if isinstance(form, OptionOrderForm):
        submitted_strike = request.form.get(f'{form._prefix}-strike')
        if submitted_strike:
            form.strike.choices = [(submitted_strike, submitted_strike)]

    if form.validate_on_submit():
        handler = handler_class(api, form)
        handler.execute_trade()
    else:
        flash(f"{handler_class.form_name} form validation failed. Errors: {form.errors}", 'danger')

    return redirect(url_for('trade.trading_page'))


@trade.route('/trade', methods=['GET', 'POST'])
@login_required
def trading_page():
    forms = {
        'submit_stock': (StockOrderForm(prefix='stock'), StockTradeHandler),
        'submit_option': (OptionOrderForm(prefix='option'), OptionTradeHandler),
        'submit_vertical': (VerticalSpreadForm(prefix='vertical'), VerticalSpreadTradeHandler),
        'submit_condor': (IronCondorForm(prefix='condor'), IronCondorTradeHandler),
    }

    if request.method == 'POST':
        for submit_key, (form, handler) in forms.items():
            if submit_key in request.form:
                return handle_trade_request(form, handler)

    return render_template('trade/trade.html', title='Trade', **{f'{key.split("_")[1]}_form': form_tuple[0] for key, form_tuple in forms.items()})


@trade.route('/get_expirations/<string:symbol>')
@login_required
def get_expirations(symbol):
    api = get_api_for_current_user()
    if not api:
        return jsonify({'error': 'API client not available. Check profile.'}), 400

    data = api.get_option_expirations(symbol.upper())
    if data and data.get('expirations') and data['expirations'].get('date'):
        dates = data['expirations']['date']
        # Ensure dates are always returned as a list
        if not isinstance(dates, list):
            dates = [dates]
        return jsonify(dates=dates)
    else:
        # Provide a more specific error message
        return jsonify({'error': f'Could not fetch expiration dates for symbol: {symbol}. Response: {data}'}), 404


@trade.route('/get_strikes/<string:symbol>/<string:expiration>')
@login_required
def get_strikes(symbol, expiration):
    api = get_api_for_current_user()
    if not api:
        return jsonify({'error': 'API client not available.'}), 400

    data = api.get_option_chain(symbol.upper(), expiration)
    if data and data.get('options') and data['options'].get('option'):
        options_list = data['options']['option']
        # Ensure options_list is always a list
        if not isinstance(options_list, list):
            options_list = [options_list]
        # Use a set for efficiency and to automatically handle duplicates
        strikes = sorted(list(set(opt['strike'] for opt in options_list)))
        return jsonify(strikes=strikes)
    else:
        # Provide a more specific error message
        return jsonify({'error': f'Could not fetch strike prices for {symbol} on {expiration}. Response: {data}'}), 404