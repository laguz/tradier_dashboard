import base64
import io
import yfinance as yf
import pandas as pd
import numpy as np
import traceback

# Configure matplotlib for a non-GUI backend
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import render_template, Blueprint, flash
from flask_login import login_required
from .forms import ResearchForm

research = Blueprint('research', __name__)

# --- Custom Rounding Function (remains the same) ---
def custom_round(price):
    """
    Rounds the price based on its value:
    - If price < $100, rounds to the nearest whole number.
    - If price >= $100, rounds to the nearest number ending in 0 or 5.
    """
    if price < 100:
        return round(price)
    else:
        return round(price / 5) * 5

# --- UPDATED ANALYSIS FUNCTION ---
def find_support_resistance(data, window=10):
    """
    Finds support/resistance levels with a dynamic minimum price difference.
    """
    all_support = []
    all_resistance = []
    if data.empty:
        return [], []

    # Find all local minima and maxima
    for i in range(window, len(data) - window):
        window_slice = data['Close'].iloc[i-window:i+window+1]
        current_price = data['Close'].iloc[i]
        price = current_price.item() if isinstance(current_price, (pd.Series, pd.DataFrame)) else current_price
        
        if np.isclose(price, window_slice.min()):
            all_support.append(price)
        if np.isclose(price, window_slice.max()):
            all_resistance.append(price)

    unique_supports = sorted(list(set(all_support)))
    unique_resistances = sorted(list(set(all_resistance)))

    # Filter levels using the dynamic difference logic
    plotted_support = []
    if unique_supports:
        last_support = unique_supports[0]
        plotted_support.append(last_support)
        for level in unique_supports:
            # Set required difference based on the last plotted level's value
            required_diff = 1 if last_support < 100 else 2
            if abs(level - last_support) >= required_diff:
                plotted_support.append(level)
                last_support = level

    plotted_resistance = []
    if unique_resistances:
        last_resistance = unique_resistances[0]
        plotted_resistance.append(last_resistance)
        for level in unique_resistances:
            # Set required difference based on the last plotted level's value
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
        try:
            stock_df = yf.download(symbol, period='185d', interval='1d')
            if stock_df.empty:
                raise ValueError(f"No data found for the symbol '{symbol}'.")

            stock_df.reset_index(inplace=True)

            # Find precise levels with the new dynamic filtering
            support, resistance = find_support_resistance(stock_df)
            
            # Apply the custom rounding logic
            rounded_support = list(dict.fromkeys([custom_round(s) for s in support]))
            rounded_resistance = list(dict.fromkeys([custom_round(r) for r in resistance]))

            levels['support'] = rounded_support
            levels['resistance'] = rounded_resistance

            # --- PLOTTING LOGIC ---
            plt.style.use('fivethirtyeight')
            fig, ax = plt.subplots(figsize=(15, 8))
            
            ax.plot(stock_df['Date'], stock_df['Close'], label=f'{symbol} Close Price', color='blue', alpha=0.8)

            # Plot the custom-rounded support and resistance lines (colors are inverted as per last request)
            for s_level in rounded_support:
                ax.axhline(y=s_level, color='green', linestyle='--', linewidth=2)
            for r_level in rounded_resistance:
                ax.axhline(y=r_level, color='red', linestyle='--', linewidth=2)

            ax.set_title(f'{symbol} Support & Resistance Levels (Last 185 Days)', fontsize=20)
            ax.set_xlabel('Date', fontsize=14)
            ax.set_ylabel('Price (USD)', fontsize=14)
            ax.grid(True)
            
            # Create a clean legend
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
            print("\n--- AN ERROR OCCURRED IN RESEARCH ROUTE ---")
            print(f"Exception Type: {type(e)}")
            traceback.print_exc()
            print("-------------------------------------------\n")
            flash(f"An error occurred during analysis for {symbol}. Please check the server terminal for details.", 'danger')

    return render_template('research/research.html', 
                           title='Research', 
                           form=form, 
                           plot_url=plot_url,
                           levels=levels)