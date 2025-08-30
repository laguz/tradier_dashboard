import json
import pandas as pd
import numpy as np
import traceback
from collections import Counter
import plotly.graph_objects as go
import plotly.io as pio


from flask import render_template, Blueprint, flash, url_for, redirect
from flask_login import login_required
from .forms import ResearchForm
# Import the api service to get the current user's api key
from app.services.tradier_api import get_api_for_current_user


research = Blueprint('research', __name__)

def custom_round(price):
    # ... (This function is unchanged) ...
    if price < 100: return round(price)
    else: return round(price / 5) * 5

def find_support_resistance(data, window=10):
    # ... (This function is unchanged) ...
    all_support, all_resistance = [], []
    if data.empty: return [], []
    for i in range(window, len(data) - window):
        window_slice = data['Close'].iloc[i-window:i+window+1]
        current_price = data['Close'].iloc[i]
        price = current_price.item() if isinstance(current_price, (pd.Series, pd.DataFrame)) else current_price
        if np.isclose(price, window_slice.min()): all_support.append(price)
        if np.isclose(price, window_slice.max()): all_resistance.append(price)
    unique_supports = sorted(list(set(all_support)))
    unique_resistances = sorted(list(set(all_resistance)))
    plotted_support = []
    if unique_supports:
        last_support = unique_supports[0]
        plotted_support.append(last_support)
        for level in unique_supports:
            required_diff = 1 if last_support < 100 else 2
            if abs(level - last_support) >= required_diff:
                plotted_support.append(level)
                last_support = level
    plotted_resistance = []
    if unique_resistances:
        last_resistance = unique_resistances[0]
        plotted_resistance.append(last_resistance)
        for level in unique_resistances:
            required_diff = 1 if last_resistance < 100 else 2
            if abs(level - last_resistance) >= required_diff:
                plotted_resistance.append(level)
                last_resistance = level
    return plotted_support, plotted_resistance


@research.route('/research', methods=['GET', 'POST'])
@login_required
def research_page():
    form = ResearchForm()
    plot_json = None
    levels = {}

    if form.validate_on_submit():
        symbol = form.symbol.data.upper()
        period = form.period.data
        api = get_api_for_current_user()
        if not api:
            flash('Cannot fetch data. Please check your API credentials in your profile.', 'danger')
            return redirect(url_for('research.research_page'))

        try:
            history_data = api.get_historical_prices(symbol, period_days=period)
            if not history_data or not history_data.get('history') or history_data['history'] == 'null':
                raise ValueError(f"No historical data found for the symbol '{symbol}'.")

            day_data = history_data['history']['day']
            stock_df = pd.DataFrame(day_data)
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            stock_df.rename(columns={'date': 'Date', 'close': 'Close'}, inplace=True)

            support, resistance = find_support_resistance(stock_df)
            rounded_support = list(dict.fromkeys([custom_round(s) for s in support]))
            rounded_resistance = list(dict.fromkeys([custom_round(r) for r in resistance]))

            levels['support'] = rounded_support
            levels['resistance'] = rounded_resistance
            
            fig = go.Figure()

            # Add the main stock price trace
            fig.add_trace(go.Scatter(x=stock_df['Date'], y=stock_df['Close'], mode='lines',
                                     name=f'{symbol} Close Price', line=dict(color='blue')))

            # Add support levels
            for s_level in rounded_support:
                fig.add_shape(type="line", x0=stock_df['Date'].min(), y0=s_level,
                              x1=stock_df['Date'].max(), y1=s_level,
                              line=dict(color="green", width=2, dash="dash"), name='Support')

            # Add resistance levels
            for r_level in rounded_resistance:
                fig.add_shape(type="line", x0=stock_df['Date'].min(), y0=r_level,
                              x1=stock_df['Date'].max(), y1=r_level,
                              line=dict(color="red", width=2, dash="dash"), name='Resistance')
            
            fig.update_layout(
                title=f'{symbol} Support & Resistance Levels (Last {period} Days)',
                xaxis_title='Date',
                yaxis_title='Price (USD)',
                template='plotly_white',
                height=800,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                shapes=[
                    dict(type='line', yref='y', y0=s, x0=stock_df['Date'].min(), x1=stock_df['Date'].max(), line=dict(color='green', dash='dash')) for s in rounded_support
                ] + [
                    dict(type='line', yref='y', y0=r, x0=stock_df['Date'].min(), x1=stock_df['Date'].max(), line=dict(color='red', dash='dash')) for r in rounded_resistance
                ]
            )

            plot_json = pio.to_json(fig)


        except Exception as e:
            flash(f"An error occurred during analysis for {symbol}. Error: {e}", 'danger')
            traceback.print_exc()

    return render_template('research/research.html',
                           title='Research',
                           form=form,
                           plot_json=plot_json,
                           levels=levels)