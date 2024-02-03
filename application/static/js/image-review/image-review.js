import { autocomplete } from '../util/autocomplete.js';
import { reviewerList } from '../util/reviewer-list.js';
import { updateFlashMessages } from '../util/updateFlashMessages.js';
import { varsAnnotationTableRow } from './vars-annotation-table-row.js';
import { tatorLocalizationRow } from './tator-localization-table-row.js';

const guidePhotoVals = ['1 best', '2 good', '3 okay', ''];
const sequences = [];

let currentPage = 1;
let pageCount;
let paginationLimit = 25;
let annotationsToDisplay = annotations;
let currentAnnotation;

let reviewerIndex = 0;
let totalReviewers = 0;

const getPaginationNumbers = () => {
    $('#pagination-numbers').empty();
    for (let i = 1; i <= pageCount; i++) {
        const pageNumber = document.createElement('button');
        pageNumber.className = 'pagination-number';
        pageNumber.innerHTML = i;
        pageNumber.setAttribute('page-index', i);
        pageNumber.setAttribute('aria-label', 'Page ' + i);
        $('#pagination-numbers').append(pageNumber);
    }
    document.querySelectorAll('.pagination-number').forEach((button) => {
        const pageIndex = Number(button.getAttribute('page-index'));
        if (pageIndex) {
            button.addEventListener('click', () => {
                setCurrentPage(pageIndex);
            });
        }
    });
    handleActivePageNumber();
};

const handleActivePageNumber = () => {
    document.querySelectorAll('.pagination-number').forEach((button) => {
        button.classList.remove('active');

        const pageIndex = Number(button.getAttribute('page-index'));
        if (pageIndex === currentPage) {
            button.classList.add('active');
        }
    });
    $('#currentPageNum').html(currentPage);
    $('#currentPageNumBottom').html(currentPage);
};

const setCurrentPage = (pageNum) => {
    const prevRange = (pageNum - 1) * paginationLimit;
    const currRange = pageNum * paginationLimit;
    const prevHash = window.location.hash.substring(0, window.location.hash.indexOf('pg='));
    const prevPage = currentPage;

    saveScrollPosition(prevPage);

    currentPage = pageNum;
    location.hash = prevHash.length > 1 ? `${prevHash}pg=${pageNum}` : `#pg=${pageNum}`;

    handleActivePageNumber();
    handlePageButtonsStatus();

    $('#annotationTable tbody').remove();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');

    annotationsToDisplay.forEach((annotation, index) => {
        if (index >= prevRange && index < currRange) {
            if (annotation.scientific_name) { // this is a tator localization
                $('#annotationTable').find('tbody').append(tatorLocalizationRow(annotation, comments[annotation.observation_uuid]));
                $(`#${annotation.observation_uuid}_overlay`).css('opacity', '0.5');
                $(`#${annotation.observation_uuid}_image`).hover((e) => {
                    if (e.type === 'mouseenter') {
                        $(`#${annotation.observation_uuid}_overlay`).css('opacity', '1.0');
                    } else if (e.type === 'mouseleave') {
                        $(`#${annotation.observation_uuid}_overlay`).css('opacity', '0.5');
                    }
                });
            } else { // this is a VARS annotation
                $('#annotationTable').find('tbody').append(varsAnnotationTableRow(annotation, comments[annotation.observation_uuid]));
            }
        }
    });

    const newUrl = new URL(window.location.href);

    if (sessionStorage.getItem(`scrollPos${newUrl.search}${newUrl.hash}`)) {
        window.scrollTo({
            top: sessionStorage.getItem(`scrollPos${newUrl.search}${newUrl.hash}`),
            left: 0,
            behavior: 'instant',
        });
    } else {
       window.scrollTo({
           top: 0,
           left: 0,
           behavior: 'instant'
       });
    }
};

const handlePageButtonsStatus = () => {
    if (currentPage === 1) {
        $('#prev-button').prop('disabled', true);
    } else {
        $('#prev-button').prop('disabled', false);
    }
    if (pageCount === currentPage) {
        $('#next-button').prop('disabled', true);
    } else {
        $('#next-button').prop('disabled', false);
    }
};

function validateName(name) {
    let disabled = false;
    if (name && !allConcepts.includes(name)) {
        disabled = true;
    }
    $('#editModalSubmitButton')[0].disabled = disabled;
}

// remove filter from hash
function removeFilter(key, value) {
    const index = window.location.hash.indexOf(key);
    const newHash = `${window.location.hash.substring(0, index)}${window.location.hash.substring(index + key.length + value.length + 2)}`;
    saveScrollPosition(currentPage);
    location.hash = newHash;
}

window.removeFilter = removeFilter;

function showAddFilter() {
    $('#addFilterRow').show();
    $('#addFilterButton').hide();
}

window.showAddFilter = showAddFilter;

