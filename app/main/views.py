from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    request,
    make_response,
    jsonify
)
from app.models import (
    EditableHTML,
    Department,
    ContrType,
    ProfServ,
    Profit_Status
)
from app.main.forms import (
    ResultsForm,
    CSVDownloadDBForm,
    CSVDownloadRSForm,
    SortByAmountHiLoForm,
    SortByAmountLoHiForm,
    SortByABC,
    SortByCBA
)
import io
import csv
from datetime import datetime
from app import db
from sqlalchemy import or_

import json
import io
import csv
from datetime import datetime

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)

# Route to search page, where users can search for city contracts
@main.route('/search', methods=['GET', 'POST'])
def search():
    database_csv_form = CSVDownloadDBForm()
    form = ResultsForm()
    depts = Department.query.all()
    types = ContrType.query.all()
    form.department.choices = [(dept.department_name, dept.department_name) for dept in depts]
    form.contract_type.choices = [(type.contract_structure_type, type.contract_structure_type) for type in types]
    if request.method == 'POST':
        if database_csv_form.database_csv_submit.data and database_csv_form.validate():
            return download_database()
    if form.validate():
        return redirect(url_for('main.results', vendor=form.vendor.data, num=form.original_contract_id.data, sd=form.start_dt.data, ed=form.end_dt.data, min=form.minimum.data, max=form.maximum.data, kw=form.keyword.data, fp=form.for_profit.data, np=form.non_profit.data, adv=form.adv.data, ex=form.ex.data))
    return render_template('main/search.html', depts=depts, types=types, form=form, database_csv_form=database_csv_form)


def modelListToJson(filtered):
    filtered_json = []

    # convert filtered into [json]
    for entry in filtered:
        entry_json = dict()
        entry_json['vendor'] = entry.vendor
        entry_json['original_contract_id'] = entry.original_contract_id
        entry_json['contract_structure_type'] = entry.contract_structure_type
        entry_json['department_name'] = entry.department_name
        entry_json['amt'] = entry.amt
        entry_json['tot_payments'] = entry.tot_payments
        entry_json['days_remaining'] = entry.days_remaining
        entry_json['start_dt'] = str(entry.start_dt)
        entry_json['end_dt'] = str(entry.end_dt)
        entry_json['short_desc'] = entry.short_desc
        entry_json['profit_status'] = str(entry.profit_status)

        filtered_json.append(entry_json)

    return json.dumps(filtered_json)


# Route to results page, where results of city contracts searching appear
@main.route('/results', methods=['GET', 'POST'])
def results():
    results_csv_form = CSVDownloadRSForm()
    high_to_low_form = SortByAmountHiLoForm()
    low_to_high_form = SortByAmountLoHiForm()
    abc = SortByABC()
    cba = SortByCBA()
    vendor = request.args.get('vendor')
    num = request.args.get('num')
    sd = request.args.get('sd')
    ed = request.args.get('ed')
    min = request.args.get('min')
    max = request.args.get('max')
    kw = request.args.get('kw')
    fp = request.args.get('fp')
    np = request.args.get('np')
    adv = request.args.get('adv')
    ex = request.args.get('ex')
    query = ProfServ.query
    if vendor:
        query = query.filter(ProfServ.vendor.ilike('%{0}%'.format(vendor)))
    if num:
        query = query.filter(ProfServ.original_contract_id == num)
    if sd:
        query = query.filter(ProfServ.start_dt >= sd)
    if ed:
        query = query.filter(ProfServ.end_dt <= ed)
    if str(min) != "":
        try:
            query = query.filter(ProfServ.amt >= min)
        except:
            pass
    if str(max) != "":
        try:
            query = query.filter(ProfServ.amt <= max)
        except:
            pass
    if kw:
        query = query.filter((ProfServ.vendor.ilike('%{0}%'.format(kw))) | (ProfServ.department_name.ilike(kw)) | (
            ProfServ.contract_structure_type.ilike(kw)) | (ProfServ.adv_or_exempt.ilike(kw)) | (ProfServ.short_desc.ilike('%{0}%'.format(kw))))

    if str(fp) == "False":
        query = query.filter(ProfServ.profit_status !=
                             Profit_Status.For_Profit)
    if str(np) == "False":
        query = query.filter(ProfServ.profit_status !=
                             Profit_Status.Non_Profit)
    if str(adv) == "False":
        query = query.filter(ProfServ.adv_or_exempt != "ADVERTISED")
    if str(ex) == "False":
        query = query.filter(ProfServ.adv_or_exempt != "EXEMPT")
    filtered = query.all()
    print(filtered[0])
    if request.method == 'POST':
        if results_csv_form and results_csv_form.results_csv_submit.data and results_csv_form.validate():
            return download_results(filtered)
        if high_to_low_form and high_to_low_form.amount_hi_lo_submit.data and high_to_low_form.validate():
            ordered = query.order_by(ProfServ.amt.desc()).all()
            return render_template('main/results.html', filtered=ordered, results_csv_form=results_csv_form, high_to_low_form=high_to_low_form, low_to_high_form=low_to_high_form, abc=abc, cba=cba)
        if low_to_high_form and low_to_high_form.amount_lo_hi_submit.data and low_to_high_form.validate():
            ordered = query.order_by(ProfServ.amt.asc()).all()
            return render_template('main/results.html', filtered=ordered, results_csv_form=results_csv_form, high_to_low_form=high_to_low_form, low_to_high_form=low_to_high_form, abc=abc, cba=cba)
        if abc and abc.name_abc.data and abc.validate():
            ordered = query.order_by(ProfServ.vendor.asc()).all()
            return render_template('main/results.html', filtered=ordered, results_csv_form=results_csv_form, high_to_low_form=high_to_low_form, low_to_high_form=low_to_high_form, abc=abc, cba=cba)
        if cba and cba.name_cba.data and cba.validate():
            ordered = query.order_by(ProfServ.vendor.desc()).all()
            return render_template('main/results.html', filtered=ordered, results_csv_form=results_csv_form, high_to_low_form=high_to_low_form, low_to_high_form=low_to_high_form, abc=abc, cba=cba)
    if filtered:
        return render_template('main/results.html', filtered=filtered, filtered_json=modelListToJson(filtered), results_csv_form=results_csv_form, high_to_low_form=high_to_low_form, low_to_high_form=low_to_high_form, abc=abc, cba=cba)
    else:
        return render_template('main/results.html', filtered=[], results_csv_form=results_csv_form, high_to_low_form=high_to_low_form, low_to_high_form=low_to_high_form, abc=abc, cba=cba)

