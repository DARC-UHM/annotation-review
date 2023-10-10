const paginationNumbers = document.getElementById('pagination-numbers');
const nextButton = document.getElementById('next-button');
const prevButton = document.getElementById('prev-button');
const guidePhotoVals = ['1 best', '2 good', '3 okay', ''];

let currentPage;
let pageCount;
let paginationLimit = 25;
let annotationsToDisplay = annotations;
let tempAnnotations;
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
        paginationNumbers.appendChild(pageNumber);
    }
    document.querySelectorAll('.pagination-number').forEach((button) => {
        const pageIndex = Number(button.getAttribute('page-index'));
        if (pageIndex) {
            button.addEventListener('click', () => {
                setCurrentPage(pageIndex);
            });
        }
    });
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

    sessionStorage.setItem(`scrollPos${currentPage}`, window.scrollY);

    currentPage = pageNum;
    location.hash = `#pg=${pageNum}`;

    if (sessionStorage.getItem(`scrollPos${currentPage}`) && pageNum !== 1) {
        window.scrollTo({top: sessionStorage.getItem(`scrollPos${currentPage}`), left: 0, behavior: 'instant'});
    } else {
       window.scrollTo({top: 0, left: 0, behavior: 'instant'});
    }

    handleActivePageNumber();
    handlePageButtonsStatus();

    $('#annotationTable tbody').remove();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');

    annotationsToDisplay.forEach((annotation, index) => {
        if (index >= prevRange && index < currRange) {
            $('#annotationTable').find('tbody').append(`
            <tr>
                <td class="ps-5">
                    <div class="row">
                        <div class="col-4">
                            Concept:
                        </div>
                        <div class="col values">
                            ${annotation.concept}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Annotator:
                        </div>
                        <div class="col values">
                            ${annotation.annotator}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            ID certainty:<br>
                        </div>
                        <div class="col values">
                            ${annotation.identity_certainty ? annotation.identity_certainty : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            ID reference:<br>
                        </div>
                        <div class="col values">
                            ${annotation.identity_reference ? annotation.identity_reference : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Upon:<br>
                        </div>
                        <div class="col values">
                            ${annotation.upon ? annotation.upon : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Comments:<br>
                        </div>
                        <div class="col values">
                            ${annotation.comment ? annotation.comment : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Guide photo:<br>
                        </div>
                        <div class="col values">
                            ${annotation.guide_photo ? annotation.guide_photo : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Depth:
                        </div>
                        <div class="col values">
                            ${annotation.depth || '?'} m<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Timestamp:
                        </div>
                        <div class="col values">
                            ${annotation.recorded_timestamp}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-4">
                            Video sequence:
                        </div>
                        <div class="col values">
                            ${annotation.video_sequence_name}<br>
                        </div>
                    </div>
                    ${ Object.keys(comments).includes(annotation.observation_uuid) ?
                    `
                    <div class="row mt-2">
                        <div class="col-4">
                            Reviewer comments:<br>
                            ${comments[annotation.observation_uuid].unread ?
                            `<form action="/mark-comment-read" method="post">
                                <input type="hidden" name="uuid" value="${annotation.observation_uuid}">
                                <input type="hidden" name="url" value="${window.location.href}">
                                <input type="hidden" name="reviewer" value="${comments[annotation.observation_uuid].reviewer}">
                                <input type="submit" class="editButton" value="Mark read">
                            </form>
                            `
                            : ''}
                        </div>
                        <div class="col values">
                            ${comments[annotation.observation_uuid].reviewer_comments 
                            ? 
                            `${comments[annotation.observation_uuid].reviewer_comments.map(item => {
                                return item.comment 
                                    ? `${item.comment.length
                                        ? `${item.comment}<br><span class="small fw-normal">- ${item.reviewer} ${item.date_modified}</span>`
                                        : 'N/A'}<br><br>`
                                    : `<span class="fw-normal">Awaiting comment from ${item.reviewer}</span><br><br>`;
                            }).join('')}`
                            :
                            '-'}
                        </div>
                    </div>
                    ` : '' }
                    <div class="row mt-2">
                        <div class="col-4">
                            <button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${ JSON.stringify(annotation) }' 
                                data-bs-target="#editModal" 
                                class="editButton">
                                    Edit annotation
                            </button>
                            <br>
                            <a class="editButton" href="${annotation.video_url}" target="_blank">See video</a>
                            <br>
                        </div>
                        <div class="col values">
                            ${ !Object.keys(comments).includes(annotation.observation_uuid) ?
                            `<button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${ JSON.stringify(annotation) }' 
                                data-bs-target="#externalReviewModal" 
                                class="editButton">
                                    Add to external review
                            </button>`
                                :
                            `<button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${ JSON.stringify(annotation) }'
                                data-bs-target="#externalReviewModal" 
                                class="editButton" 
                                onclick="updateReviewerName('${annotation.observation_uuid}')">
                                    Change reviewer
                            </button>
                            <br>
                            <button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${JSON.stringify(annotation)}'
                                data-bs-target="#deleteReviewModal" 
                                class="editButton" 
                                onclick="updateReviewerName('${annotation.observation_uuid}')">
                                    Delete from external review
                            </button>`
                            }
                        </div>
                    </div>
                </td>
                <td class="text-center">
                    <a href="${annotation.image_url}" target="_blank">
                        <img src="${annotation.image_url}" style="width: 580px;"/>
                    </a>
                </td>
            </tr>
            `);
        }
    });
};

