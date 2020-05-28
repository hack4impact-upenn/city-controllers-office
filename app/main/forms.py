from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.fields import (
    StringField,
    SubmitField,
    DateField
)

class ResultsForm(FlaskForm):
    vendor_name = StringField('Vendor Name')
    contract_number = StringField('Contract Number')
    start_date = StringField('Start Date')
    end_date = StringField('End Date')
    submit = SubmitField('View Results')