// add filter to hash
function addFilter() {
    event.preventDefault();
    const index = window.location.hash.indexOf('pg=');
    const filterKey = $('#imageFilterSelect').val().toLowerCase();
    const filterVal = $('#imageFilterEntry').val();
    saveScrollPosition(currentPage);
    location.hash = location.hash.substring(0, index - 1).length > 1
        ? `${location.hash.substring(0, index - 1)}&${filterKey}=${filterVal}&pg=1`
        : `#${filterKey}=${filterVal}&pg=1`;
}

window.addFilter = addFilter;

function sortBy(key) {
    let tempKey;
    key = key.replaceAll('%20', ' ');
    if (key === 'Default') {
        annotationsToDisplay = annotations;
        return;
    }
    if (key === 'Timestamp') {
        tempKey = 'recorded_timestamp';
        // this is for tator localizations
        annotationsToDisplay = annotationsToDisplay.sort((a, b) => a.frame - b.frame);
        annotationsToDisplay = annotationsToDisplay.sort((a, b) => a.media_id - b.media_id);
    } else if (key === 'ID Reference') {
        tempKey = 'identity_reference';
    } else {
        tempKey = key.toLowerCase();
    }
    // move all records missing specified property to bottom
    let filtered = annotationsToDisplay.filter((anno) => anno[tempKey]);
    if (tempKey === 'depth' || tempKey === 'identity_reference') {
        filtered = filtered.sort((a, b) => a[tempKey] - b[tempKey]); // sort by number instead of string
    } else {
        filtered = filtered.sort((a, b) => (a[tempKey] > b[tempKey]) ? 1 : ((b[tempKey] > a[tempKey]) ? -1 : 0));
    }
    annotationsToDisplay = filtered.concat(annotationsToDisplay.filter((anno) => !anno[tempKey]));

    $('#sortSelect').val(key);
}

function removeReviewer(num) {
    if (totalReviewers === 1) {
        return;
    }
    $('#addReviewerButton').show();
    $(`#reviewerRow${num}`).remove();
    totalReviewers--;
    $('#externalModalSubmitButton').prop('disabled', false);
}

window.removeReviewer = removeReviewer;

