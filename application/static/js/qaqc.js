const sequences = [];

let annotationsToDisplay = annotations;
let currentAnnotation;

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc-checklist${url.substring(url.indexOf('?'))}`;
}

function validateName(name) {
    let disabled = false;
    if (name && !allConcepts.includes(name)) {
        disabled = true;
    }
    $('#editModalSubmitButton')[0].disabled = disabled;
}

function sortBy(key) {
    let tempKey;
    key = key.replace('%20', ' ');
    if (key === 'Default') {
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
    const filterPairs = hash.split('&');
    const filter = {};

    annotationsToDisplay = annotations;

    if (filterPairs[0].length) {
        sortBy(filterPairs[0].split('=')[1]);
    }

    for (const key of Object.keys(filter)) {
        console.log(key)
        $('#filterList').append(`
            <span class="small filter-pill position-relative">
                ${key[0].toUpperCase()}${key.substring(1)}: ${filter[key]}
                <button type="button" class="position-absolute filter-x" onclick="removeFilter('${key}', '${filter[key]}')">×</button>
            </span>
        `);
    }

    if (!annotationsToDisplay.length) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    $('#annotationCount').html(annotationsToDisplay.length);
    $('#annotationCountBottom').html(annotationsToDisplay.length);

    $('#annotationTable').empty();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');

    annotationsToDisplay.forEach((annotation, index) => {
        let occurrenceRemarks = 'N/A';
        // get occurrence remarks
        annotation.associations.forEach((ass) => {
            if (ass.link_name === 'occurrence-remark') {
                occurrenceRemarks = ass.link_value;
            }
        });
        $('#annotationTable').find('tbody').append(`
        <tr>
            <td class="ps-5 py-3">
                <div style="font-weight: 500; font-size: 18px;">${annotation.concept}</div>
                <div class="small">${annotation.recorded_timestamp}<br>${annotation.video_sequence_name}<br>${annotation.annotator}</div>
                <div class="small">Remarks: ${occurrenceRemarks}</div>
                <button 
                    type="button" 
                    data-bs-toggle="modal" 
                    data-anno='${ JSON.stringify(annotation) }' 
                    data-bs-target="#editModal" 
                    class="editButton small">Edit annotation
                </button>
            </td>
            <td class="small"><div id="problemsDiv${index}"></div></td>
            <td class="text-center small">
                <div class="mb-2">
                    ${annotation.image_url
                        ? `<a href="${annotation.image_url}" target="_blank"><img src="${annotation.image_url}" style="width: 200px;"/></a><br>` 
                        : `<div class="text=center pt-5 m-auto" style="width: 200px; height: 110px; background: #1e2125; color: #9f9f9f;">No image</div>`
                    }
                </div>
                <a class="editButton" href="${annotation.video_url}" target="_blank">See video</a><br>
            </td>
        </tr>
        `);
        $(`#problemsDiv${index}`).empty();
        // get qaqc items
        switch (title) {
            case 'Multiple Associations':
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th><th>Link Value</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                for (let i = 1; i < sortedAssociations.length; i++) {
                    if (sortedAssociations[i].link_name !== 's2' && sortedAssociations[i].link_name === sortedAssociations[i - 1].link_name) {
                        $(`#associationTable${index}`).append(`<tr><td>${sortedAssociations[i - 1].link_name}</td><td>${sortedAssociations[i - 1].to_concept}</td><td>${sortedAssociations[i - 1].link_value}</td></tr>`);
                        $(`#associationTable${index}`).append(`<tr><td>${sortedAssociations[i].link_name}</td><td>${sortedAssociations[i].to_concept}</td><td>${sortedAssociations[i].link_value}</td></tr>`);
                    }
                }
                break;
        }
    });
}

function updateAnnotation() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#editModal').modal('hide');
    const formData = new FormData($('#updateAnnotationForm')[0]);
    fetch('/update-annotation', {
        method: 'POST',
        body: formData,
    })
        .then((result) => {
            if (result.status === 204) {
                const index = annotations.findIndex((anno) => anno.observation_uuid === formData.get('observation_uuid'));
                for (const pair of formData.entries()){
                    annotations[index][pair[0]] = pair[1];
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

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    let vesselName;
    let unread = false;

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('sequence')) {
            const param = pair[1].split(' ');
            sequences.push(param.pop());
            if (!vesselName) {
                vesselName = param.join(' ');
            }
        } else if (pair[0].includes('unread')) {
            unread = true;
        }
    }

    $('#sequenceList').html(`${sequences.join(', ')}<br>`);

    updateHash();

    $('#vesselName').html(vesselName);

    $('#sortSelect').on('change', () => {
        const hashList = window.location.hash.substring(1).split('&');
        hashList.shift();
        location.hash = `#sort=${$('#sortSelect').val()}`;
    });
});

window.onhashchange = () => {
    updateHash();
};

// get the annotation data and add it to the modal
$(document).ready(function () {
    $('#editModal').on('show.bs.modal', function (e) {
        const annotation = $(e.relatedTarget).data('anno');
        const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
        $('#editModalFields').empty();
        $('#editModalFields').append(`
            <div class="row pb-2">
                <div class="col-4 ms-4 ps-4 modal-label">
                    Concept:
                </div>
                <div class="col">
                    <input type="text" id="editConceptName" name="concept" class="modal-text">
                </div>
            </div>
        `);
        const conceptNameField = $(this).find('#editConceptName');
        autocomplete(document.getElementById('editConceptName'), allConcepts);
        conceptNameField.val(annotation.concept);
        conceptNameField.on('input', () => validateName(conceptNameField.val()));
        conceptNameField.on('change', () => validateName(conceptNameField.val()));

        sortedAssociations.forEach((ass, index) => {
            $('#editModalFields').append(`
                <div class="row pb-2">
                    <div class="col-4 ms-4 ps-4 modal-label">
                        ${ass.link_name}:
                    </div>
                    <div class="col">
                        <input type="text" id="${ass.link_name}-${index}" name="${ass.link_name}-${index}" class="modal-text">
                    </div>
                </div>
            `);
            if (ass.to_concept === 'self'){
                $(`#${ass.link_name}-${index}`).val(ass.link_value);
            } else {
                const field = $(`#${ass.link_name}-${index}`);
                field.val(ass.to_concept);
                field.on('input', () => validateName(field.val()));
                field.on('change', () => validateName(field.val()));
                autocomplete(document.getElementById(`${ass.link_name}-${index}`), allConcepts);
            }
        });

        $(this).find('#editObservationUuid').val(annotation.observation_uuid);
    });
});
