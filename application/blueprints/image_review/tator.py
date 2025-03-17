"""
Tator-specific image review endpoint.
"""

import tator
import requests
from flask import Blueprint, current_app, flash, render_template, redirect, request, session

from application.server.tator_localization_processor import TatorLocalizationProcessor

tator_image_review_bp = Blueprint('tator_image_review', __name__)


# view all Tator annotations (localizations) in a specified project & section
@tator_image_review_bp.get('/image-review/tator')
def tator_image_review():
    if 'tator_token' not in session.keys():
        return redirect('/')
    if not request.args.get('project') or not request.args.get('section') or not request.args.get('deployment'):
        flash('Please select a project, section, and deployment', 'info')
        return redirect('/')
    project_id = int(request.args.get('project'))
    section_id = int(request.args.get('section'))
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        localization_processor = TatorLocalizationProcessor(
            project_id=project_id,
            section_id=section_id,
            api=api,
            deployment_list=request.args.getlist('deployment'),
            tator_url=current_app.config.get('TATOR_URL'),
        )
        localization_processor.fetch_localizations()
        localization_processor.load_phylogeny()
        localization_processor.process_records()
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    comments = {}
    deployments = request.args.getlist('deployment')
    # get comments from external review db
    try:
        for deployment in deployments:
            with requests.get(
                    url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment.replace("-", "_")}',
                    headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            ) as res:
                comments = comments | res.json()  # merge dicts
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    data = {
        'annotations': localization_processor.final_records,
        'title': localization_processor.section_name,
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
    }
    return render_template('image-review/image-review.html', data=data)
