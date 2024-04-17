import { updateFlashMessages } from '../../util/updateFlashMessages.js';
import { autocomplete } from '../../util/autocomplete.js';

const sequences = [];
const toConcepts = ['s1', 's2', 'upon', 'size', 'guide-photo', 'habitat', 'megahabitat', 'sampled-by'];

let annotationsToDisplay = annotations;
let workingAnnotationUuid = '';
let associationToDeleteUuid = '';

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/vars/qaqc-checklist${url.substring(url.indexOf('?'))}`;
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
        switch (tempKey) {
            case 'phylum':
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                filtered = filterAndSort(filtered, 'order');
                filtered = filterAndSort(filtered, 'class');
                filtered = filterAndSort(filtered, 'phylum');
                break;
            case 'class':
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                filtered = filterAndSort(filtered, 'order');
                filtered = filterAndSort(filtered, 'class');
                break;
            case 'order':
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                filtered = filterAndSort(filtered, 'order');
                break;
            case 'family':
                filtered = filterAndSort(filtered, 'species');
                filtered = filterAndSort(filtered, 'genus');
                filtered = filterAndSort(filtered, 'family');
                break;
            case 'genus':
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

    const problemAssociations = {};
    if (title === 'Id Ref Associations') {
        // this block is to highlight the problem associations. same logic as on the backend :')
        const eqSet = (xs, ys) => xs.size === ys.size && [...xs].every((x) => ys.has(x));
        const idRefAssociations = {};

        for (const anno of annotationsToDisplay) {
            const currentIdRef = `${anno.video_sequence_name.slice(-3)}:${anno.identity_reference}`;
            if (!Object.keys(idRefAssociations).includes(currentIdRef)) {
                idRefAssociations[currentIdRef] = {s2: new Set(), 'sampled-by': new Set(), 'sample-reference': new Set()};
                problemAssociations[currentIdRef] = new Set();
                for (const ass of anno.associations) {
                    if (ass.link_name === 's2' || ass.link_name === 'sampled-by') {
                        idRefAssociations[currentIdRef][ass.link_name].add(ass.to_concept);
                    } else if (ass.link_name === 'sample-reference') {
                        idRefAssociations[currentIdRef][ass.link_name].add(ass.link_value);
                    } else {
                        idRefAssociations[currentIdRef][ass.link_name] = toConcepts.includes(ass.link_name) ? ass.to_concept : ass.link_value;
                    }
                }
            } else {
                const tempS2Set = new Set();
                const tempSampledBySet = new Set();
                const tempSampleRefSet = new Set();
                for (const ass of anno.associations) {
                    if (ass.link_name === 's2') {
                        tempS2Set.add(ass.to_concept);
                    } else if (ass.link_name === 'sampled-by') {
                        tempSampledBySet.add(ass.to_concept);
                    } else if (ass.link_name === 'sample-reference') {
                        tempSampleRefSet.add(ass.link_value);
                    } else {
                        if (toConcepts.includes(ass.link_name)) {
                            if (Object.keys(idRefAssociations[currentIdRef]).includes(ass.link_name)) {
                                if (idRefAssociations[currentIdRef][ass.link_name] !== ass.to_concept) {
                                    problemAssociations[currentIdRef].add(ass.link_name);
                                }
                            } else {
                                idRefAssociations[currentIdRef][ass.link_name] = ass.to_concept;
                            }
                        } else {
                            if (Object.keys(idRefAssociations[currentIdRef]).includes(ass.link_name)) {
                                if (idRefAssociations[currentIdRef][ass.link_name] !== ass.link_value) {
                                    problemAssociations[currentIdRef].add(ass.link_name);
                                }
                            } else {
                                idRefAssociations[currentIdRef][ass.link_name]?.add(ass.link_value);
                            }
                        }
                    }
                }
                if (!eqSet(tempS2Set, idRefAssociations[currentIdRef]['s2'])) {
                    problemAssociations[currentIdRef].add('s2');
                }
                if (!eqSet(tempSampledBySet, idRefAssociations[currentIdRef]['sampled-by'])) {
                    problemAssociations[currentIdRef].add('sampled-by');
                }
                if (!eqSet(tempSampleRefSet, idRefAssociations[currentIdRef]['sample-reference'])) {
                    problemAssociations[currentIdRef].add('sample-reference');
                }
            }
        }
    }

    annotationsToDisplay.forEach((annotation, index) => {
        let occurrenceRemarks = 'N/A';
        // get occurrence remarks
        annotation.associations.forEach((ass) => {
            if (ass.link_name === 'occurrence-remark') {
                if (occurrenceRemarks === 'N/A') {
                    occurrenceRemarks = ass.link_value;
                } else {
                    occurrenceRemarks += `; ${ass.link_value}`;
                }
            }
        });
        let videoUrl = annotation.video_url;
        videoUrl = `/video?link=${videoUrl.split('#t=')[0]}&time=${videoUrl.split('#t=')[1]}`;
        $('#annotationTable').find('tbody').append(`
        <tr>
            <td class="ps-5 py-3" style="width: 20%">
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
            <td class="small" style="width: 40%"><div id="problemsDiv${index}"></div></td>
            <td class="text-center small" style="width: 20%">
                <div class="mb-2">
                    ${annotation.image_url
                        ? `<a href="${annotation.image_url}" target="_blank"><img src="${annotation.image_url}" style="width: 200px;"/></a><br>` 
                        : `<div class="text=center pt-5 m-auto" style="width: 200px; height: 110px; background: #1e2125; color: #9f9f9f;">No image</div>`
                    }
                </div>
                <a class="editButton" href="${videoUrl}" target="_blank">See video</a><br>
            </td>
        </tr>
        `);
        $(`#problemsDiv${index}`).empty();
        // get qaqc items
        switch (title) {
            case 'Multiple Associations': {
                // TABLECEPTION
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th><th>Link Value</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                // find the duplicate associations and add them to the table
                const uniqueLinkNames = new Set();
                const duplicates = new Set();
                for (const association of sortedAssociations) {
                    if (association.link_name !== 's2') {
                        if (uniqueLinkNames.has(association.link_name)) {
                            duplicates.add(association.link_name);
                        } else {
                            uniqueLinkNames.add(association.link_name);
                        }
                    }
                }
                for (const linkName of duplicates) {
                    sortedAssociations.filter((ass) => ass.link_name === linkName).forEach((ass) => {
                        $(`#associationTable${index}`).append(`<tr><td>${ass.link_name}</td><td>${ass.to_concept}</td><td>${ass.link_value}</td></tr>`);
                    });
                }
                break;
            }
            case 'Missing Primary Substrate':
                // just here for the sake of completeness
                break;
            case 'Identical S1 &amp; S2': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                for (const association of sortedAssociations) {
                    if (association.link_name === 's1' || association.link_name === 's2') {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td></tr>`);
                    }
                }
                break;
            }
            case 'Duplicate S2': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                for (const association of sortedAssociations) {
                    if (association.link_name === 's2') {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td></tr>`);
                    }
                }
                break;
            }
            case 'Missing Upon Substrate': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                const relevantAsses = ['s1', 's2', 'upon'];
                for (const association of sortedAssociations) {
                    if (relevantAsses.includes(association.link_name)) {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td></tr>`);
                    }
                }
                break;
            }
            case 'Mismatched Substrates': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                for (const association of sortedAssociations) {
                    if (association.link_name === 's1' || association.link_name === 's2') {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td></tr>`);
                    }
                }
                break;
            }
            case 'Missing Upon': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                const relevantAsses = ['s1', 's2', 'upon'];
                for (const association of sortedAssociations) {
                    if (relevantAsses.includes(association.link_name)) {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td></tr>`);
                    }
                }
                break;
            }
            case 'Id Ref Concept Name': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                for (const association of annotation.associations) {
                    if (association.link_name === 'identity-reference') {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.link_value}</td></tr>`);
                    }
                }
                break;
            }
            case 'Id Ref Associations': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th><th>Link Value</th></tr></thead>
                    </table>
                `);
                const sortedAssociations = annotation.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
                const currentIdRef = `${annotation.video_sequence_name.slice(-3)}:${annotation.identity_reference}`;
                for (const association of sortedAssociations) {
                    if (problemAssociations[currentIdRef].has(association.link_name)) {
                        $(`#associationTable${index}`).append(`<tr style="color: yellow"><td>${association.link_name}</td><td>${association.to_concept}</td><td>${association.link_value}</td></tr>`);
                    } else {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td><td>${association.link_value}</td></tr>`);
                    }
                }
                break;
            }
            case 'Blank Associations': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>Link Value</th></tr></thead>
                    </table>
                `);
                for (const association of annotation.associations) {
                    if (association.link_value === '') {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.link_value}</td></tr>`);
                    }
                }
                break;
            }
            case 'Suspicious Hosts': {
                $(`#problemsDiv${index}`).append(`
                    <table id="associationTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Link Name</th><th>To Concept</th></tr></thead>
                    </table>
                `);
                for (const association of annotation.associations) {
                    if (association.link_name === 'upon') {
                        $(`#associationTable${index}`).append(`<tr><td>${association.link_name}</td><td>${association.to_concept}</td></tr>`);
                    }
                }
                break;
            }
            case 'Expected Associations': {
                const ranksToHighlight = ['Ophiuroidea', 'Comatulida', 'Anomura', 'Caridea', 'Goniasteridae',
                    'Poecilasmatidae', 'Parazoanthidae', 'Tubulariidae', 'Amphianthidae', 'Actinoscyphiidae',
                    'Henricia', 'Hydroidolina'];
                $(`#problemsDiv${index}`).append(`
                    <table id="taxaTable${index}" class="w-100 associationTable">
                        <thead><tr><th>Rank</th><th>Value</th></tr></thead>
                    </table>
                `);
                let upon;
                for (const association of annotation.associations) {
                    if (association.link_name === 'upon') {
                        upon = association.to_concept;
                    }
                }
                for (const key of Object.keys(annotation)) {
                    if (['class', 'order', 'infraorder', 'family', 'genus', 'species'].includes(key)) {
                        if (ranksToHighlight.includes(annotation[key])) {
                            $(`#taxaTable${index}`).append(`<tr><td style="text-transform: capitalize;">${key}</td><td style="color: yellow;">${annotation[key]}</td></tr>`);
                        } else {
                            $(`#taxaTable${index}`).append(`<tr><td style="text-transform: capitalize;">${key}</td><td>${annotation[key]}</td></tr>`);
                        }
                    }
                }
                $(`#taxaTable${index}`).append(`<tr><td>upon</td><td style="color: yellow;">${upon || 'none'}</td></tr>`);
                break;
            }
            case 'Host Associate Time Diff': {
                for (const association of annotation.associations) {
                    if (association.link_name === 'upon') {
                        $(`#problemsDiv${index}`).append(`<div>Upon: <span class="fw-bold">${association.to_concept}</span></div>`);
                    }
                }
                $(`#problemsDiv${index}`).append(`<div>Activity: <span class="fw-bold">${annotation.activity}</span></div>`);
                $(`#problemsDiv${index}`).append(`<div>${annotation.status}</div>`);
                break;
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    let vesselName;

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('sequence')) {
            const param = pair[1].split(' ');
            sequences.push(param.pop());
            if (!vesselName) {
                vesselName = param.join(' ');
            }
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
    $('#editModalFields').children().last().remove(); // get rid of the add button

    // any changes made to this select field should be also be updated in submit handler fn
    $('#editModalFields').append(`
        <div class="row pb-3 pt-2 text-center">
            <div class="col-4 ms-4 ps-4">
                <div class="small mb-1">New Association</div>
                <select id="newAssociationType" class="mb-1" style="width: 150px;" onchange="updateInputValidation()">
                    <option>categorical-abundance</option>
                    <option>comment</option>
                    <option>identity-certainty</option>
                    <option>identity-reference</option>
                    <option>occurrence-remark</option>
                    <option>population-quantity</option>
                    <option>s1</option>
                    <option>s2</option>
                    <option>size</option>
                    <option>upon</option>
                </select>
            </div>
            <div class="col-5">
                <div class="small mb-1">Value</div>
                <input id="newAssociationValue" type="text" class="modal-text-qaqc">
            </div>
            <div class="col-2 d-flex justify-content-end align-items-center pt-3">
                <button id="saveNewAssociationButton" type="button" class="qaqcCheckButton" onclick="createAssociation('${observation_uuid}')" disabled>
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
    addConceptInputValidation();
}

window.addAssociationRow = addAssociationRow;

function updateInputValidation() {
    if (toConcepts.includes($('#newAssociationType').val())) {
        addConceptInputValidation();
    } else {
        removeConceptInputValidation();
    }
}

window.updateInputValidation = updateInputValidation;

function addConceptInputValidation() {
    const inputValue = $('#newAssociationValue');
    autocomplete(inputValue, allConcepts);
    inputValue.on('input', () => validateName(inputValue.val(), $('#saveNewAssociationButton')));
    inputValue.on('change', () => validateName(inputValue.val(), $('#saveNewAssociationButton')));
    validateName(inputValue.val(), $('#saveNewAssociationButton'));
}

function removeConceptInputValidation() {
    const inputValue = $('#newAssociationValue');
    inputValue.off();
    inputValue.on('input', () => $('#saveNewAssociationButton').prop('disabled', inputValue.val() <= 0));
    inputValue.on('change', () => $('#saveNewAssociationButton').prop('disabled', inputValue.val() <= 0));
    $('#saveNewAssociationButton').prop('disabled', inputValue.val() <= 0);
}

function cancelAddAssociation() {
    $('#editModalFields').children().last().remove();
    $('#editModalFields').append(`
        <div class="row my-2">
            <button type="button" class="plusButton" onclick="addAssociationRow()">Add Association +</button>
        </div>
    `);
}

window.cancelAddAssociation = cancelAddAssociation;

async function updateConceptName(uuid) {
    const annoIndex = annotations.findIndex((anno) => anno.observation_uuid === workingAnnotationUuid);
    const formData = new FormData();
    formData.append('observation_uuid', uuid);
    formData.append('concept', $('#editConceptName').val());
    formData.append('identity-certainty', ''); // these blank values are added because that's how the
    formData.append('identity-reference', ''); // logic for the update anno function is set up and i
    formData.append('upon', '');               // don't feel like creating a new route/function just
    formData.append('comment', '');            // for updating the concept name :)
    formData.append('guide-photo', '');
    const res = await fetch('/vars/annotation', {
        method: 'PATCH',
        body: formData,
    });
    if (res.status === 200) {
        updateFlashMessages('Successfully updated concept name', 'success');
        annotations[annoIndex].concept = $('#editConceptName').val();
        $('#qaqcUpdateConceptButton').attr('disabled', true);
        updateHash();
    } else {
        updateFlashMessages('Failed to update concept name', 'danger');
    }
}

window.updateConceptName = updateConceptName;

async function createAssociation(observation_uuid) {
    const annoIndex = annotations.findIndex((anno) => anno.observation_uuid === workingAnnotationUuid);
    const newAssociation = {
        observation_uuid,
        link_name: $('#newAssociationType').val(),
    };
    if (toConcepts.includes($('#newAssociationType').val())) {
        // association uses to_concept
        newAssociation.to_concept = $('#newAssociationValue').val();
    } else {
        // association uses link_value
        newAssociation.link_value = $('#newAssociationValue').val();
        if ($('#newAssociationType').val() !== 'occurrence-remark') {
            newAssociation.to_concept = 'self';
        }
    }
    const formData = new FormData();
    Object.keys(newAssociation).forEach((key) => formData.append(key, newAssociation[key]));
    const res = await fetch('/vars/association', {
        method: 'POST',
        body: formData,
    });
    if (res.status === 201) {
        const json = await res.json();
        updateFlashMessages('Successfully added new association', 'success');
        annotations[annoIndex].associations.push(json);
        updateHash();
        loadModal(annotations[annoIndex]);
    } else {
        updateFlashMessages(`Failed to add association: ${res.status}`, 'danger');
    }
}

window.createAssociation = createAssociation;

async function updateAssociation(uuid, link_name, textInputId) {
    const annoIndex = annotations.findIndex((anno) => anno.observation_uuid === workingAnnotationUuid);
    const assIndex = annotations[annoIndex].associations.findIndex((ass) => ass.uuid === uuid);
    const updatedAssociation = { uuid, link_name };
    if (toConcepts.includes(link_name)) {
        // association uses to_concept
        updatedAssociation.to_concept = $(`#${textInputId}`).val();
    } else {
        // association uses link_value
        updatedAssociation.link_value = $(`#${textInputId}`).val();
        if (link_name !== 'occurrence-remark') {
            updatedAssociation.to_concept = 'self';
        }
    }
    const formData = new FormData();
    Object.keys(updatedAssociation).forEach((key) => formData.append(key, updatedAssociation[key]));
    const res = await fetch('/vars/association', {
        method: 'PATCH',
        body: formData,
    });
    if (res.status === 200) {
        updateFlashMessages('Successfully updated association', 'success');
        if (toConcepts.includes(link_name)) {
            annotations[annoIndex].associations[assIndex].to_concept = $(`#${textInputId}`).val();
        } else {
            annotations[annoIndex].associations[assIndex].link_value = $(`#${textInputId}`).val();
        }
        updateHash();
    } else {
        updateFlashMessages(`Failed to update association: ${res.status}`, 'danger');
    }
    $(`#button${textInputId}`).attr('disabled', true);
}

