from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ResearchForm(FlaskForm):
    """Form for submitting a stock symbol for research."""
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    submit = SubmitField('Get Analysis')