const disableButton = (button) => {
    button.classList.add('disabled');
    button.setAttribute('disabled', true);
};

const enableButton = (button) => {
    button.classList.remove('disabled');
    button.removeAttribute('disabled');
};

const handlePageButtonsStatus = () => {
    if (currentPage === 1) {
        disableButton(prevButton);
    } else {
        enableButton(prevButton);
    }
    if (pageCount === currentPage) {
        disableButton(nextButton);
    } else {
        enableButton(nextButton);
    }
};

function validateName(name) {
    let disabled = false;
    if (name && !allConcepts.includes(name)) {
        disabled = true;
    }
    $('#editModalSubmitButton')[0].disabled = disabled;
}

function updateReviewerName(uuid) {
    const reviewerComments = comments[uuid].reviewer_comments;
    $('#reviewerName1').html(reviewerComments[0].reviewer);
    for (let i = 1; i < reviewerComments.length; i++) {
        addReviewer(reviewerComments[i].reviewer, false);
    }
}

// remove filter from url parameter and reload the page
function removeFilter(key, value) {
    const url = new URL(window.location.href);
    const index = url.toString().indexOf(key);
    window.location.href = `${url.toString().substring(0, index - 1)}${url.toString().substring(index + key.length + value.length + 1)}`;
}

function showAddFilter() {
    $('#addFilterRow').show();
    $('#addFilterButton').hide();
}

// add filter and refresh page
function addFilter() {
    const url = new URL(window.location.href);
    const index = url.toString().indexOf('#');
    const filterKey = $('#imageFilterSelect').val().toLowerCase();
    const filterVal = $('#imageFilterEntry').val();
    window.location.href = `${url.toString().substring(0, index)}&${filterKey}=${filterVal}#pg=1`;
}

