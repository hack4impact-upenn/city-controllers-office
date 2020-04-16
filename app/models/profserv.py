from flask import current_app
from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db, login_manager

class Exempt_Status(enum.Enum):
    EXEMPT = 102
    ADVERTISED = 1

    def __str__(self):
        return self.name

    def __html__(self): 
        return self.value

class Profit_Status(enum.Enum):
    For_Profit = "For Profit"
    Non_Profit = "Non Profit"

    def __str__(self):
        return self.name

    def __html__(self):
        return self.value

class ProfServ(db.Model):
    __tablename__ = 'prof_serv'
    original_contract_id = db.Column(db.String(64), primary_key=True)
    current_item_id = db.Column(db.String(64))
    department_name = db.Column(db.String(64))
    vendor = db.Column(db.String(64))
    contract_structure_type = db.Column(db.String(64))
    short_desc = db.Column(db.String(64))
    start_dt = db.Column(db.Date)
    end_dt = db.Column(db.Date)
    days_remaining = db.Column(db.Integer)
    amt = db.Column(db.Double)
    tot_payments = db.Column(db.Double)
    orig_vendor = db.Column(db.String(64))
    exempt_status = db.Column(db.Enum(Exempt_Status), default=0)
    adv_or_exempt = db.Column(db.Enum(Profit_Status), default=0)

    def __repr__(self):
       return ('<Professional Services Contract \n'
             f'original contract id: {self.original_contract_id}\n')


    def __str__(self):
      return self.__repr__()
