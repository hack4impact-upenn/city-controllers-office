from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import (
    PasswordField,
    StringField,
    SubmitField,
    SelectField,
    BooleanField
)
from wtforms.fields.html5 import EmailField
from wtforms.validators import (
    Email,
    EqualTo,
    InputRequired,
    Length,
)

from app import db
from app.models import Role, User


class ChangeUserEmailForm(FlaskForm):
    email = EmailField(
        'New email', validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangeAccountTypeForm(FlaskForm):
    role = QuerySelectField(
        'New account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).filter_by(id=2))
    submit = SubmitField('Update role')


class InviteUserForm(FlaskForm):
    role = QuerySelectField(
        'Account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory = lambda: db.session.query(Role).filter_by(name='Administrator'))
    first_name = StringField(
        'First name', validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(),
                                 Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')

class CSVUploadForm(FlaskForm):
    quarter_select = SelectField("Quarter", choices = [('1', 'Q1'), ('2', 'Q2'), ('3', 'Q3'), ('4', 'Q4')])
    year_select = StringField("Year", validators=[InputRequired(), Length(1, 64)])
    document = FileField('Document', validators=[FileRequired(), FileAllowed(['csv'], 'CSV Document only!')])

class CSVDownloadForm(FlaskForm):
    download_csv = SubmitField("Download CSV")

class DeleteSelectedForm(FlaskForm):
    deleteSelected = SubmitField("Delete Selected")

class SortMLRForm(FlaskForm):
    sortMLR = SubmitField("Sort Most to Least Recent")

class SortLMRForm(FlaskForm):
    sortLMR = SubmitField("Sort Least to Most Recent")

class AddDeptNameForm(FlaskForm):
    newdn = StringField("New Department Name")
    adddn = SubmitField("Add Department Name")

class AddContrTypeForm(FlaskForm):
    newct = StringField("New Contract Type")
    addct = SubmitField("Add Contract Type")
