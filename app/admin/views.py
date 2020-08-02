from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    send_file,
)
import boto3
from flask_login import current_user, login_required
from flask_rq import get_queue
from werkzeug import secure_filename
import sqlalchemy
from app import db
from app.admin.forms import (
    ChangeAccountTypeForm,
    ChangeUserEmailForm,
    InviteUserForm,
    NewUserForm,
    CSVUploadForm,
    CSVDownloadForm,
    DeleteSelectedForm,
    SortMLRForm,
    SortLMRForm,
    AddDeptNameForm,
    AddContrTypeForm
)
from app.decorators import admin_required
from app.email import send_email
from app.models import EditableHTML, Role, User, ProfServ, Department, ContrType
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import SubmitField
import os
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Email
import calendar
import time
import io
import csv
from datetime import datetime
from ..contracts.views import readCSV

admin = Blueprint('admin', __name__)


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'admin/registered_users.html', users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'.format(
            user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<int:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash('Role for user {} successfully changed to {}.'.format(
            user.full_name(), user.role.name), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))



@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200


@admin.route('/upload-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_csv():
    form = CSVUploadForm()
    upload_status = 'No Upload'
    found_duplicate = False
    found_broken_row = False

    # upload_dir = "uploads"
    # time_stamp = calendar.timegm(time.gmtime())
    # prepending time stamp
    #filename = str(time_stamp) + '_' + secure_filename(f.filename)
    # # filepath
    # filepath = os.path.join(upload_dir, filename)
    # f.save(filepath)

    if form.validate_on_submit():
        file = form.document.data
        # process quarter and year
        # example: quarter 1 and year 2002 => quarter_year = "Q1-2002"
        # default: "-"
        quarter = form.quarter_select.data
        year = form.year_select.data
        quarter_year = "Q" + quarter + "-" + year

        # uploads csv file; returns upload alert logic variables
        upload_successful, found_duplicate, found_broken_row = readCSV(file=file, quarter_year=quarter_year)
        upload_status = 'Success' if upload_successful else 'Failed'

    return render_template('admin/upload_csv.html', form=form, upload_status=upload_status,
                           found_duplicate=found_duplicate, found_broken_row=found_broken_row)


@admin.route('/download-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def download_csv():
    download_csv_form = CSVDownloadForm()

    if request.method == 'POST':
        # make csv file and writer variables
        csv_file = io.StringIO()
        csv_writer = csv.writer(csv_file)
        filename = 'contracts' + datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'

        # write data from contracts db to csv
        prof_servs = ProfServ.query.all()

        csv_writer.writerow([
            'Contract ID',
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
            'Profit or Nonprofit',
            'As Of',
            "Timestamp"
        ])
        for ps in prof_servs:
            csv_writer.writerow([
                ps.id,
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
                ps.profit_status,
                ps.as_of,
                ps.timestamp
            ])

        # prepare file bytes for download
        csv_bytes = io.BytesIO()
        csv_bytes.write(csv_file.getvalue().encode('utf-8'))
        csv_bytes.seek(0)

        # send file for download
        return send_file(csv_bytes, as_attachment=True, attachment_filename=filename, mimetype='text/csv')

    return render_template('admin/download_csv.html', download_csv_form=download_csv_form)


@admin.route('/manage_department_names', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_department_names():
    name_list = Department.query.all()
    adddnform = AddDeptNameForm()
    dsdnForm = DeleteSelectedForm()
    adddnSuccessful = False
    if request.method == "POST":
        try:
            if adddnform.validate_on_submit():
                deptname = Department(department_name = adddnform.newdn.data)
                db.session.add(deptname)
                db.session.commit()
                adddnSuccessful = True
        except sqlalchemy.exc.SQLAlchemyError as e:
            db.session.rollback()
    return render_template('admin/manage_department_names.html', name_list=name_list, adddnform=adddnform, adddnSuccessful=adddnSuccessful, dsdnForm=dsdnForm)

@admin.route('/delete_selected_dn', methods=['POST'])
@login_required
@admin_required
def delete_selected_dn():
    if request.method == "POST":
        data = request.get_data()
        data_parsed = str(data.decode("utf-8")[44:-4])
        print(data)
        Department.query.filter(Department.department_name == data_parsed).delete()
        db.session.commit()

    return ("Success")

@admin.route('/manage_contract_types', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_contract_types():
    type_list =  ContrType.query.all()
    addctform = AddContrTypeForm()
    addctSuccessful = False
    dsctForm = DeleteSelectedForm()
    if request.method == "POST":
        try:
            if addctform.validate_on_submit():
                contracttype = ContrType(contract_structure_type = addctform.newct.data)
                db.session.add(contracttype)
                db.session.commit()
                addctSuccessful = True
        except sqlalchemy.exc.SQLAlchemyError as e:
            db.session.rollback()
    return render_template('admin/manage_contract_types.html', type_list=type_list, addctform=addctform, addctSuccessful=addctSuccessful, dsctForm=dsctForm)

@admin.route('/delete_selected_ct', methods=['POST'])
@login_required
@admin_required
def delete_selected_ct():
    if request.method == "POST":
        data = request.get_data()
        data_parsed = str(data.decode("utf-8")[60:-4])
        ContrType.query.filter(ContrType.contract_structure_type == data_parsed).delete()
        db.session.commit()

    return ("Success")

@admin.route('/delete-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_csv():
    # create forms for each button
    dsForm = DeleteSelectedForm()
    smlrForm = SortMLRForm() # reverse chronological
    slmrForm = SortLMRForm() # chronological

    # query profserv db for list of unique timestamps
    query = db.session.query(ProfServ.timestamp.distinct().label("timestamp"))
    timestamp_list = [str(row.timestamp) for row in query.all()]
    timestamp_list.sort()

    # calculate deleteSuccessful and sortChron booleans based on which forms have been submitted
    deleteSuccessful = False
    sortChron = False
    if request.method == "POST":
        if smlrForm.validate_on_submit() and "smlrButton" in str(request.form):
            sortChron = False
        if slmrForm.validate_on_submit() and "slmrButton" in str(request.form):
            sortChron = True
        if dsForm.validate_on_submit() and "deleteSelectedButton" in str(request.form):
            deleteSuccessful = True

    # reverse if most->least recent button is pressed
    if not sortChron:
        timestamp_list.reverse()

    return render_template('admin/delete_csv.html', \
                                timestamp_list=timestamp_list, \
                                sortChron=sortChron, \
                                deleteSuccessful=deleteSuccessful, \
                                smlrForm=smlrForm,
                                slmrForm=slmrForm,
                                dsForm=dsForm)

@admin.route('/delete_selected', methods=['POST'])
@login_required
@admin_required
def delete_selected():
    if request.method == "POST":
        data = request.get_data()
        timestamp_to_delete = str(data.decode("utf-8")[14:-2]) # Note: sensitive to name of button
        ProfServ.query.filter(ProfServ.timestamp == timestamp_to_delete).delete()
        db.session.commit()

    return ("Success")

@admin.route('/sign-s3/')
@admin_required
@login_required
def sign_s3():
    # Load necessary information into the application
    TARGET_FOLDER = 'json/'
    S3_REGION = 'us-east-2'
    S3_BUCKET = os.environ.get('S3_BUCKET')

    # Load required data from the request
    pre_file_name = request.args.get('file-name')
    file_name = ''.join(pre_file_name.split('.')[:-1]) + \
                str(time.time()).replace('.',  '-') + '.' + \
                ''.join(pre_file_name.split('.')[-1:])
    file_type = request.args.get('file-type')

    # Initialise the S3 client
    s3 = boto3.client('s3',
                      region_name=S3_REGION,
                      aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                      )

    # Generate and return the presigned URL
    presigned_post = s3.generate_presigned_post(
        Bucket=S3_BUCKET,
        Key=TARGET_FOLDER + file_name,
        Fields={
            "acl": "public-read",
            "Content-Type": file_type
        },
        Conditions=[{
            "acl": "public-read"
        }, {
            "Content-Type": file_type
        }],
        ExpiresIn=60000)

    # Return the data to the client
    return json.dumps({
        'data':
            presigned_post,
        'url_upload':
            'https://%s.%s.%s.amazonaws.com' % (S3_BUCKET, 's3', S3_REGION),
        'url':
            'https://%s.%s.%s.amazonaws.com/json/%s' % (S3_BUCKET, 's3', S3_REGION, file_name)
    })
