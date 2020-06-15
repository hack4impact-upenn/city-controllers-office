from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    send_file
)
from flask_login import current_user, login_required
from flask_rq import get_queue
from werkzeug import secure_filename

from app import db
from app.admin.forms import (
    ChangeAccountTypeForm,
    ChangeUserEmailForm,
    InviteUserForm,
    NewUserForm,
    CSVUploadForm,
    CSVDownloadForm,
)
from app.decorators import admin_required
from app.email import send_email
from app.models import EditableHTML, Role, User, ProfServ
from flask_wtf import FlaskForm
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

@admin.route('/upload-csv', methods = ['GET', 'POST'])
@login_required
@admin_required
def upload_csv():
    form = CSVUploadForm()
    upload_successful = False
    found_duplicate = False
    found_broken_row = False
    
    if form.validate_on_submit():
        upload_dir = "uploads"
        f = form.document.data
        time_stamp = calendar.timegm(time.gmtime())
        # prepending time stamp
        filename = str(time_stamp) + '_' + secure_filename(f.filename)
        # filepath
        filepath = os.path.join(upload_dir, filename)
        f.save(filepath)
        # process quarter and year
        # example: quarter 1 and year 2002 => quarter_year = "Q1-2002"
        # default: "-"
        quarter = form.quarter_select.data
        year = form.year_select.data
        quarter_year = "Q" + quarter + "-" + year

        # uploads csv file; returns upload alert logic variables
        upload_successful, found_duplicate, found_broken_row = readCSV(filename=filepath, quarter_year=quarter_year)

    return render_template('admin/upload_csv.html', form=form, upload_successful=upload_successful, \
        found_duplicate=found_duplicate, found_broken_row=found_broken_row)

@admin.route('/download-csv', methods = ['GET', 'POST'])
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
            'Amount', # Should specify the denomination
            'Total Payments',
            'Original Vendor',
            'Exempt Status',
            'Advertised or Exempt',
            'Profit or Nonprofit',
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
                ps.timestamp
            ])

        # prepare file bytes for download
        csv_bytes = io.BytesIO()
        csv_bytes.write(csv_file.getvalue().encode('utf-8'))
        csv_bytes.seek(0)

        # send file for download
        return send_file(csv_bytes, as_attachment=True, attachment_filename=filename, mimetype='text/csv')

    return render_template('admin/download_csv.html', download_csv_form=download_csv_form)

@admin.route('/view_database', methods = ['GET', 'POST'])
@login_required
@admin_required
def view_database():
    return render_template('admin/view_database.html')