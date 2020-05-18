from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField,
    SubmitField
)

class ResultsForm(FlaskForm):
    vendor_name = StringField('Vendor Name')
    contract_number = StringField('Contract Number')
    submit = SubmitField('View Results')
