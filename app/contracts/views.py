from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
import csv
from datetime import datetime
from flask_rq import get_queue
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import pandas as pd
from app import db
from app.models import ProfServ, Profit_Status, Exempt_Status, Department, ContrType

contract = Blueprint('ProfServ', __name__)
deptnames = Blueprint('Department', __name__)
typenames = Blueprint('ContrType', __name__)


@contract.route('/search')
def readCSV(file, quarter_year="Q2-2019"):
    dept_names = []
    contr_type_names = []
    now = datetime.now()

    upload_successful = False
    found_duplicate= False
    found_broken_row = False

    csv_data = pd.read_csv(file)
    expected_headers = ['original_contract_id', 'current_item_id', 'department_name', 'vendor', 'contract_structure_type', \
                        'short_desc', 'start_dt', 'end_dt', 'days_remaining', 'amt', \
                        'tot_payments', 'orig_vendor', 'exempt_status', 'adv_or_exempt', 'profit_status']
    headers_list = list(csv_data.columns)
    # checks if all headers in csv data are expected; if not expected, then directly fails upload
    if headers_list and len(headers_list) == len(expected_headers) and headers_list == expected_headers:
        # if reached this step, then csv file upload is successful
        upload_successful = True
        for index, headers in csv_data.iterrows():
            row = [
                headers['original_contract_id'],
                headers['current_item_id'],
                headers['department_name'],
                headers['vendor'],
                headers['contract_structure_type'],
                headers['short_desc'],
                headers['start_dt'],
                headers['end_dt'],
                headers['days_remaining'],
                headers['amt'],
                headers['tot_payments'],
                headers['orig_vendor'],
                headers['exempt_status'],
                headers['adv_or_exempt'],
                headers['profit_status'],
            ]

            # try/except statement for detecting broken rows
            try:
                dept_name = row[2]
                if dept_name == "":
                    dept_name = "No Department"
                else:
                    deptfile = 'app/assets/city_depts.csv'
                    csv_depts = pd.read_csv(deptfile)
                    if (csv_depts['Original Department Name'].str.contains(dept_name).any() or csv_depts['New Department Name'].str.contains(dept_name).any()):
                        numrows = csv_depts.shape[0]
                        for x in range(numrows):
                            if (csv_depts['Original Department Name'][x] == dept_name or csv_depts['New Department Name'][x] == dept_name):
                                dept_name = csv_depts['New Department Name'][x]
                    else:
                        dept_name = "No Department"
                if ContrType.query.filter_by(contract_structure_type=row[4]).first() is None:
                    c_type = ContrType(contract_structure_type=row[4])
                    db.session.add(c_type)
                # three profit status cases: for profit, non profit, unknown (else)
                if row[14] == 'For Profit':
                    profstat = Profit_Status.For_Profit
                elif row[14] == 'Non Profit':
                    profstat = Profit_Status.Non_Profit
                else:
                    profstat = Profit_Status.Unknown
                amount = 0
                total_payments = 0
                try:
                    amount = float(row[9].replace(',',''))
                except Exception:
                    amount = 0
                try:
                    total_payments = float(row[10].replace(',',''))
                except Exception:
                    total_payments = 0
                contract = ProfServ(
                    # hash logic: original contract id - current item id - start date
                    id=row[0] + '-' + row[1] + '-' + row[6],
                    original_contract_id=row[0],
                    current_item_id=row[1],
                    department_name=dept_name,
                    vendor=row[3],
                    contract_structure_type=row[4],
                    short_desc=row[5],
                    start_dt=datetime.strptime(row[6], '%m/%d/%Y').date(),
                    end_dt=datetime.strptime(row[7], '%m/%d/%Y').date(),
                    days_remaining=int(row[8]),
                    amt=amount,
                    tot_payments=total_payments,
                    orig_vendor=row[11],
                    exempt_status=row[12],
                    adv_or_exempt=row[13],
                    profit_status=profstat,
                    as_of=quarter_year,
                    timestamp=now
                )
                # try/except statement for detecting duplicates, i.e. db finds primary key collision
                try:
                    db.session.add(contract)
                    db.session.commit()
                except exc.IntegrityError:
                    found_duplicate = True

                    db.session.rollback()
                    conflict_id = row[0] + '-' + row[1] + '-' + row[6]
                    orig_contract = ProfServ.query.filter_by(id=conflict_id).first()
                    orig_days_remaining = orig_contract.days_remaining
                    dupl_days_remaining = int(row[8])

                    # if days_remaining of the duplicate contract has less days remaining,
                    # update the following entries: days remaining, amount, time stamp
                    if dupl_days_remaining < orig_days_remaining:
                        orig_contract.days_remaining = contract.days_remaining
                        orig_contract.amt = contract.amt
                        orig_contract.timestamp = contract.timestamp

                    db.session.commit()
            except Exception:
                found_broken_row = True
                db.session.rollback()

    # return three logic variables for upload alert
    return (upload_successful, found_duplicate, found_broken_row)
