from flask import Blueprint

vars_qaqc_bp = Blueprint(
    'vars_qaqc', __name__,
    template_folder='templates',
    static_folder='static',
)

from . import routes
