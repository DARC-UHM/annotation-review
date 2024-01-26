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
                                    data-anno="${JSON.stringify(localization)}" 
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
                : `<span
                                        class="position-absolute tator-box"
                                        style="top: ${localization.points[0][1] * 100}%; left: ${localization.points[0][0] * 100}%; width: ${localization.dimensions[0] * 100}%; height: ${localization.dimensions[1] * 100}%;"
                                    ></span>`
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

function updateHash() {
    const url = new URL(window.location.href);
    const hash = url.hash.slice(1);
    const filterPairs = hash.split('&');
    const filter = {};

    localizationsToDisplay = localizations;

    filterPairs.pop(); // pop page number

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
    const deployments = [];
    const url = new URL(window.location.href);
    const queryAndHash = url.search + url.hash;

    for (const pair of url.searchParams.entries()) { // the only search params we expect here are deployments
        deployments.push(pair[1]);
    }

    $('#deploymentList').html(deployments.join(', '));

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
        pageCount = Math.ceil(annotationsToDisplay.length / paginationLimit);
        getPaginationNumbers();
        setCurrentPage(1);
        $('#totalPageNum').html(pageCount);
        $('#totalPageNumBottom').html(pageCount);
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


// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
