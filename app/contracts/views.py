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

from app import db
from app.models import ProfServ, Profit_Status, Exempt_Status, Department, ContrType

contract = Blueprint('ProfServ', __name__)
deptnames = Blueprint('Department', __name__)
typenames = Blueprint('ContrType', __name__)


@contract.route('/search')
def readCSV(filename):
    dept_names = []
    contr_type_names = []
    now=datetime.now()
    with open(filename) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        next(csvReader)
        for row in csvReader:
            if row[0] == '':
                continue
            # if int(row[12]) == 102:
            #    exstat = Exempt_Status.EXEMPT
            #    advext = Exempt_Status.EXEMPT
            # else:
            #    exstat = Exempt_Status.ADVERTISED
            #    advext = Exempt_Status.ADVERTISED
            if Department.query.filter_by(department_name=row[2]).first() is None:
                dept = Department(department_name=row[2])
                db.session.add(dept)
            if ContrType.query.filter_by(contract_structure_type=row[4]).first() is None:
                type = ContrType(contract_structure_type=row[4])
                db.session.add(type)
            if row[14] == 'For Profit':
                profstat = Profit_Status.For_Profit
            else:
                profstat = Profit_Status.Non_Profit
            contract = ProfServ(
                # id=row[0] + row[1] + row[6] + str(now),
                # hash logic: original contract id - current item id - start date
                id=row[0] + '-' + row[1] + '-' + row[6],
                original_contract_id=row[0],
                current_item_id=row[1],
                department_name=row[2],
                vendor=row[3],
                contract_structure_type=row[4],
                short_desc=row[5],
                start_dt=datetime.strptime(row[6], '%m/%d/%Y').date(),
                end_dt=datetime.strptime(row[7], '%m/%d/%Y').date(),
                days_remaining=int(row[8]),
                amt=float(row[9]),
                tot_payments=float(row[10]),
                orig_vendor=row[11],
                exempt_status=row[12],
                adv_or_exempt=row[13],
                profit_status=profstat,
                timestamp=now
            )
            try:
                db.session.add(contract)
                db.session.commit()
            except exc.IntegrityError:
                db.session.rollback()
                conflict_id = row[0] + '-' + row[1] + '-' + row[6]
                orig_contract = ProfServ.query.filter_by(id=conflict_id).first()
                orig_days_remaining = orig_contract.days_remaining
                dupl_days_remaining = int(row[8])

                # if days_remaining of the duplicate contract has less days remaining,
                # update ALL entries of original contract
                if dupl_days_remaining < orig_days_remaining:
                    orig_contract.department_name = contract.department_name
                    orig_contract.vendor = contract.vendor
                    orig_contract.contract_structure_type = contract.contract_structure_type
                    orig_contract.short_desc = contract.short_desc
                    orig_contract.end_dt = contract.end_dt
                    orig_contract.days_remaining = contract.days_remaining
                    orig_contract.amt = contract.amt
                    orig_contract.tot_payments = contract.tot_payments
                    orig_contract.orig_vendor = contract.orig_vendor
                    orig_contract.exempt_status = contract.exempt_status
                    orig_contract.adv_or_exempt = contract.adv_or_exempt
                    orig_contract.profit_status = contract.profit_status
                    orig_contract.timestamp = contract.timestamp

                db.session.commit()
                print (orig_contract.days_remaining)
                
                print (dupl_days_remaining)
