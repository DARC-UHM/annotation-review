from flask import Blueprint

vars_bp = Blueprint('vars', __name__)

from . import routes
