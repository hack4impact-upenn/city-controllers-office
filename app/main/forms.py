from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.fields import (
    StringField,
    SubmitField,
    DateField
)
from app.models import ProfServ

class ResultsForm(FlaskForm):
    vendor = StringField('Vendor Name')
    original_contract_id = StringField('Contract Number')
    start_dt = StringField('Start Date')
    end_dt = StringField('End Date')
    submit = SubmitField('View Results')
