"""
VARS-specific image review endpoint.

/image-review/vars [GET]
"""

import requests
from flask import current_app, request, render_template, session

from . import vars_image_review_bp
from application.image_review.vars.vars_annotation_processor import VarsAnnotationProcessor


# view VARS annotations with images in a specified dive (or dives)
@vars_image_review_bp.get('')
def view_images():
    comments = {}
    sequences = request.args.getlist('sequence')
    # get comments from external review db
    try:
        for sequence in sequences:
            with requests.get(
                    url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/sequence/{sequence}',
                    headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            ) as res:
                comments = comments | res.json()  # merge dicts
            if sequence not in session.get('vars_video_sequences', []):
                return render_template('errors/404.html', err='dive'), 404
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    # get images in sequence
    image_loader = VarsAnnotationProcessor(
        sequence_names=sequences,
        vars_dive_url=current_app.config.get('VARS_DIVE_QUERY_URL'),
        vars_phylogeny_url=current_app.config.get('VARS_PHYLOGENY_URL'),
    )
    image_loader.process_sequences()
    if len(image_loader.final_records) < 1:
        return render_template('errors/404.html', err='pics'), 404
    data = {
        'annotations': image_loader.final_records,
        'highest_id_ref': image_loader.highest_id_ref,
        'title': image_loader.vessel_name,
        'tab_title': sequences[0] if len(sequences) == 1 else f'{sequences[0]} - {sequences[-1].split(" ")[-1]}',
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
    }
    return render_template('image_review/image-review.html', data=data)
