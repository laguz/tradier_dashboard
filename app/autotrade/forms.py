from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, IntegerField, DecimalField
from wtforms.validators import DataRequired, NumberRange

class AutoTradeForm(FlaskForm):
    """Form to trigger the automated trade analysis."""
    symbol = StringField('Stock Symbol', validators=[DataRequired()], default='TSLA')
    submit = SubmitField('Find Spreads')

class ExecuteTradeForm(FlaskForm):
    """
    Form to execute a single proposed multi-leg trade.
    It's pre-populated with data and the user can adjust quantity and price.
    """
    # Hidden fields to carry the core trade data
    underlying_symbol = HiddenField(validators=[DataRequired()])
    expiration_date = HiddenField(validators=[DataRequired()])
    spread_type = HiddenField(validators=[DataRequired()]) # 'put' or 'call'
    credit_debit = HiddenField(validators=[DataRequired()]) # 'credit' or 'debit'
    strike_short = HiddenField(validators=[DataRequired()])
    strike_long = HiddenField(validators=[DataRequired()])
    
    # Visible fields for user adjustment
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Price (Net)', places=2, validators=[DataRequired()])
    
    submit = SubmitField('Execute Trade')