import requests
from flask import Blueprint, current_app, request, render_template, session

from application.server.vars_annotation_processor import VarsAnnotationProcessor

vars_image_review_bp = Blueprint('vars_image_review', __name__)


# view VARS annotations with images in a specified dive (or dives)
@vars_image_review_bp.get('/image-review/vars')
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
                return render_template('not-found.html', err='dive'), 404
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    # get images in sequence
    image_loader = VarsAnnotationProcessor(sequences)
    image_loader.process_sequences()
    if len(image_loader.final_records) < 1:
        return render_template('not-found.html', err='pics'), 404
    data = {
        'annotations': image_loader.final_records,
        'highest_id_ref': image_loader.highest_id_ref,
        'title': image_loader.vessel_name,
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
    }
    return render_template('image-review/image-review.html', data=data)
