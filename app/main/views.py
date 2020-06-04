from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    request
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
            query = query.filter(ProfServ.vendor.ilike('%{0}%'.format(form.vendor.data)))
        if form.original_contract_id.data:
            query = query.filter(ProfServ.original_contract_id.ilike('%{0}%'.format(form.original_contract_id.data)))
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
        print(len(filtered))
        #results(filtered, results_csv_form)
        print(len(filtered))
        return render_template('main/results.html', filtered = filtered, results_csv_form=results_csv_form) #may change to redirect url_for
    return render_template('main/search.html', depts = depts, types = types, form = form, database_csv_form=database_csv_form)


# Route to results page, where results of city contracts searching appear
@main.route('/results', methods=['GET', 'POST'])
def results(filtered=None, results_csv_form=None):
    # use list as an error code => no form is passed in
    if request.method == 'POST':
        filtered_data = filtered
        if results_csv_form and results_csv_form.results_csv_submit.data and results_csv_form.validate():
            print(len(filtered_data))
            return download_results(filtered_data)
    if filtered and results_csv_form:
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
@main.route('/download-database', methods = ['GET', 'POST'])
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
        'Amount', # Should specify the denomination
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
@main.route('/download-results', methods = ['GET', 'POST'])
def download_results(filtered=None):

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
        'Amount', # Should specify the denomination
        'Total Payments',
        'Original Vendor',
        'Exempt Status',
        'Advertised or Exempt',
        'Profit or Nonprofit'
    ])

    if filtered:
        for rs in filtered:
            print (rs)
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
