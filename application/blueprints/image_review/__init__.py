from flask import Blueprint

image_review_bp = Blueprint('image_review', __name__)

from . import external_review, tator, vars
