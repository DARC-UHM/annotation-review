import { autocomplete, removeAllLists, removeAutocomplete } from '../util/autocomplete.js';
import { updateFlashMessages } from '../util/updateFlashMessages.js';
import { varsAnnotationTableRow } from './vars-annotation-table-row.js';
import { tatorLocalizationRow } from './tator-localization-table-row.js';

const guidePhotoVals = ['1 best', '2 good', '3 okay', ''];
const sequences = [];

for (const annotation of annotations) {
    if (!annotation.associations) {
        continue;
    }
    for (const association of annotation.associations) {
        if (['guide-photo', 'upon'].includes(association.link_name)) {
            annotation[association.link_name.replace('-', '_')] = association.to_concept;
        } else if (['identity-certainty', 'identity-reference', 'comment'].includes(association.link_name)) {
            annotation[association.link_name.replace('-', '_')] = association.link_value;
        }
    }
}

let currentPage = 1;
let pageCount;
let paginationLimit = 25;
let annotationsToDisplay = [...annotations];

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
            if (Object.keys(annotation).includes('scientific_name') && annotation.scientific_name) { // this is a tator localization
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

function validateName(name, nameList, button) {
    let disabled = false;
    if (name && !nameList.includes(name)) {
        disabled = true;
    }
    button.disabled = disabled;
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
    $('#imageFilterEntry').on('keyup', (e) => {
        if (e.key === 'Enter') {
            addFilter();
        }
    });
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
        annotationsToDisplay = [...annotations];
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
        switch (tempKey) {
            case 'phylum':
                filtered = filterAndSort(filtered, 'tentative_id');
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                filtered = filterAndSort(filtered, 'order');
                filtered = filterAndSort(filtered, 'class');
                filtered = filterAndSort(filtered, 'phylum');
                break;
            case 'class':
                filtered = filterAndSort(filtered, 'tentative_id');
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                filtered = filterAndSort(filtered, 'order');
                filtered = filterAndSort(filtered, 'class');
                break;
            case 'order':
                filtered = filterAndSort(filtered, 'tentative_id');
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                filtered = filterAndSort(filtered, 'order');
                break;
            case 'family':
                filtered = filterAndSort(filtered, 'tentative_id');
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                break;
            case 'genus':
                filtered = filterAndSort(filtered, 'tentative_id');
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                break;
            default:
                filtered = filtered.sort((a, b) => (a[tempKey].toLowerCase() > b[tempKey].toLowerCase()) ? 1 : ((b[tempKey].toLowerCase() > a[tempKey].toLowerCase()) ? -1 : 0));
                break;
        }
    }
    annotationsToDisplay = filtered.concat(annotationsToDisplay.filter((anno) => !anno[tempKey]));

    $('#sortSelect').val(key);
}

const filterAndSort = (list, key) => {
    let filtered = list.filter((anno) => anno[key]);
    filtered = filtered.sort((a, b) => (a[key] > b[key]) ? 1 : ((b[key] > a[key]) ? -1 : 0));
    return filtered.concat(list.filter((anno) => !anno[key]));
}

function updateFilterHint() {
    $('#imageFilterEntry').attr('placeholder', `Enter ${$('#imageFilterSelect').val().toLowerCase().replaceAll('_', ' ')}`);
}

window.updateFilterHint = updateFilterHint;

