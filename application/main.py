import traceback
from json import JSONDecodeError

from flask import flash, render_template, request, session

from application import app
from application.vars.annosaurus import *


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    unread_comments = 0
    read_comments = 0
    total_comments = 0
    active_reviewers = []
    try:
        # get list of reviewers from external review db
        with requests.get(
            url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as reviewers_res:
            session['reviewers'] = reviewers_res.json()
        # get stats from external review db
        with requests.get(
            url=f'{app.config.get("DARC_REVIEW_URL")}/stats',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as stats_res:
            stats_json = stats_res.json()
            unread_comments = stats_json['unread_comments']
            read_comments = stats_json['read_comments']
            total_comments = stats_json['total_comments']
            active_reviewers = stats_json['active_reviewers']
    except (JSONDecodeError, KeyError, requests.exceptions.ConnectionError):
        flash('Unable to connect to external review server', 'danger')
        print('\nERROR: unable to connect to external review server\n')
        session['reviewers'] = []
    try:
        # get list of sequences from vars
        with requests.get(url=app.config.get('VARS_SEQUENCE_LIST_URL')) as sequences_res:
            session['vars_video_sequences'] = sequences_res.json()
        # get concept list from vars (for input validation)
        with requests.get(url=app.config.get('VARS_CONCEPT_LIST_URL')) as concept_res:
            session['vars_concepts'] = concept_res.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to VARS\n')
        flash('Unable to connect to VARS', 'danger')
        session['vars_video_sequences'] = []
        session['vars_concepts'] = []
    return render_template(
        'index.html',
        sequences=session['vars_video_sequences'],
        unread_comment_count=unread_comments,
        read_comment_count=read_comments,
        total_comment_count=total_comments,
        active_reviewers=active_reviewers,
    )


# video player
@app.get('/video')
def video():
    data = {'link': request.args.get('link'), 'time': request.args.get('time')}
    return render_template('video.html', data=data), 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html', err=''), 404


@app.errorhandler(Exception)
def server_error(e):
    error = f'{type(e).__name__}: {e}'
    print('\nApplication error 😔')
    print(error)
    print(traceback.format_exc())
    return render_template('errors/500.html', err=error), 500
