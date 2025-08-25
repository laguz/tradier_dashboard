import base64
import io
import pandas as pd
import numpy as np
import traceback
from collections import Counter

# Configure matplotlib for a non-GUI backend
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import render_template, Blueprint, flash
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
    plot_url = None
    levels = {}

    if form.validate_on_submit():
        symbol = form.symbol.data.upper()
        api = get_api_for_current_user() # Get the user's API client
        if not api:
            flash('Cannot fetch data. Please check your API credentials in your profile.', 'danger')
            return redirect(url_for('research.research_page'))

        try:
            # --- UPDATED DATA FETCHING LOGIC ---
            history_data = api.get_historical_prices(symbol)
            if not history_data or not history_data.get('history') or history_data['history'] == 'null':
                 raise ValueError(f"No historical data found for the symbol '{symbol}'.")
            
            # Convert Tradier's data into a Pandas DataFrame
            day_data = history_data['history']['day']
            stock_df = pd.DataFrame(day_data)
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            # Rename columns to match the old format for the analysis function
            stock_df.rename(columns={'date': 'Date', 'close': 'Close'}, inplace=True)
            # --- END OF UPDATED LOGIC ---

            support, resistance = find_support_resistance(stock_df)
            rounded_support = list(dict.fromkeys([custom_round(s) for s in support]))
            rounded_resistance = list(dict.fromkeys([custom_round(r) for r in resistance]))

            levels['support'] = rounded_support
            levels['resistance'] = rounded_resistance

            plt.style.use('fivethirtyeight')
            fig, ax = plt.subplots(figsize=(15, 8))
            
            ax.plot(stock_df['Date'], stock_df['Close'], label=f'{symbol} Close Price', color='blue', alpha=0.8)

            for s_level in rounded_support:
                ax.axhline(y=s_level, color='green', linestyle='--', linewidth=2)
            for r_level in rounded_resistance:
                ax.axhline(y=r_level, color='red', linestyle='--', linewidth=2)

            ax.set_title(f'{symbol} Support & Resistance Levels (Last 185 Days)', fontsize=20)
            ax.set_xlabel('Date', fontsize=14)
            ax.set_ylabel('Price (USD)', fontsize=14)
            ax.grid(True)
            
            handles, labels = [], []
            if rounded_support:
                handles.append(plt.Line2D([0], [0], color='green', linestyle='--', linewidth=2))
                labels.append('Support')
            if rounded_resistance:
                handles.append(plt.Line2D([0], [0], color='red', linestyle='--', linewidth=2))
                labels.append('Resistance')
            handles.append(plt.Line2D([0], [0], color='blue', alpha=0.8))
            labels.append(f'{symbol} Close Price')
            ax.legend(handles, labels, loc='best')

            plt.tight_layout()

            img = io.BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode('utf8')
            plt.close(fig)

        except Exception as e:
            # ... (Error handling is unchanged) ...
            flash(f"An error occurred during analysis for {symbol}. Error: {e}", 'danger')

    return render_template('research/research.html', 
                           title='Research', 
                           form=form, 
                           plot_url=plot_url,
                           levels=levels)