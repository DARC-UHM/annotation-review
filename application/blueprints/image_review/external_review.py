import json
import sys

import tator
import requests
from flask import Blueprint, current_app, flash, redirect, render_template, request, session

from application.server.annosaurus import Annosaurus
from application.server.comment_processor import CommentProcessor

external_review_bp = Blueprint('external_review', __name__)


# displays comments in the external review db
@external_review_bp.get('/image-review/external-review')
def get_external_review():
    comments = []
    unread_comments = 0
    read_comments = 0
    total_comments = 0
    if 'tator_token' in session.keys():
        try:
            api = tator.get_api(
                host=current_app.config.get('TATOR_URL'),
                token=session['tator_token'],
            )
        except tator.openapi.tator_openapi.exceptions.ApiException:
            flash('Error connecting to Tator', 'danger')
            return redirect('/')
    try:
        print('Fetching external comments...', end='')
        sys.stdout.flush()
        with requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/stats',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        ) as stats_res:
            stats_json = stats_res.json()
            unread_comments = stats_json['unread_comments']
            read_comments = stats_json['read_comments']
            total_comments = stats_json['total_comments']
        # get a list of comments from external review db
        if request.args.get('reviewer'):
            query = ''
            if request.args.get('read'):
                query += '?read=true'
            elif request.args.get('unread'):
                query += '?unread=true'
            comments_res = requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/reviewer/{request.args.get("reviewer")}{query}',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments_json = comments_res.json()
            comments = comments_json['comments']
            unread_comments = comments_json['unread_comments']
            read_comments = comments_json['read_comments']
            total_comments = comments_json['total_comments']
        elif request.args.get('unread'):
            unread_comments_res = requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/unread',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments = unread_comments_res.json()
        elif request.args.get('read'):
            read_comments_res = requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/read',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments = read_comments_res.json()
        else:
            all_comments_res = requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/all',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments = all_comments_res.json()
        print('fetched!')
    except requests.exceptions.ConnectionError:
        _reviewers = []
        print('\nERROR: unable to connect to external review server\n')
    comment_loader = CommentProcessor(comments)
    if len(comment_loader.distilled_records) < 1:
        if request.args.get('unread'):
            return render_template('not-found.html', err='unread'), 404
        return render_template('not-found.html', err='comments'), 404
    data = {
        'annotations': comment_loader.distilled_records,
        'title': f'External Review {"(" + request.args.get("reviewer") + ")" if request.args.get("reviewer") else ""}',
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'missing_records': comment_loader.missing_records,
        'unread_comment_count': unread_comments,
        'read_comment_count': read_comments,
        'total_comment_count': total_comments,
    }
    return render_template('image-review/image-review.html', data=data)


# adds an annotation for review/updates the reviewer for an annotation
@external_review_bp.post('/image-review/external-review/annotation')
def add_external_review():
    def add_vars_or_tator_comment(status_code):
        if not request.values.get('all_localizations'):  # VARS annotation, update VARS comment
            annosaurus = Annosaurus(current_app.config.get('ANNOSAURUS_URL'))
            annosaurus.update_annotation_comment(
                observation_uuid=request.values.get('observation_uuid'),
                reviewers=json.loads(request.values.get('reviewers')),
                client_secret=current_app.config.get('ANNOSAURUS_CLIENT_SECRET')
            )
        else:  # Tator localization, update Tator notes
            api = tator.get_api(
                host=current_app.config.get('TATOR_URL'),
                token=session.get('tator_token'),
            )
            current_notes = api.get_localization_by_elemental_id(
                version=json.loads(request.values.get('all_localizations'))[0].get('version', 45),
                elemental_id=request.values.get('observation_uuid'),
            ).attributes.get('Notes', '').split('|')
            current_notes = [note for note in current_notes if 'send to' not in note.lower()]  # get rid of 'send to expert' notes
            current_notes = [note for note in current_notes if 'added for review' not in note.lower()]  # get rid of old 'added for review' notes
            current_notes = '|'.join(current_notes)
            new_notes = f'{current_notes + "|" if current_notes else ""}Added for review: {", ".join(json.loads(request.values.get("reviewers")))}'
            api.update_localization_by_elemental_id(
                version=json.loads(request.values.get('all_localizations'))[0].get('version', 45),
                elemental_id=request.values.get('observation_uuid'),
                localization_update=tator.models.LocalizationUpdate(
                    attributes={'Notes': new_notes},
                )
            )
        return {}, status_code
    data = {
        'uuid': request.values.get('observation_uuid'),
        'all_localizations': request.values.get('all_localizations'),
        'id_reference': request.values.get('id_reference'),
        'section_id': request.values.get('section_id'),
        'sequence': request.values.get('sequence'),
        'timestamp': request.values.get('timestamp'),
        'reviewers': request.values.get('reviewers'),
        'image_url': request.values.get('image_url'),
        'video_url': request.values.get('video_url'),
        'annotator': request.values.get('annotator'),
        'depth': request.values.get('depth'),
        'lat': request.values.get('lat'),
        'long': request.values.get('long'),
        'temperature': request.values.get('temperature'),
        'oxygen_ml_l': request.values.get('oxygen_ml_l'),
    }
    with requests.post(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            data=data,
    ) as post_comment_res:
        if post_comment_res.status_code == 409:  # comment already exists in the db, update record
            put_comment_res = requests.put(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/reviewers/{data["uuid"]}',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
                data=data,
            )
            if put_comment_res.status_code == 200:
                return add_vars_or_tator_comment(200)
        elif post_comment_res.status_code == 201:  # comment added to db, update VARS "comment" field
            return add_vars_or_tator_comment(201)
        return {}, 500