window.updateAssociation = updateAssociation;

async function deleteAssociation() {
    const annoIndex = annotations.findIndex((anno) => anno.observation_uuid === workingAnnotationUuid);
    const assIndex = annotations[annoIndex].associations.findIndex((ass) => ass.uuid === associationToDeleteUuid);
    const res = await fetch(`/vars/association/${associationToDeleteUuid}`, { method: 'DELETE' });
    if (res.status === 204) {
        updateFlashMessages('Successfully deleted association', 'success');
        annotations[annoIndex].associations.splice(assIndex, 1);
        updateHash();
        loadModal(annotations[annoIndex]);
    } else {
        updateFlashMessages(`Failed to delete association: ${res.status}`, 'danger');
    }
    $('#deleteAssociationModal').modal('hide');
}

window.deleteAssociation = deleteAssociation;

function loadModal(annotationData) {
    const sortedAssociations = annotationData.associations.sort((a, b) => (a.link_name > b.link_name) ? 1 : ((b.link_name > a.link_name) ? -1 : 0));
    workingAnnotationUuid = annotationData.observation_uuid;
    $('#editModalFields').empty();
    $('#editModalFields').append(`
        <div class="row pb-2">
            <div class="col-4 ms-4 ps-4 my-auto modal-label">
                Concept:
            </div>
            <div class="col-5">
                <input type="text" id="editConceptName" class="modal-text-qaqc">
            </div>
            <div class="col-2 d-flex justify-content-center pe-3">
                <button id="qaqcUpdateConceptButton" type="button" class="qaqcCheckButton" onclick="updateConceptName('${annotationData.observation_uuid}')" disabled>
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                        <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                    </svg>
                </button>
            </div>
        </div>
    `);
    const conceptNameField = $('#editConceptName');
    autocomplete(conceptNameField, allConcepts);
    conceptNameField.val(annotationData.concept);
    conceptNameField.on('input', () => validateName(conceptNameField.val(), $('#qaqcUpdateConceptButton')));
    conceptNameField.on('change', () => validateName(conceptNameField.val(), $('#qaqcUpdateConceptButton')));

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
                    <button id="button${ass.link_name}-${index}" type="button" class="qaqcCheckButton" onclick="updateAssociation('${ass.uuid}', '${ass.link_name}', '${ass.link_name}-${index}')" disabled>
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                            <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                        </svg>
                    </button>
                    <button type="button" class="qaqcXButton" data-bs-toggle="modal" data-ass='${ JSON.stringify(ass) }' data-bs-target="#deleteAssociationModal">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" stroke="currentColor" stroke-width="0.5px"/>
                        </svg>
                    </button>
                </div>
            </div>
        `);
        const field = $(`#${ass.link_name}-${index}`);
        const button = $(`#button${ass.link_name}-${index}`);
        if (toConcepts.includes(ass.link_name)) {
            field.val(ass.to_concept);
            field.on('input', () => validateName(field.val(), button));
            field.on('change', () => validateName(field.val(), button));
            autocomplete($(`#${ass.link_name}-${index}`), allConcepts);
        } else {
            field.val(ass.link_value);
            field.on('input', () => button.prop('disabled', field.val() <= 0));
            field.on('change', () => button.prop('disabled', field.val() <= 0));
        }
    });
    $('#editModalFields').append(`
        <div class="row my-3">
            <button type="button" class="plusButton" onclick="addAssociationRow('${annotationData.observation_uuid}')">Add Association +</button>
        </div>
    `);
}

$(document).ready(function () {
    $('#editModal').on('show.bs.modal', (e) => {
        loadModal($(e.relatedTarget).data('anno'));
    });

    $('#deleteAssociationModal').on('show.bs.modal', (e) => {
        associationToDeleteUuid = $(e.relatedTarget).data('ass').uuid;
    });
});
