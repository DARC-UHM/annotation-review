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
                        <div class="col">
                            Concept:
                        </div>
                        <div class="col values">
                            ${annotation.concept}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            ID Certainty:<br>
                        </div>
                        <div class="col values">
                            ${annotation.identity_certainty ? annotation.identity_certainty : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            ID Reference:<br>
                        </div>
                        <div class="col values">
                            ${annotation.identity_reference ? annotation.identity_reference : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            Upon:<br>
                        </div>
                        <div class="col values">
                            ${annotation.upon ? annotation.upon : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            Comments:<br>
                        </div>
                        <div class="col values">
                            ${annotation.comment ? annotation.comment : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            Guide Photo:<br>
                        </div>
                        <div class="col values">
                            ${annotation.guide_photo ? annotation.guide_photo : '-'}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            Timestamp:
                        </div>
                        <div class="col values">
                            ${annotation.recorded_timestamp}<br>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            Video Sequence:
                        </div>
                        <div class="col values">
                            ${annotation.video_sequence_name}<br>
                        </div>
                    </div>
                    <button type="button" data-bs-toggle="modal" data-anno='${ JSON.stringify(annotation) }' data-bs-target="#editModal" class="editButton mt-2">Edit</button>
                </td>
                <td class="text-center">
                    <a href="${annotation.image_url}" target="_blank">
                        <img src="${annotation.image_url}" style="width: 500px;"/>
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
    $('#modalSubmitButton')[0].disabled = disabled;
}

autocomplete(document.getElementById('editConceptName'), allConcepts);
autocomplete(document.getElementById('editUpon'), allConcepts);

// load scroll position
document.addEventListener('DOMContentLoaded', function(event) {
    if (sessionStorage.getItem(`scrollPos${currentPage}`)) {
        window.scrollTo({top: sessionStorage.getItem(`scrollPos${currentPage}`), left: 0, behavior: 'instant'});
    }

    getPaginationNumbers();
    setCurrentPage(1);

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
    let vesselName = null;
    const url = new URL(window.location.href);
    url.searchParams.forEach((param) => {
        param = param.split(' ');
        sequences.push(param.pop());
        if (!vesselName) {
            vesselName = param.join(' ');
        }
    });
    $('#vesselName').html(vesselName);
    $('#sequenceList').html(sequences.join(', '));
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
    $('#editModal').on('show.bs.modal', function (e) {
        const annotation = $(e.relatedTarget).data('anno');
        const conceptNameField = $(this).find('#editConceptName');
        const uponField = $(this).find('#editUpon');

        conceptNameField.val(annotation.concept);
        uponField.val(annotation.upon);
        $(this).find('#editIdCert').val(annotation.identity_certainty);
        $(this).find('#editIdRef').val(annotation.identity_reference);
        $(this).find('#editComments').val(annotation.comment);
        $(this).find('#observationUuid').val(annotation.observation_uuid);

        conceptNameField.on('input', () => { validateName(conceptNameField.val()) });
        uponField.on('input', () => { validateName(uponField.val()) });

        document.getElementById("editGuidePhoto").options.length = 0; // clear options
        const guidePhotoSelect = $(this).find('#editGuidePhoto');
        for (val of guidePhotoVals) { // append options back on with matching option selected
            const opt = $('<option/>', { value: val })
                .text(val)
                .prop('selected', annotation.guide_photo === val || val === '' && !annotation.guide_photo);
            opt.appendTo(guidePhotoSelect);
        }
    });
});