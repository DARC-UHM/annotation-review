import { autocomplete } from '../../util/autocomplete.js';
import { reviewerList } from '../../util/reviewer-list.js';
import { updateFlashMessages } from '../../util/updateFlashMessages.js';

const knownAnnotators = {
    22: 'Jeff Drazen',
    24: 'Meagan Putts',
    25: 'Sarah Bingo',
    332: 'Nikki Cunanan',
    433: 'Aaron Judah',
};

let currentPage = 1;
let pageCount;
let paginationLimit = 25;
let localizationsToDisplay = localizations;
let currentLocalization;

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

    localizationsToDisplay.forEach((localization, index) => {
        if (index >= prevRange && index < currRange) {
            $('#annotationTable').find('tbody').append(`
                <tr>
                    <td class="ps-5">
                        <div class="row">
                            <div class="col-5">
                                Scientific Name:
                            </div>
                            <div class="col values">
                                ${localization.scientific_name}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Count:
                            </div>
                            <div class="col values">
                                ${localization.count}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Annotator:
                            </div>
                            <div class="col values">
                                ${knownAnnotators[localization.annotator] || `Unknown annotator (#${localization.annotator})`}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Attracted:
                            </div>
                            <div class="col values">
                                ${localization.attracted}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Qualifier:
                            </div>
                            <div class="col values">
                                ${localization.qualifier}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Categorical Abundance:
                            </div>
                            <div class="col values">
                                ${localization.categorical_abundance}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Reason:
                            </div>
                            <div class="col values">
                                ${localization.reason}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Tentative ID:
                            </div>
                            <div class="col values">
                                ${localization.tentative_id}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Identification Remarks:
                            </div>
                            <div class="col values">
                                ${localization.identification_remarks}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Identified By:
                            </div>
                            <div class="col values">
                                ${localization.identified_by}<br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-5">
                                Notes:
                            </div>
                            <div class="col values">
                                ${localization.notes}<br>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-5">
                                <a class="editButton" href="https://cloud.tator.io/26/annotation/${localization.media_id}?frame=${localization.frame}" target="_blank">View on Tator</a>
                            </div>
                            <div class="col">
                                <button 
                                    type="button" 
                                    data-bs-toggle="modal" 
                                    data-anno='${JSON.stringify(localization)}' 
                                    data-bs-target="#externalReviewModal" 
                                    class="editButton">
                                        Add to external review
                                </button>
                            </div>
                        </div>
                    </td>
                    <td class="text-center">
                        <a href="${localization.frame_url}" target="_blank">
                            <div id="${localization.id}_image" class="position-relative" style="width: 580px;">
                                <img src="${localization.frame_url}" style="width: 580px;" alt="${localization.scientific_name}"/>
                                <div id="${localization.id}_overlay">
                                ${localization.type === 49
                                    ? localization.points.map((point) => {
                                        return `<span class="position-absolute tator-dot" style="top: ${point[1] * 100}%; left: ${point[0] * 100}%;"></span>`;
                                    }).join('')
                                    : localization.points.map((point, index) => {
                                        if (index < 1) {
                                            return `<span
                                                class="position-absolute tator-box"
                                                style="top: ${point[1] * 100}%; left: ${point[0] * 100}%; width: ${localization.dimensions[0] * 100}%; height: ${localization.dimensions[1] * 100}%;"
                                            ></span>`
                                        } else {
                                            return `<span class="position-absolute tator-dot" style="top: ${point[1] * 100}%; left: ${point[0] * 100}%;"></span>`;
                                        }
                                    }).join('')
                                }
                                </div>
                            </div>
                        </a>
                    </td>
                </tr>
            `);

            $(`#${localization.id}_overlay`).css('opacity', '0.5');
            $(`#${localization.id}_image`).hover((e) => {
                if (e.type === 'mouseenter') {
                    $(`#${localization.id}_overlay`).css('opacity', '1.0');
                } else if (e.type === 'mouseleave') {
                    $(`#${localization.id}_overlay`).css('opacity', '0.5');
                }
            });
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
}

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
        localizationsToDisplay = localizations;
        return;
    }
    tempKey = key.toLowerCase();
    if (tempKey === 'timestamp') {
        localizationsToDisplay = localizationsToDisplay.sort((a, b) => a.frame - b.frame);
        localizationsToDisplay = localizationsToDisplay.sort((a, b) => a.media_id - b.media_id);
    } else {
        // move all records missing specified property to bottom
        let filtered = localizationsToDisplay.filter((localization) => localization[tempKey]);
        filtered = filtered.sort((a, b) => (a[tempKey] > b[tempKey]) ? 1 : ((b[tempKey] > a[tempKey]) ? -1 : 0));
        localizationsToDisplay = filtered.concat(localizationsToDisplay.filter((anno) => !anno[tempKey]));
    }
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
    const phylum = currentLocalization.phylum.toLowerCase();
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
    const deployments = [];

    localizationsToDisplay = localizations;

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

    for (const pair of url.searchParams.entries()) { // the only search params we expect here are deployments
        deployments.push(pair[1]);
    }

    $('#deploymentList').empty();
    $('#deploymentList').html(deployments.join(', '));
    $('#deploymentList').append(`<div id="filterList" class="small mt-2">Filters: ${Object.keys(filter).length ? '' : 'None'}</div>`);

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
                        <option>Notes</option>
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
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['phylum']?.toLowerCase() === filter['phylum'].toLowerCase());
    }
    if (filter['class']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['class']?.toLowerCase() === filter['class'].toLowerCase());
    }
    if (filter['order']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['order']?.toLowerCase() === filter['order'].toLowerCase());
    }
    if (filter['family']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['family']?.toLowerCase() === filter['family'].toLowerCase());
    }
    if (filter['genus']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['genus']?.toLowerCase() === filter['genus'].toLowerCase());
    }
    if (filter['species']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['species']?.toLowerCase() === filter['species'].toLowerCase().replaceAll('%20', ' '));
    }
    if (filter['certainty']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['identity_certainty']?.toLowerCase().includes(filter['certainty'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['notes']) {
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['notes']?.toLowerCase().includes(filter['notes'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['annotator']) {
        const annotatorNum = Object.keys(knownAnnotators).find((key) => knownAnnotators[key].toLowerCase().includes(filter['annotator'].toLowerCase().replaceAll('%20', ' ')));
        localizationsToDisplay = localizationsToDisplay.filter((anno) => anno['annotator'] === parseInt(annotatorNum));
    }

    if (!localizationsToDisplay.length) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    pageCount = Math.ceil(localizationsToDisplay.length / paginationLimit);

    getPaginationNumbers();

    if (window.location.hash.includes('pg=')) {
        setCurrentPage(parseInt(window.location.hash.slice(window.location.hash.indexOf('pg=')).substring(3)));
    } else {
        location.replace(`#sort=Default&pg=1`); // to prevent extra pages without hash of page num when back button pressed
        setCurrentPage(1);
    }

    $('#totalImageCount').html(localizationsToDisplay.length);
    $('#totalImageCountBottom').html(localizationsToDisplay.length);
    $('#totalPageNum').html(pageCount);
    $('#totalPageNumBottom').html(pageCount);
}

function saveScrollPosition(page) {
    const url = new URL(window.location.href);
    const index = url.hash.indexOf('pg=');
    const queryAndHash = `${url.search}${url.hash.substring(0, index)}pg=${page}`;
    sessionStorage.setItem(`scrollPos${queryAndHash}`, `${window.scrollY}`);
}

document.addEventListener('DOMContentLoaded', () => {
    const url = new URL(window.location.href);
    const queryAndHash = url.search + url.hash;

    if (sessionStorage.getItem(`scrollPos${queryAndHash}`)) {
        window.scrollTo({
            top: 0,
            left: Number(sessionStorage.getItem(`scrollPos${queryAndHash}`)),
            behavior: 'instant',
        });
    }

    updateHash();

    $('#prev-button').on('click', () => {
        setCurrentPage(parseInt(currentPage) - 1);
    });

    $('#next-button').on('click', () => {
        setCurrentPage(parseInt(currentPage) + 1);
    });

    $('#paginationSelect').on('change', () => {
        paginationLimit = $('#paginationSelect').val();
        pageCount = Math.ceil(localizationsToDisplay.length / paginationLimit);
        getPaginationNumbers();
        setCurrentPage(1);
        $('#totalPageNum').html(pageCount);
        $('#totalPageNumBottom').html(pageCount);
    });

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

$(document).ready(function () {
    $('#externalReviewModal').on('show.bs.modal', (e) => {
        currentLocalization = $(e.relatedTarget).data('anno');
        console.log(currentLocalization);
        $('#externalModalSubmitButton').prop('disabled', true);
        addReviewer(null);

        $('#externalId').val(currentLocalization.id);
        $('#externalScientificName').val(currentLocalization.scientific_name);
        $('#externalImageUrl').val(currentLocalization.image_url);
        $('#externalAnnotator').val(knownAnnotators[currentLocalization.annotator]);
        $('#externalLat').val(currentLocalization.lat);
        $('#externalLong').val(currentLocalization.long);
        $('#externalDepth').val(currentLocalization.depth);
    });

    $('#externalReviewModal').on('hide.bs.modal', () => {
        currentLocalization = null;
        totalReviewers = 0;
        reviewerIndex = 0;

        // clear the reviewer list from the modal
        $('#reviewerList').empty();
    })

    $('#deleteReviewModal').on('show.bs.modal', function (e) {
        $('#externalDeleteUuid').val($(e.relatedTarget).data('anno').observation_uuid);
    });
});


// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
