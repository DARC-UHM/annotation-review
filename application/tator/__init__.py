from flask import Blueprint

tator_bp = Blueprint('tator', __name__)

from . import routes
