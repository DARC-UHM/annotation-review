const sequences = [];

let annotationsToDisplay = annotations;

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc-checklist${url.substring(url.indexOf('?'))}`;
}

function updateFlashMessages(msg, cat) {
    $('#flash-messages-container').html(`
        <div class="alert alert-${cat} alert-dismissible px-5" style="position:fixed; left: 50%; transform: translate(-50%, 0); z-index: 10000;">
            <span class="px-2" style="font-weight: 500;">${msg}</span>
            <button type="button" class="btn-close small" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
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

function addAssociationRow(observation_uuid) {
    // TODO check to see if there are more associations we should add here
    $('#editModalFields').children().last().remove(); // get rid of the add button

    // any changes made to this select field should be also be updated in submit handler fn
    $('#editModalFields').append(`
        <div class="row pb-3 pt-2 text-center">
            <div class="col-4 ms-4 ps-4">
                <div class="small mb-1">New Association</div>
                <select id="newAssociationType" class="mb-1" style="width: 150px;">
                    <option>s1</option>
                    <option>s2</option>
                    <option>upon</option>
                    <option>population-quantity</option>
                    <option>identity-reference</option>
                    <option>identity-certainty</option>
                    <option>comment</option>
                    <option>occurrence-remarks</option>
                    <option>categorical-abundance</option>
                </select>
            </div>
            <div class="col-5">
                <div class="small mb-1">Value</div>
                <input id="newAssociationValue" type="text" class="modal-text-qaqc">
            </div>
            <div class="col-2 d-flex justify-content-end align-items-center pt-3">
                <button type="button" class="qaqcCheckButton" onclick="createAssociation('${observation_uuid}')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                        <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                    </svg>
                </button><button type="button" class="qaqcXButton" onclick="cancelAddAssociation()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                      <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" stroke="currentColor" stroke-width="0.5px"/>
                    </svg>
                </button>
            </div>
        </div>
    `);
}

function cancelAddAssociation() {
    $('#editModalFields').children().last().remove();
    $('#editModalFields').append(`
        <div class="row my-2">
            <button type="button" class="plusButton" onclick="addAssociationRow()">Add Association +</button>
        </div>
    `);
}

async function updateConceptName(uuid) {
    const formData = new FormData();
    formData.append('observation_uuid', uuid);
    formData.append('concept', $('#editConceptName').val());
    formData.append('identity-certainty', ''); // these blank values are added because that's how the
    formData.append('identity-reference', ''); // logic for the update anno function is set up and i
    formData.append('upon', '');               // don't feel like creating a new route/function just
    formData.append('comment', '');            // for updating the concept name :)
    formData.append('guide-photo', '');
    const res = await fetch('/update-annotation', {
        method: 'POST',
        body: formData,
    });
    if (res.status === 204) {
        updateFlashMessages('Successfully updated concept name', 'success');
    } else {
        updateFlashMessages('Failed to update concept name', 'danger');
    }
}

async function createAssociation(observation_uuid) {
    const newAssociation = {
        observation_uuid,
        link_name: $('#newAssociationType').val(),
    }
    if (['s1', 's2', 'upon'].includes($('#newAssociationType').val())) {
        // association uses to_concept
        newAssociation.to_concept = $('#newAssociationValue').val();
    } else {
        // association uses link_value
        newAssociation.link_value = $('#newAssociationValue').val();
        if ($('#newAssociationType').val() !== 'occurrence-remarks') {
            newAssociation.to_concept = 'self';
        }
    }
    console.log(newAssociation)
    const formData = new FormData();
    Object.keys(newAssociation).forEach((key) => formData.append(key, newAssociation[key]));
    const res = await fetch('/create-association', {
        method: 'POST',
        body: formData,
    });
    if (res.status === 201) {
        updateFlashMessages('Successfully added new association', 'success');
    } else {
        updateFlashMessages(`Failed to add association ${res.status}`, 'danger');
    }
}

async function updateAssociation() {
    
}

async function deleteAssociation() {

}

// get the annotation data and add it to the modal
$(document).ready(function () {
    $('#editModal').on('show.bs.modal', function (e) {
        const annotation = $(e.relatedTarget).data('anno');
        const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
        $('#editModalFields').empty();
        $('#editModalFields').append(`
            <div class="row pb-2">
                <div class="col-4 ms-4 ps-4 my-auto modal-label">
                    Concept:
                </div>
                <div class="col-5">
                    <input type="text" id="editConceptName" class="modal-text-qaqc">
                </div>
                <div class="col-2 d-flex justify-content-end">
                    <button type="button" class="qaqcCheckButton" onclick="updateConceptName('${annotation.observation_uuid}')">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                            <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                        </svg>
                    </button><button type="button" class="qaqcXButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" stroke="currentColor" stroke-width="0.5px"/>
                        </svg>
                    </button>
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
                    <div class="col-4 ms-4 ps-4 my-auto modal-label">
                        ${ass.link_name}:
                    </div>
                    <div class="col-5">
                        <input type="text" id="${ass.link_name}-${index}" class="modal-text-qaqc">
                    </div>
                    <div class="col-2 d-flex justify-content-end">
                        <button type="button" class="qaqcCheckButton">
                            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                                <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                            </svg>
                        </button><button type="button" class="qaqcXButton">
                            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                              <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" stroke="currentColor" stroke-width="0.5px"/>
                            </svg>
                        </button>
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
        $('#editModalFields').append(`
            <div class="row my-2">
                <button type="button" class="plusButton" onclick="addAssociationRow('${annotation.observation_uuid}')">Add Association +</button>
            </div>
        `);
    });
});
