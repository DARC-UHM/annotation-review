from flask import Blueprint

qaqc_bp = Blueprint('qaqc', __name__)

from . import tator, vars
