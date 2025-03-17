from flask import Blueprint

vars_bp = Blueprint('vars', __name__)
tator_bp = Blueprint('tator', __name__)

from . import tator, vars
