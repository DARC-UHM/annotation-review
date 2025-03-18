from flask import Blueprint

tator_qaqc_bp = Blueprint('tator_qaqc', __name__, template_folder='templates/tator')

from . import routes
