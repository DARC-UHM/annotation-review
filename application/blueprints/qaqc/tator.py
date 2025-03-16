from flask import Blueprint, request, session, render_template, redirect, flash
import tator
import requests
from application.server.tator_qaqc_processor import TatorQaqcProcessor

tator_qaqc_bp = Blueprint('tator_qaqc', __name__)

@tator_qaqc_bp.route('/tator/qaqc-checklist/<project_id>/<section_id>', methods=['GET'])
def tator_qaqc_checklist(project_id, section_id):
    # Your existing tator qaqc checklist route code
    pass

# Add other Tator QAQC routes here