# deletes an item from the external review db
@external_review_bp.delete('/image-review/external-review/annotation')
def delete_external_review():
    delete_comment_res = requests.delete(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/{request.values.get("uuid")}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    )
    if delete_comment_res.status_code == 200:
        if request.values.get('tator') and request.values.get('tator') == 'true':  # tator localization
            api = tator.get_api(
                host=current_app.config.get('TATOR_URL'),
                token=session.get('tator_token'),
            )
            current_notes = api.get_localization_by_elemental_id(
                version=request.values.get('tator_version'),
                elemental_id=request.values.get('uuid'),
            ).attributes.get('Notes', '').split('|')
            current_notes = [note for note in current_notes if 'send to' not in note.lower()]  # get rid of 'send to expert' notes
            current_notes = [note for note in current_notes if 'added for review' not in note.lower()]  # get rid of old 'added for review' notes
            api.update_localization_by_elemental_id(
                version=request.values.get('tator_version'),
                elemental_id=request.values.get('uuid'),
                localization_update=tator.models.LocalizationUpdate(
                    attributes={'Notes': '|'.join(current_notes)},
                )
            )
        else:  # VARS annotation
            annosaurus = Annosaurus(current_app.config.get('ANNOSAURUS_URL'))
            annosaurus.update_annotation_comment(
                observation_uuid=request.values.get('uuid'),
                reviewers=[],
                client_secret=current_app.config.get('ANNOSAURUS_CLIENT_SECRET')
            )
        return {}, 200
    return {}, 500


# displays information about all the reviewers in the hurl db
@external_review_bp.get('/image-review/external-review/reviewer-list')
def reviewers():
    return render_template('external-reviewers.html', reviewers=session.get('reviewers'))


# create or update a reviewer's information
@external_review_bp.post('/image-review/external-review/reviewer')
def update_reviewer_info():
    success = False
    name = request.values.get('ogReviewerName') or 'nobody'
    data = {
        'new_name': request.values.get('editReviewerName'),
        'phylum': request.values.get('editPhylum'),
        'focus': request.values.get('editFocus'),
        'organization': request.values.get('editOrganization'),
        'email': request.values.get('editEmail')
    }
    patch_reviewer_res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/reviewer/{name}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        data=data,
    )
    if patch_reviewer_res.status_code == 404:
        data['name'] = data['new_name']
        post_reviewer_res = requests.post(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/reviewer',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            data=data,
        )
        if post_reviewer_res.status_code == 201:
            success = True
            flash('Successfully added reviewer', 'success')
        else:
            flash(post_reviewer_res.json(), 'danger')
    elif patch_reviewer_res.status_code == 200:
        success = True
        flash('Successfully updated reviewer', 'success')
    else:
        flash(patch_reviewer_res.json(), 'danger')
    if success:
        with requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/reviewer/all',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        ) as all_reviewers_res:
            session['reviewers'] = all_reviewers_res.json()
    return redirect('/image-review/external-review/reviewer-list')


# delete a reviewer
@external_review_bp.delete('/image-review/external-review/reviewer/<name>')
def delete_reviewer(name):
    delete_reviewer_res = requests.delete(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/reviewer/{name}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    )
    if delete_reviewer_res.status_code == 200:
        flash('Successfully deleted reviewer', 'success')
        with requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/reviewer/all',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        ) as res:
            session['reviewers'] = res.json()
    else:
        flash('Error deleting reviewer', 'danger')
    return {}, delete_reviewer_res.status_code
