import base64
import io
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flask import render_template, Blueprint, flash
from flask_login import login_required
from .forms import ResearchForm

# Create a Blueprint for research routes
research = Blueprint('research', __name__)

def find_support_resistance(data, window=10):
    """
    Finds support and resistance levels in the price data.
    """
    support_levels = []
    resistance_levels = []
    if data.empty:
        return [], []

    for i in range(window, len(data) - window):
        window_slice = data['Close'][i-window:i+window+1]
        current_price = data['Close'][i]
        
        if current_price == window_slice.min():
            support_levels.append(current_price)
            
        if current_price == window_slice.max():
            resistance_levels.append(current_price)
            
    return sorted(list(set(support_levels))), sorted(list(set(resistance_levels)))

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
                raise ValueError("No data found for the symbol.")

            support, resistance = find_support_resistance(stock_df)
            levels['support'] = [round(s, 2) for s in support]
            levels['resistance'] = [round(r, 2) for r in resistance]

            # --- Generate Plot ---
            fig, ax = plt.subplots(figsize=(15, 8))
            ax.plot(stock_df.index, stock_df['Close'], label=f'{symbol} Close Price', color='blue', alpha=0.8)

            for s_level in support:
                ax.axhline(y=s_level, color='green', linestyle='--', linewidth=1.5)
            for r_level in resistance:
                ax.axhline(y=r_level, color='red', linestyle='--', linewidth=1.5)

            ax.set_title(f'{symbol} Support and Resistance Levels (Last 185 Days)', fontsize=20)
            ax.set_xlabel('Date', fontsize=14)
            ax.set_ylabel('Price (USD)', fontsize=14)
            ax.grid(True)
            plt.tight_layout()

            # --- Convert plot to image for web display ---
            img = io.BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode('utf8')
            plt.close(fig) # Close the figure to free memory

        except Exception as e:
            flash(f"Could not generate analysis for {symbol}. Error: {e}", 'danger')

    return render_template('research/research.html', 
                           title='Research', 
                           form=form, 
                           plot_url=plot_url,
                           levels=levels)