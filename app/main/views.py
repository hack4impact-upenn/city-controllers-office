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
    ProfServ
)
from app.main.forms import (
    ResultsForm,
    CSVDownloadDBForm,
    CSVDownloadRSForm
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
    results_csv_form = CSVDownloadRSForm()
    form = ResultsForm()
    depts = Department.query.all()
    types = ContrType.query.all()
    if request.method == 'POST':
        if database_csv_form.database_csv_submit.data and database_csv_form.validate():
            return download_database()
    if form.validate():
        query = ProfServ.query
        if form.vendor.data:
            query = query.filter(ProfServ.vendor == form.vendor.data)
        if form.original_contract_id.data:
            query = query.filter(
                ProfServ.original_contract_id == form.original_contract_id.data)
        if form.start_dt.data:
            query = query.filter(ProfServ.start_dt >= form.start_dt.data)
        if form.end_dt.data:
            query = query.filter(ProfServ.end_dt <= form.end_dt.data)
        if str(form.minimum.data) != "":
            try:
                query = query.filter(ProfServ.amt >= form.minimum.data)
            except:
                pass
        if str(form.maximum.data) != "":
            try:
                query = query.filter(ProfServ.amt <= form.maximum.data)
            except:
                pass
        filtered = query.all()
        return redirect("/results")
        # return render_template('main/results.html', filtered=filtered, results_csv_form=results_csv_form, filtered_len=len(filtered))
    return render_template('main/search.html', depts=depts, types=types, form=form, database_csv_form=database_csv_form)


global_filter = []

# pagenation loading route
@main.route('/load')
def load():
    if request.args:
        counter = int(request.args.get('c'))
        # the filtering function happens here
        filtered = ProfServ.query.all()
        num_entries = len(filtered)
        num_per_page = 20

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
            entry_json['start_dt'] = entry.start_dt
            entry_json['end_dt'] = entry.end_dt
            entry_json['short_desc'] = entry.short_desc

            filtered_json.append(entry_json)

        if counter == 0:
            res = make_response(jsonify(filtered_json[0: num_per_page]), 200)
        elif counter == num_entries:
            res = make_response(jsonify({}), 200)
        else:
            res = make_response(
                jsonify(filtered_json[counter: counter + num_per_page]), 200)

        return res


# Route to results page, where results of city contracts searching appear
@main.route('/results', methods=['GET', 'POST'])
def results():
    # for testing only, CHANGE THIS TO ACTUAL QUERY / FILTER
    results_csv_form = CSVDownloadRSForm()
    filtered = ProfServ.query.all()

    # use list as an error code => no form is passed in
    if request.method == 'POST':
        if results_csv_form and results_csv_form.results_csv_submit.data and results_csv_form.validate():
            return download_results(filtered)
    if filtered and results_csv_form:
        # set the filter here for the load function
        global global_filter
        global_filter = filtered
        return render_template('main/results.html', filtered=filtered, results_csv_form=results_csv_form)
    else:
        return render_template('main/results.html')

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
                rs.profit_status
            ])

    # prepare file bytes for download
    csv_bytes = io.BytesIO()
    csv_bytes.write(csv_file.getvalue().encode('utf-8'))
    csv_bytes.seek(0)

    # send file for download
    return send_file(csv_bytes, as_attachment=True, attachment_filename=filename, mimetype='text/csv')
