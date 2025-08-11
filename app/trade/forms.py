from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError

class StockOrderForm(FlaskForm):
    """Form for placing a stock trade order."""
    # ... (no changes to this form)
    symbol = StringField('Symbol', validators=[DataRequired()])
    side = SelectField('Side', choices=[('buy', 'Buy'), ('sell', 'Sell')], validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, message="Quantity must be at least 1.")])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit'), ('stop', 'Stop'), ('stop_limit', 'Stop Limit')], validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    limit_price = DecimalField('Limit Price', places=2, validators=[Optional()])
    stop_price = DecimalField('Stop Price', places=2, validators=[Optional()])
    submit = SubmitField('Preview Order')


class OptionOrderForm(FlaskForm):
    """Form for placing a single-leg option order."""
    # ... (no changes to this form)
    underlying_symbol = StringField('Underlying Symbol', validators=[DataRequired()])
    option_symbol = StringField('Option Symbol', validators=[DataRequired()])
    side = SelectField('Side', choices=[('buy_to_open', 'Buy to Open'), ('buy_to_close', 'Buy to Close'), ('sell_to_open', 'Sell to Open'), ('sell_to_close', 'Sell to Close')], validators=[DataRequired()])
    quantity = IntegerField('Quantity (Contracts)', validators=[DataRequired(), NumberRange(min=1)])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit')], validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    limit_price = DecimalField('Limit Price', places=2, validators=[Optional()])
    submit = SubmitField('Preview Option Order')


class VerticalSpreadForm(FlaskForm):
    """Form for placing a two-leg vertical spread order."""
    underlying_symbol = StringField('Underlying Symbol', validators=[DataRequired()])
    
    # --- CHANGED LINE ---
    expiration_date = SelectField('Expiration', validators=[DataRequired()], choices=[])
    
    spread_type = SelectField('Option Type', choices=[
        ('put', 'Put Spread'),
        ('call', 'Call Spread')
    ], validators=[DataRequired()])
    credit_debit = SelectField('Strategy', choices=[
        ('credit', 'Credit (Sell Spread)'),
        ('debit', 'Debit (Buy Spread)')
    ], validators=[DataRequired()])
    strike_short = DecimalField('Strike to Sell', places=2, validators=[DataRequired()])
    strike_long = DecimalField('Strike to Buy', places=2, validators=[DataRequired()])
    quantity = IntegerField('Quantity of Spreads', validators=[DataRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Price (Net)', places=2, validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    submit = SubmitField('Preview Spread Order')


class IronCondorForm(FlaskForm):
    """Form for placing a four-leg iron condor order."""
    underlying_symbol = StringField('Underlying Symbol', validators=[DataRequired()])

    # --- CHANGED LINE ---
    expiration_date = SelectField('Expiration', validators=[DataRequired()], choices=[])
    
    long_put_strike = DecimalField('Long Put Strike', places=2, validators=[DataRequired()])
    short_put_strike = DecimalField('Short Put Strike', places=2, validators=[DataRequired()])
    short_call_strike = DecimalField('Short Call Strike', places=2, validators=[DataRequired()])
    long_call_strike = DecimalField('Long Call Strike', places=2, validators=[DataRequired()])
    quantity = IntegerField('Quantity of Condors', validators=[DataRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Price (Net Credit)', places=2, validators=[DataRequired()])
    duration = SelectField('Duration', choices=[('day', 'Day Order'), ('gtc', 'Good \'til Canceled')], validators=[DataRequired()])
    submit = SubmitField('Preview Condor Order')
    
    def validate(self, extra_validators=None):
        if not super(IronCondorForm, self).validate(extra_validators):
            return False
        if not (self.long_put_strike.data < self.short_put_strike.data and \
                self.short_put_strike.data < self.short_call_strike.data and \
                self.short_call_strike.data < self.long_call_strike.data):
            msg = "Strikes must be in ascending order: Long Put < Short Put < Short Call < Long Call."
            self.long_put_strike.errors.append(msg)
            return False
        return True