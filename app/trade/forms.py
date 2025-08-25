from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError

class UnvalidatedSelectField(SelectField):
    """
    A custom SelectField that skips the choice validation.
    This is useful for fields populated dynamically by JavaScript.
    """
    def pre_validate(self, form):
        # Overriding pre_validate to prevent the "Not a valid choice" error.
        pass

class StockOrderForm(FlaskForm):
    """Form for placing a stock trade order."""
    symbol = StringField('Symbol', validators=[DataRequired()])
    side = SelectField('Side', choices=[('buy', 'Buy'), ('sell', 'Sell')], validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, message="Quantity must be at least 1.")])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit'), ('stop', 'Stop'), ('stop_limit', 'Stop Limit')], validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    limit_price = DecimalField('Limit Price', places=2, validators=[Optional()])
    stop_price = DecimalField('Stop Price', places=2, validators=[Optional()])


class OptionOrderForm(FlaskForm):
    """Form for placing a single-leg option order."""
    underlying_symbol = StringField('Underlying Symbol', validators=[DataRequired()])
    expiration_date = UnvalidatedSelectField('Expiration', validators=[DataRequired()], choices=[])
    strike = UnvalidatedSelectField('Strike', validators=[DataRequired()], choices=[])
    option_type = SelectField('Type', choices=[('call', 'Call'), ('put', 'Put')], validators=[DataRequired()])
    side = SelectField('Side', choices=[('buy_to_open', 'Buy to Open'), ('buy_to_close', 'Buy to Close'), ('sell_to_open', 'Sell to Open'), ('sell_to_close', 'Sell to Close')], validators=[DataRequired()])
    quantity = IntegerField('Quantity (Contracts)', validators=[DataRequired(), NumberRange(min=1)])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit')], validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    limit_price = DecimalField('Limit Price', places=2, validators=[Optional()])


class VerticalSpreadForm(FlaskForm):
    """Form for placing a two-leg vertical spread order."""
    underlying_symbol = StringField('Underlying Symbol', validators=[DataRequired()])
    expiration_date = UnvalidatedSelectField('Expiration', validators=[DataRequired()], choices=[])
    spread_type = SelectField('Option Type', choices=[('put', 'Put Spread'), ('call', 'Call Spread')], validators=[DataRequired()])
    credit_debit = SelectField('Strategy', choices=[('credit', 'Credit (Sell Spread)'), ('debit', 'Debit (Buy Spread)')], validators=[DataRequired()])
    strike_short = DecimalField('Strike to Sell', places=2, validators=[DataRequired()])
    strike_long = DecimalField('Strike to Buy', places=2, validators=[DataRequired()])
    quantity = IntegerField('Quantity of Spreads', validators=[DataRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Price (Net)', places=2, validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])


class IronCondorForm(FlaskForm):
    """Form for placing a four-leg iron condor order."""
    underlying_symbol = StringField('Underlying Symbol', validators=[DataRequired()])
    expiration_date = UnvalidatedSelectField('Expiration', validators=[DataRequired()], choices=[])
    long_put_strike = DecimalField('Buy Put Strike', places=2, validators=[DataRequired()])
    short_put_strike = DecimalField('Sell Put Strike', places=2, validators=[DataRequired()])
    short_call_strike = DecimalField('Sell Call Strike', places=2, validators=[DataRequired()])
    long_call_strike = DecimalField('Buy Call Strike', places=2, validators=[DataRequired()])
    quantity = IntegerField('Quantity of Condors', validators=[DataRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Price (Net Credit)', places=2, validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    
    def validate(self, extra_validators=None):
        # Run the standard field-level validators first
        if not super().validate(extra_validators):
            return False
        
        # Store data in variables for clarity and to ensure they are not None
        lp = self.long_put_strike.data
        sp = self.short_put_strike.data
        sc = self.short_call_strike.data
        lc = self.long_call_strike.data

        # Check that all strike data is present before attempting to compare
        if all((lp, sp, sc, lc)):
            if not (lp < sp < sc < lc):
                # Create a more detailed error message
                msg = f"Strike order is invalid. Your values were: {lp} < {sp} < {sc} < {lc}. Please ensure they are in ascending order."
                self.long_put_strike.errors.append(msg)
                return False
        return True