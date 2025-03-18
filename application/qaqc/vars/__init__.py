from flask import Blueprint

vars_qaqc_bp = Blueprint('vars_qaqc', __name__, template_folder='templates/vars')

from . import routes
