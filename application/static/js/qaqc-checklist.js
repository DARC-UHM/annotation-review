const checkboxBlank = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#131818" class="bi bi-square-fill" viewBox="0 0 16 16">
                         <path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2z"/>
                       </svg>`;

const checkboxInProgress = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#c7b636" class="bi bi-dash-square-fill" viewBox="0 0 16 16">
                              <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2zm2.5 7.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1z"/>
                            </svg>`;

const checkboxComplete = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#61c05a" class="bi bi-check-square-fill" viewBox="0 0 16 16">
                            <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2zm10.03 4.97a.75.75 0 0 1 .011 1.05l-3.992 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.75.75 0 0 1 1.08-.022z"/>
                          </svg>`;

const checkboxStatus = {
    multipleAssociationCheckbox: 0,
    primarySubstrateCheckbox: 0,
    identicalS1S2Checkbox: 0,
    duplicateS2Checkbox: 0,
    uponSubstrateCheckbox: 0,
    timestampSubstrateCheckbox: 0,
    missingUponCheckbox: 0,
    missingAncillaryCheckbox: 0,
    refIdConceptNameCheckbox: 0,
    refIdAssociationsCheckbox: 0,
    suspiciousHostCheckbox: 0,
    expectedAssociationCheckbox: 0,
    timeDiffHostUponCheckbox: 0,
    uniqueFieldsCheckbox: 0,
    uniqueHostUponCheckbox: 0,
};

function updateCheckbox(checkboxName) {
    switch (checkboxStatus[checkboxName]) {
        case 0: // not done
            return checkboxBlank;
        case 1: // in progress
            return checkboxInProgress;
        case 2:
            return checkboxComplete;
    }
}

function updateTaskCount() {
    const tasksComplete = Object.values(checkboxStatus).reduce((accumulator, currentValue) => currentValue === 2 ? accumulator + 1 : accumulator, 0);
    $('#tasksComplete').html(tasksComplete);
    if (tasksComplete === 15) {
        $('#fireworks').show();
    } else {
        $('#fireworks').hide();
    }
}

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    const sequences = [];
    let vesselName;

    for (const pair of url.searchParams.entries()) { // the only search params we expect here are sequences
        sequences.push(pair[1]);
        if (!vesselName) {
            vesselName = pair[1].split(' ').slice(0, -1).join(' ');
        }
    }

    $('#vesselName').html(vesselName);
    $('#sequenceList').html(sequences.map((seq) => seq.split(' ').slice(-1)).join(', '));

    $('#annotationCount').html(annotationCount);

    if (!annotationCount) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    // check local storage for checkbox status, load values to checkboxes
    for (const checkbox of Object.keys(checkboxStatus)) {
        checkboxStatus[checkbox] = parseInt(localStorage.getItem(`${vesselName[0]}${sequences.map((seq) => seq.split(' ').slice(-1)).join('&')}-${checkbox}`)) || 0;
        $(`#${checkbox}`).html(updateCheckbox(checkbox));
        $(`#${checkbox}`).on('click', () => {
            checkboxStatus[checkbox] = checkboxStatus[checkbox] < 2 ? checkboxStatus[checkbox] + 1 : 0;
           $(`#${checkbox}`).html(updateCheckbox(checkbox));
           updateTaskCount();
        });
    }

    window.onbeforeunload = (e) => {
        for (const checkbox of Object.keys(checkboxStatus)) {
            localStorage.setItem(`${vesselName[0]}${sequences.map((seq) => seq.split(' ').slice(-1)).join('&')}-${checkbox}`, checkboxStatus[checkbox]);
        }
    };

    $('#multipleAssociationAnchor').attr('href', `/qaqc/multiple-associations?sequence=${sequences.join('&sequence=')}`);
    $('#primarySubstrateAnchor').attr('href', `/qaqc/primary-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#identicalS1S2Anchor').attr('href', `/qaqc/identical-s1-s2?sequence=${sequences.join('&sequence=')}`);
    $('#duplicateS2Anchor').attr('href', `/qaqc/duplicate-s2?sequence=${sequences.join('&sequence=')}`);
    $('#uponSubstrateAnchor').attr('href', `/qaqc/upon-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#timestampSubstrateAnchor').attr('href', `/qaqc/timestamp-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#missingUponAnchor').attr('href', `/qaqc/missing-upon?sequence=${sequences.join('&sequence=')}`);
    $('#missingAncillaryAnchor').attr('href', `/qaqc/missing-ancillary-date?sequence=${sequences.join('&sequence=')}`);
    $('#refIdConceptNameAnchor').attr('href', `/qaqc/id-ref-concept-name?sequence=${sequences.join('&sequence=')}`);
    $('#refIdAssociationsAnchor').attr('href', `/qaqc/id-ref-associations?sequence=${sequences.join('&sequence=')}`);
    $('#suspiciousHostAnchor').attr('href', `/qaqc/suspicious-hosts?sequence=${sequences.join('&sequence=')}`);
    $('#expectedAssociationAnchor').attr('href', `/qaqc/expected-associations?sequence=${sequences.join('&sequence=')}`);
    $('#timeDiffHostUponAnchor').attr('href', `/qaqc/host-upon-time-diff?sequence=${sequences.join('&sequence=')}`);
    $('#uniqueFieldsAnchor').attr('href', `/qaqc/unique-fields?sequence=${sequences.join('&sequence=')}`);
    $('#uniqueHostUponAnchor').attr('href', `/qaqc/unique-host-upon?sequence=${sequences.join('&sequence=')}`);

});