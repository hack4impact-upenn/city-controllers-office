from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField,
    SubmitField
)

class ResultsForm(FlaskForm):
    vendor_name = StringField('Vendor Name')
    contract_number = StringField('Contract Number')
    submit = SubmitField('View Results')

class CSVDownloadDBForm(FlaskForm):
    database_csv_submit = SubmitField("Download Database")

class CSVDownloadRSForm(FlaskForm):
    results_csv_submit = SubmitField("Download Results")