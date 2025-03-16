from flask import Blueprint, request, session, render_template, redirect, flash
import tator
import requests
from application.server.tator_localization_processor import TatorLocalizationProcessor

tator_image_review_bp = Blueprint('tator_image_review', __name__)

@tator_image_review_bp.route('/tator/image-review/<project_id>/<section_id>', methods=['GET'])
def tator_image_review(project_id, section_id):
    # Your existing tator image review route code
    pass

# Add other Tator image review routes here
