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


def get_individual_count(tator_client, project_id: int, section_ids: list[int], dot_type: int, media_ids: list[int] = None) -> int:
    """Checklist individual total: one per dot, plus the abundance weight for the larger buckets."""
    if media_ids:
        localizations = []
        for i in range(0, len(media_ids), 50):
            localizations += tator_client.get_localizations(
                project_id,
                media_ids=media_ids[i:i + 50],
                localization_type=dot_type,
            )
    else:
        localizations = tator_client.get_localizations(project_id, section_ids=section_ids, localization_type=dot_type)
    weights = dict(_ABUNDANCE_WEIGHTS)
    total = 0
    for localization in localizations:
        total += 1
        abundance = localization.get('attributes', {}).get('Categorical Abundance')
        total += weights.get(abundance, 0)
    return total


def get_counts(tator_client, project_id: int, section_ids: list[int], dot_type: int, media_ids: list[int] = None) -> tuple[int, int]:
    """Checklist totals: every localization, and the individual total for the given dot type."""
    if media_ids:
        localization_count = tator_client.get_localization_count(project_id, media_ids=media_ids)
    else:
        localization_count = tator_client.get_localization_count(project_id, section_ids)
    individual_count = get_individual_count(tator_client, project_id, section_ids, dot_type, media_ids=media_ids)
    return localization_count, individual_count


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
