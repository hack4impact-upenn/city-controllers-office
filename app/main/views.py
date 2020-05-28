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
    CSVDownloadSCForm
)

import io
import csv
from datetime import datetime

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method=='POST':
        return download_database()
    database_csv_form = CSVDownloadDBForm()
    return render_template('main/index.html', database_csv_form=database_csv_form)


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)

# Route to search page, where users can search for city contracts
@main.route('/search', methods=['GET', 'POST'])
def search():
    form = ResultsForm()
    depts = Department.query.all()
    types = ContrType.query.all()
    if form.validate():
        filtered = ProfServ.query.filter_by(vendor=form.vendor_name.data, original_contract_id=form.contract_number.data)
        return render_template('main/results.html', filtered = filtered) #may change to redirect url_for
    return render_template('main/search.html', depts = depts, types = types, form = form)

# Route to results page, where results of city contracts searching appear
@main.route('/results', methods=['GET', 'POST'])
def results():
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
