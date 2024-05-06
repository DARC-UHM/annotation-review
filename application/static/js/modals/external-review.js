import { updateFlashMessages } from '../util/updateFlashMessages.js';
import { reviewerList } from '../util/reviewer-list.js';
import { updateHash } from '../image-review/image-review.js';

let reviewerIndex = 0;
let totalReviewers = 0;
let currentAnnotation;

// Adds another reviewer to the external review modal
function addReviewer(reviewerName) {
    if (totalReviewers > 4) {
        return;
    }
    const phylum = currentAnnotation.phylum?.toLowerCase() || null;
    const recommendedReviewers = phylum ? reviewers.filter((obj) => obj.phylum.toLowerCase().includes(phylum)) : reviewers;
    const thisReviewerIndex = ++reviewerIndex;

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

// Removes a reviewer from the external review modal
function removeReviewer(num) {
    if (totalReviewers === 1) {
        return;
    }
    $('#addReviewerButton').show();
    $(`#reviewerRow${num}`).remove();
    totalReviewers--;
    $('#externalModalSubmitButton').prop('disabled', false);
}

// For the initial loading of the modal: if the annotation is already added for review, load these reviewers to the modal
function updateReviewerName(uuid) {
    const reviewerComments = comments[uuid].reviewer_comments;
    $('#reviewerName1').html(reviewerComments[0].reviewer);
    for (let i = 1; i < reviewerComments.length; i++) {
        addReviewer(reviewerComments[i].reviewer);
    }
}

// Updates the assigned external reviewers in the external review db
async function updateExternalReviewers() {
    event.preventDefault();
    const reviewers = [];
    for (const item of document.getElementsByClassName('reviewerName')) {
        if (item.innerHTML !== 'Select') {
            reviewers.push(item.innerHTML);
        }
    }
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#externalReviewModal').modal('hide');
    $('#externalReviewers').val(JSON.stringify(reviewers));

    // post form data to backend
    const formData = new FormData($('#updateExternalReviewerForm')[0]);
    const res = await fetch('/external-review', {
        method: 'POST',
        body: formData,
    });

    // update the annotation object and comments object with the new reviewers
    const index = annotations.findIndex((anno) => anno.observation_uuid.toString() === formData.get('observation_uuid'));
    if (res.status === 200 || res.status === 201) {
        if (!comments[formData.get('observation_uuid')]) {
            comments[formData.get('observation_uuid')] = {};
        }
        // refetch the comments for the observation
        const commentsRes = await fetch(`https://hurlstor.soest.hawaii.edu:5000/comment/get/${formData.get('observation_uuid')}`);
        const commentJson = await commentsRes.json();
        comments[formData.get('observation_uuid')] = commentJson;
        annotations[index].comment = `Added for review: ${reviewers.join(', ')}`; // doesn't accurately reflect data on server, but that's okay
        annotations[index].notes = `Added for review: ${reviewers.join(', ')}`; // doesn't accurately reflect data on server, but that's okay
        updateFlashMessages(commentsRes.status === 200 ? 'Reviewers successfully updated' : 'Successfully added for review', 'success');
        updateHash();
    } else {
        updateFlashMessages('Failed to update reviewers - please try again', 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

// Marks an annotation as "read" in the external review db (each annotation has a single "read" field, not each individual comment)
async function markCommentRead(commentUuid) {
    event.preventDefault();
    const url = new URL(window.location.href);
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const res = await fetch(`https://hurlstor.soest.hawaii.edu:5000/comment/mark-read/${commentUuid}`, {
        method: 'PUT',
    });
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
}

// Marks an annotation as "unread" in the external review db
async function markCommentUnread(commentUuid) {
    event.preventDefault();
    const url = new URL(window.location.href);
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const res = await fetch(`https://hurlstor.soest.hawaii.edu:5000/comment/mark-unread/${commentUuid}`, {
        method: 'PUT',
    });
    if (res.status === 200) {
        if (url.searchParams.get('read')) {
            // we're on the read page, remove from list
            delete comments[commentUuid]; // remove the comment object from comments object
            // remove the annotation object from the annotations list
            annotations.splice(annotations.findIndex((anno) => anno.observation_uuid === commentUuid), 1);
        } else {
            // we're on the all comments page or a dive page, just mark as read
            comments[commentUuid].unread = true;
        }
        updateHash();
        updateFlashMessages('Comment marked as unread', 'success');
    } else {
        updateFlashMessages('Unable to mark comment as unread - please try again', 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

// Deletes an annotation from the external review db
async function deleteFromExternalReview() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#deleteReviewModal').modal('hide');

    const formData = new FormData($('#deleteFromExternalReviewForm')[0]);
    const res = await fetch('/external-review', {
        method: 'DELETE',
        body: formData,
    });
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
}

async function deleteMissingRecords() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#missingRecordsModal').modal('hide');
    let statusOkay = true;

    for (const missingRecord of missingRecords) {
        const formData = new FormData();
        formData.append('uuid', missingRecord.uuid);
        const res = await fetch('/external-review', {
            method: 'DELETE',
            body: formData,
        });
        if (res.status !== 200) {
            statusOkay = false;
            break;
        }
    }
    if (statusOkay) {
        updateFlashMessages('Removed missing records from external review', 'success');
        updateHash();
    } else {
        updateFlashMessages('Error removing missing records from external review', 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

$(document).ready(() => {
    window.addReviewer = addReviewer;
    window.removeReviewer = removeReviewer;
    window.updateReviewerName = updateReviewerName;
    window.updateExternalReviewers = updateExternalReviewers;
    window.markCommentRead = markCommentRead;
    window.markCommentUnread = markCommentUnread;
    window.deleteFromExternalReview = deleteFromExternalReview;
    window.deleteMissingRecords = deleteMissingRecords;

    $('#externalReviewModal').on('show.bs.modal', (e) => {
        currentAnnotation = $(e.relatedTarget).data('anno');
        let scientificName = currentAnnotation.scientific_name;
        if (scientificName && scientificName !== '') {
            // tator localization
            if (currentAnnotation.tentative_id && currentAnnotation.tentative_id !== '') {
                scientificName += ` (${currentAnnotation.tentative_id}?)`;
            }
            currentAnnotation.video_url = `https://hurlstor.soest.hawaii.edu:5000/video?link=/tator-video/${currentAnnotation.media_id}&time=${Math.round(currentAnnotation.frame / 30)}`;
            // just assume that all records with the same scientific name in the same clip are the same individual
            currentAnnotation.id_reference = `${currentAnnotation.media_id}:${scientificName}`;
        }
        $('#externalModalSubmitButton').prop('disabled', true);
        addReviewer(null);
        $('#externalObservationUuid').val(currentAnnotation.observation_uuid);
        $('#externalSequence').val(currentAnnotation.video_sequence_name);
        $('#externalSectionId').val(currentAnnotation.section_id);
        $('#externalScientificName').val(scientificName);
        $('#externalTatorOverlay').val(JSON.stringify(currentAnnotation.all_localizations));
        $('#externalTimestamp').val(currentAnnotation.recorded_timestamp);
        $('#externalImageUrl').val(currentAnnotation.image_url || currentAnnotation.frame_url);
        $('#externalVideoUrl').val(currentAnnotation.video_url);
        $('#externalAnnotator').val(currentAnnotation.annotator);
        $('#externalIdRef').val(currentAnnotation.id_reference);
        $('#externalLat').val(currentAnnotation.lat);
        $('#externalLong').val(currentAnnotation.long);
        $('#externalDepth').val(currentAnnotation.depth);
        $('#externalTemperature').val(currentAnnotation.temperature);
        $('#externalOxygen').val(currentAnnotation.oxygen_ml_l);
    });

    $('#externalReviewModal').on('hide.bs.modal', () => {
        currentAnnotation = null;
        totalReviewers = 0;
        reviewerIndex = 0;
        $('#reviewerList').empty(); // clear the reviewer list from the modal
    })

    $('#deleteReviewModal').on('show.bs.modal', function (e) {
        const anno = $(e.relatedTarget).data('anno');
        $('#externalDeleteTator').val(anno.scientific_name != null && anno.scientific_name !== '');
        $('#externalDeleteUuid').val(anno.observation_uuid);
    });
});
