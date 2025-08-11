from flask import render_template, redirect, url_for, flash, Blueprint, request
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from app import mongo
from app.auth.forms import UpdateAccountForm
from app.services.tradier_api import get_api_for_current_user

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    api = get_api_for_current_user()
    if not api:
        flash('Please provide your Tradier API key and account number on your profile page to view the dashboard.', 'warning')
        return redirect(url_for('main.profile'))

    balances_data = api.get_account_balances()
    positions_data = api.get_positions()
    
    kpis = {}
    positions = []
    
    if balances_data and balances_data.get('balances'):
        b = balances_data['balances']
        kpis = {
            'total_equity': b.get('total_equity'), 'total_cash': b.get('total_cash'),
            'unrealized_pl': b.get('unrealized_pl'), 'day_pl': b.get('pnl', {}).get('todays_pnl')
        }
    
    if positions_data and positions_data.get('positions') and positions_data['positions'] != 'null':
        pos_list = positions_data['positions']['position']
        raw_positions = pos_list if isinstance(pos_list, list) else [pos_list]
        
        symbols = [p['symbol'] for p in raw_positions]
        quotes_data = api.get_quotes(symbols)
        
        quotes_map = {}
        if quotes_data and quotes_data.get('quotes'):
            quotes_list = quotes_data['quotes']['quote']
            quotes_list = quotes_list if isinstance(quotes_list, list) else [quotes_list]
            quotes_map = {q['symbol']: q['last'] for q in quotes_list}
            
        for pos in raw_positions:
            quantity = float(pos['quantity'])
            cost_basis = float(pos['cost_basis'])
            last_price = quotes_map.get(pos['symbol'], 0)
            
            pos['market_value'] = quantity * float(last_price)
            pos['unrealized_pl'] = pos['market_value'] - cost_basis
            
            # --- ADDED CALCULATION ---
            if quantity > 0:
                pos['unit_cost'] = cost_basis / quantity
            else:
                pos['unit_cost'] = 0
            # --- END ADDED CALCULATION ---
            
            positions.append(pos)

    return render_template('dashboard.html', title='Dashboard', kpis=kpis, positions=positions)


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': { 'tradier_api_key': form.tradier_api_key.data, 'tradier_account_number': form.tradier_account_number.data }}
        )
        flash('Your account details have been updated!', 'success')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.tradier_api_key.data = current_user.tradier_api_key
        form.tradier_account_number.data = current_user.tradier_account_number
        
    return render_template('profile.html', title='Profile', form=form)