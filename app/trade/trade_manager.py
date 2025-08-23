from abc import ABC, abstractmethod
from flask import flash
from .utils import generate_occ_symbol

class TradeHandler(ABC):
    """
    Base class for handling different types of trades.
    """
    def __init__(self, api, form):
        self.api = api
        self.form = form

    def execute_trade(self):
        """
        Executes the trade and handles the response.
        """
        payload = self._create_payload()
        response = self.api.place_order(payload)
        self._process_response(response)

    @abstractmethod
    def _create_payload(self):
        """
        Creates the payload for the API request.
        """
        pass

    def _process_response(self, response):
        """
        Processes the API response and flashes messages.
        """
        if response and response.get('order'):
            status = response['order'].get('status', 'N/A')
            flash(f"{self.form_name} submitted! Status: {status}", 'success')
        elif response and response.get('errors'):
            errors = ', '.join(response['errors']['error'])
            flash(f"{self.form_name} failed: {errors}", 'danger')
        else:
            flash(f'An unknown error occurred while placing the {self.form_name.lower()}.', 'danger')

    @property
    @abstractmethod
    def form_name(self):
        """

        Returns the name of the form.
        """
        pass


class StockTradeHandler(TradeHandler):
    """Handles stock trades."""
    form_name = "Stock order"

    def _create_payload(self):
        payload = {
            'class': 'equity',
            'symbol': self.form.symbol.data.upper(),
            'duration': self.form.duration.data,
            'side': self.form.side.data,
            'quantity': str(self.form.quantity.data),
            'type': self.form.order_type.data
        }
        if self.form.limit_price.data is not None:
            payload['price'] = f"{self.form.limit_price.data:.2f}"
        if self.form.stop_price.data is not None:
            payload['stop'] = f"{self.form.stop_price.data:.2f}"
        return payload


class OptionTradeHandler(TradeHandler):
    """Handles single-leg option trades."""
    form_name = "Single option order"

    def _create_payload(self):
        option_symbol = generate_occ_symbol(
            underlying=self.form.underlying_symbol.data,
            expiration_str=self.form.expiration_date.data,
            option_type=self.form.option_type.data,
            strike=self.form.strike.data
        )
        payload = {
            'class': 'option',
            'symbol': self.form.underlying_symbol.data.upper(),
            'option_symbol': option_symbol,
            'side': self.form.side.data,
            'quantity': str(self.form.quantity.data),
            'type': self.form.order_type.data,
            'duration': self.form.duration.data
        }
        if self.form.limit_price.data is not None:
            payload['price'] = f"{self.form.limit_price.data:.2f}"
        return payload


class VerticalSpreadTradeHandler(TradeHandler):
    """Handles vertical spread trades."""
    form_name = "Vertical spread order"

    def _create_payload(self):
        short_leg_symbol = generate_occ_symbol(
            underlying=self.form.underlying_symbol.data,
            expiration_str=self.form.expiration_date.data,
            option_type=self.form.spread_type.data,
            strike=self.form.strike_short.data
        )
        long_leg_symbol = generate_occ_symbol(
            underlying=self.form.underlying_symbol.data,
            expiration_str=self.form.expiration_date.data,
            option_type=self.form.spread_type.data,
            strike=self.form.strike_long.data
        )
        return {
            'class': 'multileg',
            'symbol': self.form.underlying_symbol.data.upper(),
            'type': self.form.credit_debit.data,
            'duration': self.form.duration.data,
            'price': f"{self.form.limit_price.data:.2f}",
            'option_symbol[0]': short_leg_symbol,
            'side[0]': 'sell_to_open',
            'quantity[0]': str(self.form.quantity.data),
            'option_symbol[1]': long_leg_symbol,
            'side[1]': 'buy_to_open',
            'quantity[1]': str(self.form.quantity.data)
        }


class IronCondorTradeHandler(TradeHandler):
    """Handles iron condor trades."""
    form_name = "Iron condor order"

    def _create_payload(self):
        long_put = generate_occ_symbol(self.form.underlying_symbol.data, self.form.expiration_date.data, 'put', self.form.long_put_strike.data)
        short_put = generate_occ_symbol(self.form.underlying_symbol.data, self.form.expiration_date.data, 'put', self.form.short_put_strike.data)
        short_call = generate_occ_symbol(self.form.underlying_symbol.data, self.form.expiration_date.data, 'call', self.form.short_call_strike.data)
        long_call = generate_occ_symbol(self.form.underlying_symbol.data, self.form.expiration_date.data, 'call', self.form.long_call_strike.data)
        return {
            'class': 'multileg',
            'symbol': self.form.underlying_symbol.data.upper(),
            'type': 'credit',
            'duration': self.form.duration.data,
            'price': f"{self.form.limit_price.data:.2f}",
            'option_symbol[0]': long_put,
            'side[0]': 'buy_to_open',
            'quantity[0]': str(self.form.quantity.data),
            'option_symbol[1]': short_put,
            'side[1]': 'sell_to_open',
            'quantity[1]': str(self.form.quantity.data),
            'option_symbol[2]': short_call,
            'side[2]': 'sell_to_open',
            'quantity[2]': str(self.form.quantity.data),
            'option_symbol[3]': long_call,
            'side[3]': 'buy_to_open',
            'quantity[3]': str(self.form.quantity.data),
        }
