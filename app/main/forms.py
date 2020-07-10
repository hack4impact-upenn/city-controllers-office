from flask_wtf import FlaskForm
from datetime import datetime
from wtforms.fields import (
    StringField,
    SubmitField,
    DateField,
    DecimalField,
    BooleanField,
    SelectField
)
from wtforms import validators
from app.models import ProfServ

class ResultsForm(FlaskForm):
    department = SelectField('Department', coerce=str, validators=(validators.Optional(),))
    contract_type = SelectField('Contract Type', coerce=str, validators=(validators.Optional(),))
    vendor = StringField('Vendor Name')
    original_contract_id = StringField('Contract Number')
    start_dt = DateField('Start Date (MM-DD-YYYY)', format='%m-%d-%Y', validators=(validators.Optional(),))
    end_dt = DateField('End Date (MM-DD-YYYY)', format='%m-%d-%Y', validators=(validators.Optional(),))
    minimum = DecimalField('Minimum', places=2, validators=(validators.Optional(),))
    maximum = DecimalField('Maximum', places=2, validators=(validators.Optional(),))
    keyword = StringField('Keyword')
    for_profit = BooleanField('For Profit', default=True)
    non_profit = BooleanField('Nonprofit', default=True)
    adv = BooleanField('Advertised', default=True)
    ex = BooleanField('Exempt', default=True)
    submit = SubmitField('View Results',
    render_kw={
        'style':'width: 100%'
    })

class CSVDownloadDBForm(FlaskForm):
    database_csv_submit = SubmitField("Download Database",
    render_kw={
        'style':'background:none; text-align: left; padding: 0'
    })

class CSVDownloadRSForm(FlaskForm):
    results_csv_submit = SubmitField("Download Results",
    render_kw={
        'style':'background:none; text-align: left; padding: 0; margin-right: 25px;'
    })

class SortByAmountHiLoForm(FlaskForm):
    amount_hi_lo_submit = SubmitField("Amount (Descending)", 
    render_kw={
        'style':'border:none; background:none; text-align:left; font-weight: 400; padding: 0; margin: 0; color: black'
    })

class SortByAmountLoHiForm(FlaskForm):
    amount_lo_hi_submit = SubmitField("Amount (Ascending)",
    render_kw={
        'style':'border:none; background:none; text-align:left; font-weight: 400; padding: 0; margin: 0; color: black'
    })

class SortByABC(FlaskForm):
    name_abc = SubmitField("Vendor Name (A-Z)",
    render_kw={
        'style':'border:none; background:none; text-align:left; font-weight: 400; padding: 0; margin: 0; color: black'
    })

class SortByCBA(FlaskForm):
    name_cba = SubmitField("Vendor Name (Z-A)",
    render_kw={
        'style':'border:none; background:none; text-align:left; font-weight: 400; padding: 0; margin: 0; color: black'
    })
