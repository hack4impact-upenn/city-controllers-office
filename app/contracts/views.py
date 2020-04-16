from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_rq import get_queue

from app import db
from app.models import ProfServ

contact = Blueprint('account', __name__)
