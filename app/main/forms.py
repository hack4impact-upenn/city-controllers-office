from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.fields import (
    StringField,
    SubmitField,
    DateField,
    DecimalField
)
from wtforms import validators
from app.models import ProfServ

class ResultsForm(FlaskForm):
    vendor = StringField('Vendor Name')
    original_contract_id = StringField('Contract Number')
    start_dt = DateField('Start Date (MM-DD-YYYY)', format='%m-%d-%Y', validators=(validators.Optional(),))
    end_dt = DateField('End Date (MM-DD-YYYY)', format='%m-%d-%Y', validators=(validators.Optional(),))
    minimum = DecimalField('Minimum', places=2, validators=(validators.Optional(),))
    maximum = DecimalField('Maximum', places=2, validators=(validators.Optional(),))
    keyword = StringField('Keyword')
    submit = SubmitField('View Results')


class CSVDownloadDBForm(FlaskForm):
    database_csv_submit = SubmitField("Download Database")

class CSVDownloadRSForm(FlaskForm):
    results_csv_submit = SubmitField("Download Results")