// exporting so we can call from the review modal js
export function updateHash() {
    const url = new URL(window.location.href);
    const hash = url.hash.slice(1);
    const filterPairs = hash.split('&');
    const filter = {};

    annotationsToDisplay = [...annotations];

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
    $('#sequenceList').html(sequences.join(', '));
    $('#sequenceList').append(`<div id="filterList" class="small mt-2">Filters: ${Object.keys(filter).length ? '' : 'None'}</div>`);

    for (const key of Object.keys(filter)) {
        $('#filterList').append(`
            <span class="small filter-pill position-relative">
                <span style="text-transform: capitalize;">${key.replaceAll('_', ' ')}:</span> ${filter[key].replaceAll('%20', ' ')}
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
                        <option>Annotator</option>
                        <option value="comment">Comment (VARS)</option>
                        <option value="concept">Concept (VARS)</option>
                        <option value="good_image">Good Image (Tator)</option>
                        <option value="id_certainty">ID Certainty (VARS)</option>
                        <option value="notes">Notes (Tator)</option>
                        <option value="scientific_name">Scientific Name (Tator)</option>
                        <option value="localization_type">Type (Tator)</option>
                        <option value="video_sequence">Video Sequence</option>
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
    if (filter['id_certainty']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['identity_certainty']?.toLowerCase().includes(filter['id_certainty'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['video_sequence']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['video_sequence_name']?.toLowerCase().includes(filter['video_sequence'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['comment']) { // VARS
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['comment']?.toLowerCase().includes(filter['comment'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['notes']) { // Tator
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['notes']?.toLowerCase().includes(filter['notes'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['scientific_name']) { // Tator
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['scientific_name']?.toLowerCase().includes(filter['scientific_name'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['concept']) { // VARS
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['concept']?.toLowerCase().includes(filter['concept'].toLowerCase().replaceAll('%20', ' ')));
    }
    if (filter['localization_type']) { // Tator
        const localizationType = filter.localization_type.toLowerCase().includes('box') ? 48 : 49;
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['all_localizations'][0].type === localizationType);
    }
    if (filter['good_image']) {
        annotationsToDisplay = annotationsToDisplay.filter((anno) => anno['good_image']);
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

async function deleteAssociation(associationUuid) {
    const res = await fetch(`/vars/association/${associationUuid}`, {
        method: 'DELETE',
    });
    if (res.ok) {
        return true;
    }
    updateFlashMessages('Failed to update annotation - please try again', 'danger');
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
    return false;
}

// vars
async function updateAnnotation() {
    event.preventDefault();
    const formData = new FormData($('#updateAnnotationForm')[0]);
    const associations = JSON.parse(formData.get('associations')) || [];
    const creations = [];
    const updates = [];
    const deletes = [];

    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#editVarsAnnotationModal').modal('hide');

    // check for concept name change
    if (formData.get('concept') !== formData.get('originalConcept')) {
        const res = await fetch('/vars/annotation-concept', {
            method: 'PATCH',
            body: formData,
        });
        if (res.ok) {
            updates.push('concept');
        } else {
            updateFlashMessages('Failed to update annotation - please try again', 'danger');
            $('#load-overlay').addClass('loader-bg-hidden');
            $('#load-overlay').removeClass('loader-bg');
            return;
        }
    }

        const associationsToCheck = ['upon', 'guide-photo', 'identity-certainty', 'identity-reference', 'comment'];

    // update current associations
    for (const association of associations) {
        if (associationsToCheck.includes(association.link_name)) {
            // remove from list of associations to check
            associationsToCheck.splice(associationsToCheck.indexOf(association.link_name), 1);
            if ((['identity-certainty', 'identity-reference', 'comment'].includes(association.link_name) && formData.get(association.link_name) !== association.link_value)
                || (['upon', 'guide-photo'].includes(association.link_name) && formData.get(association.link_name) !== association.to_concept)
            ) {
                if (formData.get(association.link_name) === '') {
                    // delete association
                    if (await deleteAssociation(association.uuid)) {
                        deletes.push(association.link_name.replace('-', ' '));
                    } else {
                        return;
                    }
                } else {
                    // update association
                    const associationFormData = new FormData();
                    associationFormData.append('uuid', association.uuid);
                    associationFormData.append('link_name', association.link_name);
                    if (['identity-certainty', 'identity-reference', 'comment'].includes(association.link_name)) {
                        associationFormData.append('link_value', formData.get(association.link_name));
                    } else {
                        associationFormData.append('to_concept', formData.get(association.link_name));
                    }
                    const res = await fetch('/vars/association', {
                        method: 'PATCH',
                        body: associationFormData,
                    });
                    if (res.ok) {
                        updates.push(association.link_name.replace('-', ' '));
                    } else {
                        updateFlashMessages('Failed to update annotation - please try again', 'danger');
                        $('#load-overlay').addClass('loader-bg-hidden');
                        $('#load-overlay').removeClass('loader-bg');
                    }
                }
            }
        }
    }

    // add new associations
    for (const field of associationsToCheck) {
        if (formData.get(field)) {
            const newAssociationFormData = new FormData();
            newAssociationFormData.append('observation_uuid', formData.get('observation_uuid'));
            newAssociationFormData.append('link_name', field);
            if (['identity-certainty', 'identity-reference', 'comment'].includes(field)) {
                newAssociationFormData.append('link_value', formData.get(field));
            } else {
                newAssociationFormData.append('to_concept', formData.get(field));
            }
            const res = await fetch('/vars/association', {
                method: 'POST',
                body: newAssociationFormData,
            });
            if (res.ok) {
                creations.push(field.replace('-', ' '));
            } else {
                updateFlashMessages('Failed to update annotation - please try again', 'danger');
                $('#load-overlay').addClass('loader-bg-hidden');
                $('#load-overlay').removeClass('loader-bg');
                return;
            }
        }
    }

    if (!creations.length && !updates.length && !deletes.length) {
        updateFlashMessages('No changes made', 'info');
        $('#load-overlay').addClass('loader-bg-hidden');
        $('#load-overlay').removeClass('loader-bg');
    } else {
        let flashString = '';
        if (creations.length) {
            flashString += `Added ${(creations).join(', ')}`;
        }
        if (updates.length) {
            flashString += `${flashString.length ? ', u' : 'U'}pdated ${(updates).join(', ')}`;
        }
        if (deletes.length) {
            flashString += `${flashString.length ? ', d' : 'D'}eleted ${(deletes).join(', ')}`;
        }
        updateFlashMessages(flashString, 'success');
        console.log(flashString)
        const res = await fetch(`/current-annotation/${formData.get('observation_uuid')}`);
        const updatedAnnotation = await res.json();
        const index = annotations.findIndex((anno) => anno.observation_uuid === formData.get('observation_uuid'));
        annotations[index].concept = updatedAnnotation.concept;
        annotations[index].associations = updatedAnnotation.associations;
        annotations[index].upon = null;
        annotations[index].guide_photo = null;
        annotations[index].identity_certainty = null;
        annotations[index].identity_reference = null;
        annotations[index].comment = null;
        updateHash();
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.updateAnnotation = updateAnnotation;

// tator
async function updateLocalization() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#editTatorLocalizationModal').modal('hide');
    const formData = new FormData($('#updateLocalizationForm')[0]);
    const res = await fetch('/tator/localization', {
        method: 'PATCH',
        body: formData,
    });
    if (res.status === 200) {
        const index = annotations.findIndex((anno) => anno.observation_uuid.toString() === formData.get('observation_uuid'));
        for (const pair of formData.entries()){
            annotations[index][pair[0]] = pair[1];
        }
        updateFlashMessages('Annotation successfully updated', 'success');
        updateHash();
    } else if (res.status === 304) {
        updateFlashMessages('No changes made', 'secondary');
    } else {
        updateFlashMessages('Failed to update annotation - please try again', 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.updateLocalization = updateLocalization;

function saveScrollPosition(page) {
    const url = new URL(window.location.href);
    const index = url.hash.indexOf('pg=');
    const queryAndHash = `${url.search}${url.hash.substring(0, index)}pg=${page}`;
    sessionStorage.setItem(`scrollPos${queryAndHash}`, `${window.scrollY}`);
}

async function getWormsAutocomplete() {
    const scientificNameObj = $('#editScientificName');
    const scientificName = scientificNameObj.val();
    if (scientificName.length > 2) {
        removeAutocomplete(scientificNameObj);
        removeAllLists();
        $('#scientificNameAutocompleteSpinner').show();
        const res = await fetch(`https://www.marinespecies.org/rest/AphiaRecordsByName/${scientificName}?like=true&marine_only=true`);
        let scientificNameList = [];
        if (res.status === 200) {
            const data = await res.json();
            scientificNameList = data.map((record) => record.scientificname);
        }
        autocomplete(scientificNameObj, scientificNameList);
        scientificNameObj.on('input', () => getWormsAutocomplete());

        validateName(scientificNameObj.val(), scientificNameList, $('#editTatorLocaModalSubmitButton')[0]);
        scientificNameObj.on('input', () => validateName(scientificNameObj.val(), scientificNameList, $('#editTatorLocaModalSubmitButton')[0]));
        scientificNameObj.on('change', () => validateName(scientificNameObj.val(), scientificNameList, $('#editTatorLocaModalSubmitButton')[0]));
        $('#scientificNameAutocompleteSpinner').hide();
    } else {
        $('#editTatorLocaModalSubmitButton')[0].disabled = true;
        removeAllLists(); // only show autocomplete if there are more than 2 characters
    }
}

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    const queryAndHash = url.search + url.hash;
    let unread = false;
    let read = false;
    let reviewer = null;

    autocomplete($('#editConceptName'), allConcepts);
    autocomplete($('#editUpon'), allConcepts);

    $('#scientificNameAutocompleteSpinner').hide();
    $('#editScientificName').on('input', () => getWormsAutocomplete());

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
        } else if (pair[0].includes('read')) {
            read = true;
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
        $('#externalAllAnchor').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
        });
        $('#externalUnreadAnchor').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
        });
        $('#externalReadAnchor').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
        });
        $('#syncCTD').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
        });
        if (unread) {
            $('#externalUnreadAnchor').css('color', 'white');
        } else if (read) {
            $('#externalReadAnchor').css('color', 'white');
        } else {
            $('#externalAllAnchor').css('color', 'white');
        }
        if (reviewer) {
            $('#externalAllAnchor').attr('href', `/external-review?reviewer=${reviewer}`);
            $('#externalUnreadAnchor').attr('href', `/external-review?reviewer=${reviewer}&unread=true`);
            $('#externalReadAnchor').attr('href', `/external-review?reviewer=${reviewer}&read=true`);
        }
    } else {
        // regular dive page
        $('#syncCTD').hide();
        $('#externalReviewFilters').hide();
    }

    $('#paginationSelect').on('change', () => {
        paginationLimit = $('#paginationSelect').val();
        pageCount = Math.ceil(annotationsToDisplay.length / paginationLimit);
        getPaginationNumbers();
        setCurrentPage(1);
        $('#totalPageNum').html(pageCount);
        $('#totalPageNumBottom').html(pageCount);
    });

    $('#imageFilterSelect').on('change', () => $('#imageFilterEntry').attr('placeholder', `Enter ${$('#imageFilterSelect').val().toLowerCase().replaceAll('_', ' ')}`));

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
$(document).ready(()=> {
    if (missingRecords?.length) {
        $('#missingRecordTable').find('tbody').append(missingRecords.map((record) =>
            `<tr>
                <td>${record.sequence}</td>
                <td>${record.timestamp}</td>
                <td>${record.annotator}</td>
                <td><a href="${record.image_url}" target="_blank" class="aquaLink" style="font-weight: 600;">Link</a></td>
            </tr>`
        ));
        $('#missingRecordsModal').modal('show');
    }

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
        $(this).find('#editOgConceptName').val(annotation.concept);
        $(this).find('#editAssociations').val(JSON.stringify(annotation.associations));

        conceptNameField.on('input', () => validateName(conceptNameField.val(), allConcepts, $('#editVarsAnnoModalSubmitButton')[0]));
        conceptNameField.on('change', () => validateName(conceptNameField.val(), allConcepts, $('#editVarsAnnoModalSubmitButton')[0]));
        uponField.on('input', () => validateName(uponField.val(), allConcepts, $('#editVarsAnnoModalSubmitButton')[0]));
        uponField.on('change', () => validateName(uponField.val(), allConcepts, $('#editVarsAnnoModalSubmitButton')[0]));

        document.getElementById("editGuidePhoto").options.length = 0; // clear options
        const guidePhotoSelect = $(this).find('#editGuidePhoto');
        for (const val of guidePhotoVals) { // append options back on with matching option selected
            const opt = $('<option/>', { value: val })
                .text(val)
                .prop('selected', annotation.guide_photo === val || val === '' && !annotation.guide_photo);
            opt.appendTo(guidePhotoSelect);
        }
    });

    $('#editTatorLocalizationModal').on('show.bs.modal', function (e) {
        const localization = $(e.relatedTarget).data('anno');
        const scientificNameField = $(this).find('#editScientificName');

        scientificNameField.val(localization.scientific_name);
        $(this).find('#editAttracted').val(localization.attracted);
        $(this).find('#editQualifier').val(localization.qualifier);
        $(this).find('#editCatAbundance').val(localization.categorical_abundance || '--');
        $(this).find('#editReason').val(localization.reason);
        $(this).find('#editTentativeId').val(localization.tentative_id);
        $(this).find('#editIdRemarks').val(localization.identification_remarks);
        $(this).find('#editIdentifiedBy').val(localization.identified_by);
        $(this).find('#editNotes').val(localization.notes);
        $(this).find('#editLocalizationIdType').val(JSON.stringify(localization.all_localizations.map((loc) => {
            return { elemental_id: loc.elemental_id, version: loc.version, type: loc.type };
        })));
        $(this).find('#baseUuid').val(localization.observation_uuid);
    });
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