function sortBy(key) {
    let tempKey;
    if (key === 'Default') {
        annotationsToDisplay = [...tempAnnotations]; // reset to default sort
        setCurrentPage(1);
        return;
    }
    if (key === 'Timestamp') {
        tempKey = 'recorded_timestamp';
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
    setCurrentPage(1);
}

function removeReviewer(num) {
    $(`#reviewerRow${num}`).remove();
    totalReviewers--;
}

function addReviewer(reviewerName, firstReviewer) {
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
                ${firstReviewer
                    ? `<button id="plusButton" type="button" class="plusButton" onClick="addReviewer()">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-plus"
                             viewBox="0 0 16 16">
                            <path
                                d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                        </svg>
                    </button>`
                    : `<button id="xButton${thisReviewerIndex}" type="button" class="xButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                        </svg>
                    </button>`
                }
            </div>
        </div>
    `);
    $(`#xButton${thisReviewerIndex}`).on('click', () => removeReviewer(thisReviewerIndex));
    reviewerList($(`#reviewerName${thisReviewerIndex}Button`), recommendedReviewers, $(`#reviewerName${thisReviewerIndex}`));
}

function loadReviewers() {
    // loads reviewers to form fields on submit
    const reviewers = [];
    for (const item of document.getElementsByClassName('reviewerName')) {
        reviewers.push(item.innerHTML);
    }
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#externalReviewModal').modal('hide');
    $('#externalReviewers').val(JSON.stringify(reviewers));
}

document.addEventListener('DOMContentLoaded', function(event) {
    const sequences = [];
    const filter = {};
    const url = new URL(window.location.href);
    let vesselName;

    autocomplete(document.getElementById('editConceptName'), allConcepts);
    autocomplete(document.getElementById('editUpon'), allConcepts);

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('sequence')) {
            const param = pair[1].split(' ');
            sequences.push(param.pop());
            if (!vesselName) {
                vesselName = param.join(' ');
            }
        } else {
            filter[pair[0]] = pair[1];
        }
    }
    if (filter['phylum']) {
        annotationsToDisplay = annotations.filter((anno) => anno['phylum']?.toLowerCase() === filter['phylum'].toLowerCase());
    }
    if (filter['class']){
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['class']?.toLowerCase() === filter['class'].toLowerCase());
    }
    if (filter['order']){
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['order']?.toLowerCase() === filter['order'].toLowerCase());
    }
    if (filter['family']){
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['family']?.toLowerCase() === filter['family'].toLowerCase());
    }
    if (filter['genus']){
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['genus']?.toLowerCase() === filter['genus'].toLowerCase());
    }
    if (filter['species']){
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['species']?.toLowerCase() === filter['species'].toLowerCase());
    }
    if (filter['comment']){
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['comment']?.toLowerCase().includes(filter['comment'].toLowerCase()));
    }

    tempAnnotations = [...annotationsToDisplay]; // save these so we can go back to default sort later

    if (!annotationsToDisplay.length) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    pageCount = Math.ceil(annotationsToDisplay.length / paginationLimit);

    getPaginationNumbers();
    if (window.location.hash) {
      setCurrentPage(window.location.hash.substring(4));
    } else {
      location.replace(`#pg=1`); // to prevent extra pages without hash of page num when back button pressed
      setCurrentPage(1);
    }

    if (sessionStorage.getItem(`scrollPos${currentPage}`)) {
        window.scrollTo({top: sessionStorage.getItem(`scrollPos${currentPage}`), left: 0, behavior: 'instant'});
    }

    prevButton.addEventListener("click", () => {
        setCurrentPage(currentPage - 1);
    });

    nextButton.addEventListener("click", () => {
        setCurrentPage(currentPage + 1);
    });

    $('#annotationCount').html(annotationsToDisplay.length);
    $('#annotationCountBottom').html(annotationsToDisplay.length);
    $('#totalPageNum').html(pageCount);
    $('#totalPageNumBottom').html(pageCount);
    $('#sequenceList').html(sequences.join(', '));

    if (!vesselName) {
        // external review page
        if (filter['unread']) {
            $('#vesselName').html('External Review List (Unread)');
            document.title = 'DARC Image Review | External Review List (Unread Comments)';
            $('#changeExternalView').html('View All');
            $('#changeExternalView').attr('href', '/external-review');
        } else {
            $('#vesselName').html('External Review List (All)');
            document.title = 'DARC Image Review | External Review List (All)';
            $('#changeExternalView').html('View Unread');
            $('#changeExternalView').attr('href', '/external-review?unread=true');
        }
    } else {
        // regular dive page
        $('#syncCTD').hide();
        $('#changeExternalView').hide();
        $('#vesselName').html(vesselName);
        $('#sequenceList').append(`<br><span class="small">Filters: ${Object.keys(filter).length ? '' : 'None'}</span>`);
        for (const key of Object.keys(filter)) {
            $('#sequenceList').append(`
                <span class="small filter-pill position-relative">
                    ${key[0].toUpperCase()}${key.substring(1)}: ${filter[key]}
                    <button type="button" class="position-absolute filter-x" onclick="removeFilter('${key}', '${filter[key]}')">×</button>
                </span>
            `);
        }
        $('#sequenceList').append(`
            <span id="addFilterRow" class="small ms-3" style="display: none;">
                <form onsubmit="event.preventDefault(); addFilter()" class="d-inline-block">
                    <span class="position-relative">
                        <select id="imageFilterSelect">
                            <option>Phylum</option>
                            <option>Class</option>
                            <option>Order</option>
                            <option>Family</option>
                            <option>Genus</option>
                            <option>Species</option>
                            <option>Comment</option>
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
    }

    $('#editModalSubmitButton').on('click', () => {
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        $('#editModal').modal('hide');
    });

    $('#externalModalDeleteButton').on('click', () => {
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        $('#externalModalDeleteButton').modal('hide');
    });

    $('#paginationSelect').on('change', () => {
        paginationLimit = $('#paginationSelect').val();
        pageCount = Math.ceil(annotationsToDisplay.length / paginationLimit);
        getPaginationNumbers();
        setCurrentPage(1);
        $('#totalPageNum').html(pageCount);
        $('#totalPageNumBottom').html(pageCount);
    });

    $('#imageFilterSelect').on('change', () => $('#imageFilterEntry').attr('placeholder', `Enter ${$('#imageFilterSelect').val().toLowerCase()}`));

    $('#sortSelect').on('change', () => sortBy($('#sortSelect').val()));
});

window.onbeforeunload = (e) => {
    sessionStorage.setItem(`scrollPos${currentPage}`, window.scrollY);
};

window.onhashchange = () => {
    const hashNum = Number(location.hash.substring(4));
    if (currentPage !== hashNum) {
        setCurrentPage(hashNum);
    }
};

// get the annotation data and add it to the modal
$(document).ready(function () {

    $('#editModal').on('show.bs.modal', function (e) {
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
        for (val of guidePhotoVals) { // append options back on with matching option selected
            const opt = $('<option/>', { value: val })
                .text(val)
                .prop('selected', annotation.guide_photo === val || val === '' && !annotation.guide_photo);
            opt.appendTo(guidePhotoSelect);
        }

        $('#editUrl').val(window.location.href);
    });

    $('#externalReviewModal').on('show.bs.modal', (e) => {
        currentAnnotation = $(e.relatedTarget).data('anno');
        $('#externalModalSubmitButton').prop('disabled', true);
        addReviewer(null, true);

        $('#externalUrl').val(window.location.href);
        $('#externalObservationUuid').val(currentAnnotation.observation_uuid);
        $('#externalSequence').val(currentAnnotation.video_sequence_name);
        $('#externalTimestamp').val(currentAnnotation.recorded_timestamp);
        $('#externalImageUrl').val(currentAnnotation.image_url);
        $('#externalConcept').val(currentAnnotation.concept);
        $('#externalVideoUrl').val(currentAnnotation.video_url);
        $('#externalAnnotator').val(currentAnnotation.annotator);
        $('#externalIdRef').val(`${currentAnnotation.video_sequence_name.slice(-2)}:${currentAnnotation.identity_reference}`);
        $('#externalLat').val(currentAnnotation.lat);
        $('#externalLong').val(currentAnnotation.long);
        $('#externalDepth').val(currentAnnotation.depth);
    });

    $('#externalReviewModal').on('hide.bs.modal', () => {
        currentAnnotation = null;
        totalReviewers = 0;
        reviewerIndex = 0;

        // clear the reviewer list from the modal
        $('#reviewerList').empty();
    })

    $('#deleteReviewModal').on('show.bs.modal', function (e) {
        $('#externalDeleteUrl').val(window.location.href);
        $('#externalDeleteUuid').val($(e.relatedTarget).data('anno').observation_uuid);
    });
});
