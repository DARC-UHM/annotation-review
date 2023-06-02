const paginationNumbers = document.getElementById('pagination-numbers');
const nextButton = document.getElementById('next-button');
const prevButton = document.getElementById('prev-button');
const guidePhotoVals = ['1 best', '2 good', '3 okay', ''];
const paginationLimit = 25;
const pageCount = Math.ceil(annotations.length / paginationLimit);
let currentPage;

const appendPageNumber = (index) => {
    const pageNumber = document.createElement('button');
    pageNumber.className = 'pagination-number';
    pageNumber.innerHTML = index;
    pageNumber.setAttribute('page-index', index);
    pageNumber.setAttribute('aria-label', 'Page ' + index);
    paginationNumbers.appendChild(pageNumber);
};

const getPaginationNumbers = () => {
    for (let i = 1; i <= pageCount; i++) {
        appendPageNumber(i);
    }
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
};

const setCurrentPage = (pageNum) => {
    const prevRange = (pageNum - 1) * paginationLimit;
    const currRange = pageNum * paginationLimit;

    sessionStorage.setItem(`scrollPos${currentPage}`, window.scrollY);

    currentPage = pageNum;
    location.hash = "#pg=" + pageNum;

    if (sessionStorage.getItem(`scrollPos${currentPage}`)) {
        window.scrollTo({top: sessionStorage.getItem(`scrollPos${currentPage}`), left: 0, behavior: 'instant'});
    } else {
       window.scrollTo({top: 0, left: 0, behavior: 'instant'});
    }

    handleActivePageNumber();
    handlePageButtonsStatus();

    $('#annotationTable tbody').remove();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');

    annotations.forEach((annotation, index) => {
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
                                <input type="submit" class="editButton" value="Mark read">
                            </form>
                            `
                            : ''}
                        </div>
                        <div class="col values">
                            ${comments[annotation.observation_uuid].comment 
                            ? 
                            `${comments[annotation.observation_uuid].comment}
                            <br>
                            ${comments[annotation.observation_uuid].date_modified}`
                            :
                            '-'}<br>
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
                                onclick="updateReviewerName('${comments[annotation.observation_uuid].reviewer}')">
                                    Change reviewer
                            </button>
                            <br>
                            <button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${JSON.stringify(annotation)}'
                                data-bs-target="#deleteReviewModal" 
                                class="editButton" 
                                onclick="updateReviewerName('${comments[annotation.observation_uuid].reviewer}')">
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

function updateReviewerName(name) {
    $('#reviewerName').html(name);
}

autocomplete(document.getElementById('editConceptName'), allConcepts);
autocomplete(document.getElementById('editUpon'), allConcepts);

// load scroll position
document.addEventListener('DOMContentLoaded', function(event) {
    if (sessionStorage.getItem(`scrollPos${currentPage}`)) {
        window.scrollTo({top: sessionStorage.getItem(`scrollPos${currentPage}`), left: 0, behavior: 'instant'});
    }

    getPaginationNumbers();
    if (window.location.hash) {
      setCurrentPage(window.location.hash.substring(4));
    } else {
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

    document.querySelectorAll('.pagination-number').forEach((button) => {
        const pageIndex = Number(button.getAttribute('page-index'));
        if (pageIndex) {
            button.addEventListener('click', () => {
                setCurrentPage(pageIndex);
            });
        }
    });

    $('#annotationCount').html(annotations.length);
    $('#totalPageNum').html(pageCount);

    const sequences = [];
    const filter = [];
    let vesselName = null;
    const url = new URL(window.location.href);

    for (let pair of url.searchParams.entries()) {
        if (pair[0].includes('sequence')) {
            const param = pair[1].split(' ');
            sequences.push(param.pop());
            if (!vesselName) {
                vesselName = param.join(' ');
            }
        } else {
            filter.push(pair[0]);
            filter.push(pair[1]);
        }
    }
    $('#vesselName').html(vesselName || 'Annotations Added for External Review');
    $('#sequenceList').html(sequences.join(', '));
    if (filter.length > 0) {
        $('#sequenceList').append(`<br><span class="small">Filtered by ${filter.join(': ')}</span>`);
    }

    $('#editModalSubmitButton').on('click', () => {
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        $('#editModal').modal('hide');
    });

    $('#externalModalSubmitButton').on('click', () => {
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        $('#externalReviewModal').modal('hide');
    });

    $('#externalModalDeleteButton').on('click', () => {
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        $('#externalModalDeleteButton').modal('hide');
    });
});

window.onbeforeunload = function(e) {
    sessionStorage.setItem(`scrollPos${currentPage}`, window.scrollY);
};

window.onhashchange = () => {
    const hashNum = Number(location.hash.substring(4));
    if (currentPage !== hashNum) {
        setCurrentPage(hashNum);
    }
}

// get the annotation data and add it to the modal
$(document).ready(function () {
    const url = new URL(window.location.href);

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

        $('#editUrl').val(url);
    });

    $('#externalReviewModal').on('show.bs.modal', function (e) {
        const annotation = $(e.relatedTarget).data('anno');
        const phylum = annotation.phylum.toLowerCase();
        console.log(phylum)
        const recommendedReviewers = reviewers.filter((obj) => {
            console.log(obj.phylum)
            return obj.phylum.toLowerCase().includes(phylum);
        });
        reviewerList(document.getElementById('reviewerNameButton'), recommendedReviewers);

        $('#externalUrl').val(url);
        $('#externalObservationUuid').val(annotation.observation_uuid);
        $('#externalSequence').val(annotation.video_sequence_name);
        $('#externalTimestamp').val(annotation.recorded_timestamp);
        $('#externalImageUrl').val(annotation.image_url);
        $('#externalConcept').val(annotation.concept);
        $('#externalVideoUrl').val(annotation.video_url);
        $('#externalAnnotator').val(annotation.annotator);
        $('#externalLat').val(annotation.lat);
        $('#externalLong').val(annotation.long);
        $('#externalDepth').val(annotation.depth);
    });

    $('#deleteReviewModal').on('show.bs.modal', function (e) {
        $('#externalDeleteUrl').val(url);
        $('#externalDeleteUuid').val($(e.relatedTarget).data('anno').observation_uuid);
    });
});
