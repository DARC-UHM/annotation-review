from flask import Blueprint

vars_image_review_bp = Blueprint('vars_image_review', __name__)

from . import routes
