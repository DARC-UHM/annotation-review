"""
Tator-specific image review endpoint.

/image-review/tator [GET]
"""
import json

import tator
import requests
from flask import current_app, flash, render_template, redirect, request, session

from . import tator_image_review_bp
from application.image_review.tator.tator_localization_processor import TatorLocalizationProcessor


# view all Tator annotations (localizations) in a specified project & section
@tator_image_review_bp.get('')
def tator_image_review():
    if 'tator_token' not in session.keys():
        return redirect('/')
    if not request.args.get('project') or not request.args.getlist('section'):
        flash('Please select a project and a section', 'info')
        return redirect('/')
    project_id = int(request.args.get('project'))
    section_ids = request.args.getlist('section')
    transect_ids = request.args.getlist('transect')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        localization_processor = TatorLocalizationProcessor(
            project_id=project_id,
            section_ids=section_ids,
            api=api,
            tator_url=current_app.config.get('TATOR_URL'),
            transect_media_ids=(int(transect_id) for transect_id in transect_ids) if transect_ids else None,
        )
        localization_processor.fetch_localizations()
        localization_processor.process_records()
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        flash(json.loads(e.body)['message'], 'danger')
        return redirect('/')
    comments = {}
    image_refs = {}
    # get comments and image ref list from external review db
    try:
        for section in localization_processor.sections:
            comment_res = requests.get(
                    url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/sequence/{section.deployment_name.replace("-", "_")}',
                    headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            if comment_res.status_code != 200:
                raise requests.exceptions.ConnectionError
            comments |= comment_res.json()  # merge dicts
        image_ref_res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference/quick')
        if image_ref_res.status_code != 200:
            raise requests.exceptions.ConnectionError
        image_refs = image_ref_res.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    expedition_name = localization_processor.sections[0].expedition_name
    if transect_ids:
        transect_media = api.get_media_list(project_id, media_id=[int(tid) for tid in transect_ids])
        transect_names = [media.name for media in transect_media]
        deployments_str = ', '.join(transect_names)
        tab_title = transect_names[0] if len(transect_names) == 1 else expedition_name
    else:
        deployments_str = ', '.join([section.deployment_name for section in localization_processor.sections])
        tab_title = localization_processor.sections[0].deployment_name if len(localization_processor.sections) == 1 else expedition_name
    data = {
        'annotations': localization_processor.final_records,
        'title': expedition_name,
        'tab_title': tab_title,
        'deployments': deployments_str,
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'image_refs': image_refs,
    }
    return render_template('image_review/image-review.html', data=data)
