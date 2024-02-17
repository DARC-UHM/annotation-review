import { tatorLocalizationRow } from '../image-review/tator-localization-table-row.js';

let annotationsToDisplay = annotations;

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
});

window.onhashchange = () => {
    updateHash();
};
