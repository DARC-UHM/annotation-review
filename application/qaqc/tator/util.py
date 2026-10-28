import json

import tator
import requests
from flask import current_app, flash, redirect, session


def init_tator_api():
    if 'tator_token' not in session:
        flash('Please log in to Tator', 'info')
        return None, redirect('/')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        return api, None
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        flash(json.loads(e.body)['message'], 'danger')
        return None, redirect('/')


_ABUNDANCE_WEIGHTS = (
    ('20-49', 35),
    ('50-99', 75),
    ('100-999', 500),
    ('1000+', 1000),
)


def get_individual_count(tator_client, project_id: int, section_ids: list[int], dot_type: int) -> int:
    """Checklist individual total: one per dot, plus the abundance weight for the larger buckets."""
    total = tator_client.get_localization_count(project_id, section_ids, localization_type=dot_type)
    for abundance, weight in _ABUNDANCE_WEIGHTS:
        total += weight * tator_client.get_localization_count(
            project_id,
            section_ids,
            localization_type=dot_type,
            attribute=f'Categorical Abundance::{abundance}',
        )
    return total


# TODO - either update review server to allow batch requests by sequence, or use threading to make this faster
def get_comments_and_image_refs(deployment_names: list[str]) -> tuple[dict, dict]:
    comments = {}
    image_refs = {}
    try:
        for deployment in deployment_names:
            print(f'Getting comments for deployment {deployment}...')
            comment_res = requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment?sequence={deployment}',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            if comment_res.status_code != 200:
                raise requests.exceptions.ConnectionError
            comments |= {comment['uuid']: comment for comment in comment_res.json()}
        image_ref_res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference/quick')
        if image_ref_res.status_code != 200:
            raise requests.exceptions.ConnectionError
        image_refs = image_ref_res.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    return comments, image_refs