# Route to contact page, where users can contact City Controller's Office
@main.route('/contact')
def contact():
    return render_template('main/contact.html')

# Route to tips page, where users can find search tips
@main.route('/tips')
def tips():
    return render_template('main/tips.html')

# Route to report page, where users can report page
@main.route('/report')
def report():
    return render_template('main/report.html')

# Function to download csv of database
@main.route('/download-database', methods=['GET', 'POST'])
def download_database():
    # make csv file and writer variables
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file)
    filename = 'contracts' + datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'

    # write data from contracts db to csv
    prof_servs = ProfServ.query.all()

    csv_writer.writerow([
        'Original Contract ID',
        'Current Item ID',
        'Department Name',
        'Vendor',
        'Contract Structure Type',
        'Short Description',
        'Start Date',
        'End Date',
        'Days Remaining',
        'Amount',  # Should specify the denomination
        'Total Payments',
        'Original Vendor',
        'Exempt Status',
        'Advertised or Exempt',
        'As Of',
        'Profit or Nonprofit'
    ])

    if prof_servs:
        for ps in prof_servs:
            csv_writer.writerow([
                ps.original_contract_id,
                ps.current_item_id,
                ps.department_name,
                ps.vendor,
                ps.contract_structure_type,
                ps.short_desc,
                ps.start_dt,
                ps.end_dt,
                ps.days_remaining,
                ps.amt,
                ps.tot_payments,
                ps.orig_vendor,
                ps.exempt_status,
                ps.adv_or_exempt,
                ps.as_of,
                ps.profit_status
            ])

    # prepare file bytes for download
    csv_bytes = io.BytesIO()
    csv_bytes.write(csv_file.getvalue().encode('utf-8'))
    csv_bytes.seek(0)

    # send file for download
    return send_file(csv_bytes, as_attachment=True, attachment_filename=filename, mimetype='text/csv')

# Function to download csv of results
@main.route('/download-results', methods=['GET', 'POST'])
def download_results(filtered):

    # make csv file and writer variables
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file)
    filename = 'results' + datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'

    # write data from results to csv
    csv_writer.writerow([
        'Original Contract ID',
        'Current Item ID',
        'Department Name',
        'Vendor',
        'Contract Structure Type',
        'Short Description',
        'Start Date',
        'End Date',
        'Days Remaining',
        'Amount',  # Should specify the denomination
        'Total Payments',
        'Original Vendor',
        'Exempt Status',
        'Advertised or Exempt',
        'As Of',
        'Profit or Nonprofit'
    ])

    if filtered:
        for rs in filtered:
            print(rs)
            csv_writer.writerow([
                rs.original_contract_id,
                rs.current_item_id,
                rs.department_name,
                rs.vendor,
                rs.contract_structure_type,
                rs.short_desc,
                rs.start_dt,
                rs.end_dt,
                rs.days_remaining,
                rs.amt,
                rs.tot_payments,
                rs.orig_vendor,
                rs.exempt_status,
                rs.adv_or_exempt,
                rs.as_of,
                rs.profit_status
            ])

    # prepare file bytes for download
    csv_bytes = io.BytesIO()
    csv_bytes.write(csv_file.getvalue().encode('utf-8'))
    csv_bytes.seek(0)

    # send file for download
    return send_file(csv_bytes, as_attachment=True, attachment_filename=filename, mimetype='text/csv')
