from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class ResearchForm(FlaskForm):
    """Form for submitting a stock symbol for research."""
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    period = SelectField(
        'Analysis Period',
        choices=[
            (32, '32 Days'),
            (94, '94 Days'),
            (185, '185 Days'),
            (366, '366 Days')
        ],
        default=185,
        coerce=int,
        validators=[DataRequired()]
    )
    submit = SubmitField('Get Analysis')