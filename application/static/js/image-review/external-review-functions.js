import { updateFlashMessages } from '../util/updateFlashMessages.js';
import { reviewerList } from '../util/reviewer-list.js';

export function addReviewer(reviewerName) {
    if (totalReviewers > 4) {
        return;
    }
    const phylum = currentAnnotation.phylum.toLowerCase();
    const recommendedReviewers = reviewers.filter((obj) => obj.phylum.toLowerCase().includes(phylum));
    const thisReviewerIndex = ++reviewerIndex;

    // TODO figure out how to pass totalReviewers between this and qaqc/image review pages
    totalReviewers++;

    $('#reviewerList').append(`
        <div id="reviewerRow${thisReviewerIndex}" class="row pt-1">
            <input type="hidden" id="externalReviewer${thisReviewerIndex}" name="reviewer${thisReviewerIndex}">
            <button type="button" id="reviewerName${thisReviewerIndex}Button" class="btn reviewerNameButton" name="reviewerName">
                <div class="row">
                    <div class="col-1 ms-2"></div>
                    <div id="reviewerName${thisReviewerIndex}" class="col reviewerName">${reviewerName || 'Select'}</div>
                    <div class="col-1 me-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-down" viewBox="0 0 16 16">
                          <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
                        </svg>
                    </div>
                </div>
            </button>
            <div class="col-1 mt-1">
                <button id="xButton${thisReviewerIndex}" type="button" class="xButton">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                    </svg>
                </button>
            </div>
        </div>
    `);
    $(`#xButton${thisReviewerIndex}`).on('click', () => removeReviewer(thisReviewerIndex));
    reviewerList($(`#reviewerName${thisReviewerIndex}Button`), recommendedReviewers, $(`#reviewerName${thisReviewerIndex}`));

    if (totalReviewers === 5) {
        $('#addReviewerButton').hide();
    }
}

export function removeReviewer(num) {
    if (totalReviewers === 1) {
        return;
    }
    $('#addReviewerButton').show();
    $(`#reviewerRow${num}`).remove();
    totalReviewers--;
    $('#externalModalSubmitButton').prop('disabled', false);
}

export function updateReviewerName(uuid) {
    const reviewerComments = comments[uuid].reviewer_comments;
    $('#reviewerName1').html(reviewerComments[0].reviewer);
    for (let i = 1; i < reviewerComments.length; i++) {
        addReviewer(reviewerComments[i].reviewer);
    }
}

export function updateExternalReviewers() {
    // loads reviewers to form fields and submits form
    event.preventDefault();

    const reviewers = [];
    for (const item of document.getElementsByClassName('reviewerName')) {
        reviewers.push(item.innerHTML);
    }
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#externalReviewModal').modal('hide');
    $('#externalReviewers').val(JSON.stringify(reviewers));

    const formData = new FormData($('#updateExternalReviewerForm')[0]);
    fetch('/external-review', {
        method: 'POST',
        body: formData,
    })
        .then((result) => {
            const index = annotations.findIndex((anno) => anno.observation_uuid.toString() === formData.get('observation_uuid'));
            if (result.status === 200 || result.status === 201) {
                if (!comments[formData.get('observation_uuid')]) {
                    comments[formData.get('observation_uuid')] = {};
                }
                fetch(`https://hurlstor.soest.hawaii.edu:5000/comment/get/${formData.get('observation_uuid')}`)
                    .then((res) => res.json())
                    .then((data) => {
                        comments[formData.get('observation_uuid')] = data;
                        annotations[index].comment = `Added for review: ${reviewers.join(', ')}`; // doesn't accurately reflect data on server, but that's okay
                        annotations[index].notes = `Added for review: ${reviewers.join(', ')}`; // doesn't accurately reflect data on server, but that's okay
                        updateFlashMessages(result.status === 200 ? 'Reviewers successfully updated' : 'Successfully added for review', 'success');
                        updateHash();
                    })
                    .catch((err) => console.log(err));
            } else {
                updateFlashMessages('Failed to update reviewers - please try again', 'danger');
            }
            $('#load-overlay').addClass('loader-bg-hidden');
            $('#load-overlay').removeClass('loader-bg');
        })
        .catch((err) => console.log(err));
}

export function markCommentRead(commentUuid) {
    event.preventDefault();
    const url = new URL(window.location.href);
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    fetch(`https://hurlstor.soest.hawaii.edu:5000/comment/mark-read/${commentUuid}`, {
        method: 'PUT',
    })
        .then((res) => {
            if (res.status === 200) {
                if (url.searchParams.get('unread')) {
                    // we're on the unread page, remove from list
                    delete comments[commentUuid]; // remove the comment object from comments object
                    // remove the annotation object from the annotations list
                    annotations.splice(annotations.findIndex((anno) => anno.observation_uuid === commentUuid), 1);
                } else {
                    // we're on the all comments page or a dive page, just mark as read
                    comments[commentUuid].unread = false;
                }
                updateHash();
                updateFlashMessages('Comment marked as read', 'success');
            } else {
                updateFlashMessages('Unable to mark comment as read - please try again', 'danger');
            }
            $('#load-overlay').addClass('loader-bg-hidden');
            $('#load-overlay').removeClass('loader-bg');
        })
        .catch((err) => console.log(err));
}

export function deleteFromExternalReview() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#deleteReviewModal').modal('hide');

    const formData = new FormData($('#deleteFromExternalReviewForm')[0]);
    fetch('/external-review', {
        method: 'DELETE',
        body: formData,
    })
        .then((res) => {
            if (res.status === 200) {
                const index = annotations.findIndex((anno) => anno.observation_uuid.toString() === formData.get('uuid'));
                delete comments[formData.get('uuid')];
                annotations[index].comment = '';
                annotations[index].notes = '';
                updateFlashMessages('Removed annotation from external review', 'success');
                updateHash();
            } else {
                updateFlashMessages('Error removing annotation from external review', 'danger');
            }
            $('#load-overlay').addClass('loader-bg-hidden');
            $('#load-overlay').removeClass('loader-bg');
        })
        .catch((err) => console.log(err));
}
