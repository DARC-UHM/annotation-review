from flask import Blueprint

external_review_bp = Blueprint('external_review', __name__)

from . import routes