function addReviewer(reviewerName) {
    if (totalReviewers > 4) {
        return;
    }
    const phylum = currentAnnotation.phylum.toLowerCase();
    const recommendedReviewers = reviewers.filter((obj) => obj.phylum.toLowerCase().includes(phylum));
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

window.addReviewer = addReviewer;

function updateReviewerName(uuid) {
    const reviewerComments = comments[uuid].reviewer_comments;
    $('#reviewerName1').html(reviewerComments[0].reviewer);
    for (let i = 1; i < reviewerComments.length; i++) {
        addReviewer(reviewerComments[i].reviewer);
    }
}

window.updateReviewerName = updateReviewerName;

function updateFilterHint() {
    $('#imageFilterEntry').attr('placeholder', `Enter ${$('#imageFilterSelect').val().toLowerCase()}`);
}

window.updateFilterHint = updateFilterHint;

function updateHash() {
    const url = new URL(window.location.href);
    const hash = url.hash.slice(1);
    const filterPairs = hash.split('&');
    const filter = {};

    annotationsToDisplay = annotations;

    filterPairs.pop(); // pop page number

    for (const pair of filterPairs) {
        const key = pair.split('=')[0];
        const value = pair.split('=')[1];
        if (key !== 'sort') {
            filter[key] = value;
        } else {
            sortBy(value);
        }
    }

    $('#sequenceList').empty();
    $('#sequenceList').html(`${sequences.join(', ')}<br>`);
    $('#sequenceList').append(`<div id="filterList" class="small mt-2">Filters: ${Object.keys(filter).length ? '' : 'None'}</div>`);

    for (const key of Object.keys(filter)) {
        $('#filterList').append(`
            <span class="small filter-pill position-relative">
                ${key[0].toUpperCase()}${key.substring(1)}: ${filter[key].replaceAll('%20', ' ')}
                <button type="button" class="position-absolute filter-x" onclick="removeFilter('${key}', '${filter[key]}')">×</button>
            </span>
        `);
    }

    $('#filterList').append(`
        <span id="addFilterRow" class="small ms-3" style="display: none;">
            <form onsubmit="addFilter()" class="d-inline-block">
                <span class="position-relative">
                    <select id="imageFilterSelect" onchange="updateFilterHint()">
                        <option>Phylum</option>
                        <option>Class</option>
                        <option>Order</option>
                        <option>Family</option>
                        <option>Genus</option>
                        <option>Species</option>
                        <option>Certainty</option>
                        <option>Comment (VARS)</option>
                        <option>Notes (Tator)</option>
                        <option>Annotator</option>
                    </select>
                    <span class="position-absolute dropdown-chev">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-down" viewBox="0 0 16 16">
                          <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
                        </svg>
                    </span>
                </span>
                <input type="text" id="imageFilterEntry" name="blank" placeholder="Enter phylum" autocomplete="off">
                <button id="saveFilterButton" type="submit" class="plusButton">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                      <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                    </svg>
                </button>
            </form>
        </span>
        <button id="addFilterButton" type="button" class="plusButton ms-2" onclick="showAddFilter()">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-plus"
                 viewBox="0 0 16 16">
                <path
                    d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
            </svg>
        </button>
    `);
    autocomplete($('#imageFilterEntry'), allConcepts);

    if (filter['phylum']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['phylum']?.toLowerCase() === filter['phylum'].toLowerCase());
    }
    if (filter['class']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['class']?.toLowerCase() === filter['class'].toLowerCase());
    }
    if (filter['order']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['order']?.toLowerCase() === filter['order'].toLowerCase());
    }
    if (filter['family']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['family']?.toLowerCase() === filter['family'].toLowerCase());
    }
    if (filter['genus']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['genus']?.toLowerCase() === filter['genus'].toLowerCase());
    }
    if (filter['species']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['species']?.toLowerCase() === filter['species'].toLowerCase().replaceAll('%20', ' '));
    }
    if (filter['certainty']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['identity_certainty']?.toLowerCase().includes(filter['certainty'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['comment']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['comment']?.toLowerCase().includes(filter['comment'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['annotator']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['annotator']?.toLowerCase().includes(filter['annotator'].toLowerCase().replaceAll('%20', ' ')));
    }

    if (!annotationsToDisplay.length) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    pageCount = Math.ceil(annotationsToDisplay.length / paginationLimit);

    getPaginationNumbers();

    if (window.location.hash.includes('pg=')) {
        setCurrentPage(parseInt(window.location.hash.slice(window.location.hash.indexOf('pg=')).substring(3)));
    } else {
        location.replace(`#sort=Default&pg=1`); // to prevent extra pages without hash of page num when back button pressed
        setCurrentPage(1);
    }

    $('#annotationCount').html(annotationsToDisplay.length);
    $('#annotationCountBottom').html(annotationsToDisplay.length);
    $('#totalPageNum').html(pageCount);
    $('#totalPageNumBottom').html(pageCount);
}

function updateExternalReviewers() {
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
    fetch('/annotation/reviewer', {
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

window.updateExternalReviewers = updateExternalReviewers;

function markCommentRead(commentUuid) {
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

window.markCommentRead = markCommentRead;

function deleteFromExternalReview() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#deleteReviewModal').modal('hide');

    const formData = new FormData($('#deleteFromExternalReviewForm')[0]);
    fetch('/external-comment', {
        method: 'DELETE',
        body: formData,
    })
        .then((res) => {
            if (res.status === 200) {
                const index = annotations.findIndex((anno) => anno.observation_uuid.toString() === formData.get('uuid'));
                delete comments[formData.get('uuid')];
                annotations[index].comment = '';
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

window.deleteFromExternalReview = deleteFromExternalReview;

function updateAnnotation() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#editVarsAnnotationModal').modal('hide');
    const formData = new FormData($('#updateAnnotationForm')[0]);
    fetch('/vars/annotation', {
        method: 'PATCH',
        body: formData,
    })
        .then((result) => {
            if (result.status === 204) {
                const index = annotations.findIndex((anno) => anno.observation_uuid === formData.get('observation_uuid'));
                for (const pair of formData.entries()){
                    annotations[index][pair[0].replace('-', '_')] = pair[1];
                }
                updateFlashMessages('Annotation successfully updated', 'success');
                updateHash();
            } else if (result.status === 304) {
                updateFlashMessages('No changes made', 'secondary');
            } else {
                updateFlashMessages('Failed to update annotation - please try again', 'danger');
            }
            $('#load-overlay').addClass('loader-bg-hidden');
            $('#load-overlay').removeClass('loader-bg');
        })
        .catch((err) => console.log(err));
}

window.updateAnnotation = updateAnnotation;

function saveScrollPosition(page) {
    const url = new URL(window.location.href);
    const index = url.hash.indexOf('pg=');
    const queryAndHash = `${url.search}${url.hash.substring(0, index)}pg=${page}`;
    sessionStorage.setItem(`scrollPos${queryAndHash}`, `${window.scrollY}`);
}

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    const queryAndHash = url.search + url.hash;
    let unread = false;
    let reviewer = null;

    autocomplete($('#editConceptName'), allConcepts);
    autocomplete($('#editUpon'), allConcepts);

    if (sessionStorage.getItem(`scrollPos${queryAndHash}`)) {
        window.scrollTo({
            top: 0,
            left: Number(sessionStorage.getItem(`scrollPos${queryAndHash}`)),
            behavior: 'instant',
        });
    }

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('sequence') || pair[0].includes('deployment')) {
            const param = pair[1].split(' ');
            sequences.push(param.pop());
        } else if (pair[0].includes('unread')) {
            unread = true;
        } else if (pair[0].includes('reviewer')) {
            reviewer = pair[1];
        }
    }

    updateHash();

    $('#prev-button').on('click', () => {
        setCurrentPage(parseInt(currentPage) - 1);
    });

    $('#next-button').on('click', () => {
        setCurrentPage(parseInt(currentPage) + 1);
    });

    if (url.pathname.includes('external-review')) {
        // external review page
        $('#changeExternalView').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
        });
        if (reviewer) {
            $('#title').html(`External Review List (${reviewer})`);
            document.title = `DARC Image Review | External Review List (${reviewer})`;
            $('#changeExternalView').html('View All');
            $('#changeExternalView').attr('href', '/external-review');
        } else if (unread) {
            $('#changeExternalView').html('View All');
            $('#changeExternalView').attr('href', '/external-review');
        } else {
            $('#changeExternalView').html('View Unread');
            $('#changeExternalView').attr('href', '/external-review?unread=true');
        }
    } else {
        // regular dive page
        $('#syncCTD').hide();
        $('#changeExternalView').hide();
    }

    $('#paginationSelect').on('change', () => {
        paginationLimit = $('#paginationSelect').val();
        pageCount = Math.ceil(annotationsToDisplay.length / paginationLimit);
        getPaginationNumbers();
        setCurrentPage(1);
        $('#totalPageNum').html(pageCount);
        $('#totalPageNumBottom').html(pageCount);
    });

    $('#imageFilterSelect').on('change', () => $('#imageFilterEntry').attr('placeholder', `Enter ${$('#imageFilterSelect').val().toLowerCase()}`));

    $('#sortSelect').on('change', () => {
        const hashList = window.location.hash.substring(1).split('&');
        hashList.shift();
        saveScrollPosition(currentPage);
        location.hash = `#sort=${$('#sortSelect').val()}&${hashList.join('&')}`;
    });
});

window.onbeforeunload = (e) => {
    const url = new URL(window.location.href);
    const queryAndHash = url.search + url.hash;
    sessionStorage.setItem(`scrollPos${queryAndHash}`, window.scrollY);
};

window.onhashchange = () => {
    updateHash();
};

// get the annotation data and add it to the modal
$(document).ready(function () {
    $('#editVarsAnnotationModal').on('show.bs.modal', function (e) {
        const annotation = $(e.relatedTarget).data('anno');
        const conceptNameField = $(this).find('#editConceptName');
        const uponField = $(this).find('#editUpon');

        conceptNameField.val(annotation.concept);
        uponField.val(annotation.upon);
        $(this).find('#editIdCert').val(annotation.identity_certainty);
        $(this).find('#editIdRef').val(annotation.identity_reference);
        $(this).find('#editComments').val(annotation.comment);
        $(this).find('#editObservationUuid').val(annotation.observation_uuid);

        conceptNameField.on('input', () => validateName(conceptNameField.val()));
        conceptNameField.on('change', () => validateName(conceptNameField.val()));
        uponField.on('input', () => validateName(uponField.val()));
        uponField.on('change', () => validateName(uponField.val()));

        document.getElementById("editGuidePhoto").options.length = 0; // clear options
        const guidePhotoSelect = $(this).find('#editGuidePhoto');
        for (const val of guidePhotoVals) { // append options back on with matching option selected
            const opt = $('<option/>', { value: val })
                .text(val)
                .prop('selected', annotation.guide_photo === val || val === '' && !annotation.guide_photo);
            opt.appendTo(guidePhotoSelect);
        }
    });

    $('#externalReviewModal').on('show.bs.modal', (e) => {
        currentAnnotation = $(e.relatedTarget).data('anno');
        $('#externalModalSubmitButton').prop('disabled', true);
        addReviewer(null);

        $('#externalObservationUuid').val(currentAnnotation.observation_uuid);
        $('#externalSequence').val(currentAnnotation.video_sequence_name);
        $('#externalScientificName').val(currentAnnotation.scientific_name);
        $('#externalTimestamp').val(currentAnnotation.recorded_timestamp);
        $('#externalImageUrl').val(currentAnnotation.image_url || currentAnnotation.frame_url);
        $('#externalVideoUrl').val(currentAnnotation.video_url);
        $('#externalAnnotator').val(currentAnnotation.annotator);
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

        // clear the reviewer list from the modal
        $('#reviewerList').empty();
    })

    $('#deleteReviewModal').on('show.bs.modal', function (e) {
        $('#externalDeleteTator').val($(e.relatedTarget).data('anno').scientific_name != null);
        $('#externalDeleteUuid').val($(e.relatedTarget).data('anno').observation_uuid);
    });
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
