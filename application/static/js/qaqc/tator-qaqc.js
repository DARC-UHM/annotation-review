import { updateFlashMessages } from '../util/updateFlashMessages.js';
import { autocomplete } from '../util/autocomplete.js';
import { tatorLocalizationRow } from '../image-review/tator-localization-table-row.js';
import {
    deleteFromExternalReview,
    markCommentRead,
    updateExternalReviewers,
    removeReviewer,
    addReviewer,
    updateReviewerName,
} from '../image-review/external-review-functions.js';

let annotationsToDisplay = annotations;
let currentAnnotation;
let reviewerIndex = 0;
let totalReviewers = 0;

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/tator/qaqc-checklist${url.substring(url.indexOf('?'))}`;
}

window.returnToCheckList = returnToCheckList;

function validateName(name, button) {
    button[0].disabled = name.length < 1 || !allConcepts.includes(name);
}

window.validateName = validateName;

function sortBy(key) {
    let tempKey;
    key = key.replace('%20', ' ');
    if (key === 'Default') {
        annotationsToDisplay = annotations;
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

    $('#sortSelect').val(key);
}

function updateHash() {
    const hash = window.location.hash.slice(1);

    annotationsToDisplay = annotations;

    if (hash.length) {
        sortBy(hash.split('=')[1]);
    }

    if (!annotationsToDisplay.length) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    $('#annotationCount').html(annotationsToDisplay.length);
    $('#annotationTable').empty();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');

    annotationsToDisplay.forEach((annotation) => {
        $('#annotationTable').find('tbody').append(tatorLocalizationRow(annotation, comments[annotation.observation_uuid]));
        $(`#${annotation.observation_uuid}_overlay`).css('opacity', '0.5');
        $(`#${annotation.observation_uuid}_image`).hover((e) => {
            if (e.type === 'mouseenter') {
                $(`#${annotation.observation_uuid}_overlay`).css('opacity', '1.0');
            } else if (e.type === 'mouseleave') {
                $(`#${annotation.observation_uuid}_overlay`).css('opacity', '0.5');
            }
        });
    });
}

window.updateExternalReviewers = updateExternalReviewers;
window.markCommentRead = markCommentRead;
window.removeReviewer = removeReviewer;
window.addReviewer = addReviewer;
window.updateReviewerName = updateReviewerName;
window.deleteFromExternalReview = deleteFromExternalReview;

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    const deployments = [];

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('deployment')) {
            const param = pair[1].split(' ');
            deployments.push(param.pop());
        }
    }

    $('#sequenceList').html(`${deployments.join(', ')}<br>`);

    updateHash();

    $('#sortSelect').on('change', () => {
        const hashList = window.location.hash.substring(1).split('&');
        hashList.shift();
        location.hash = `#sort=${$('#sortSelect').val()}`;
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
            return { id: loc.id, type: loc.type };
        })));
        $(this).find('#baseUuid').val(localization.observation_uuid);

        scientificNameField.on('input', () => validateName(scientificNameField.val(), $('#editTatorLocaModalSubmitButton')[0]));
        scientificNameField.on('change', () => validateName(scientificNameField.val(), $('#editTatorLocaModalSubmitButton')[0]));
    });

    $('#externalReviewModal').on('show.bs.modal', (e) => {
        currentAnnotation = $(e.relatedTarget).data('anno');
        $('#externalModalSubmitButton').prop('disabled', true);
        addReviewer(null);
        let tatorOverlay = null;
        if (currentAnnotation.type) {
            tatorOverlay = JSON.stringify({
                type: currentAnnotation.type,
                points: currentAnnotation.points,
                count: currentAnnotation.count,
                dimensions: currentAnnotation.dimensions,
            });
        }
        $('#externalObservationUuid').val(currentAnnotation.observation_uuid);
        $('#externalSequence').val(currentAnnotation.video_sequence_name);
        $('#externalScientificName').val(currentAnnotation.scientific_name);
        $('#externalTatorOverlay').val(tatorOverlay);
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

window.onhashchange = () => {
    updateHash();
};
