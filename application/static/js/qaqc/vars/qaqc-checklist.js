import { updateCheckbox } from '../qaqcCheckboxes.js';

function updateTaskCount() {
    const tasksComplete = Object.values(checklist).reduce((accumulator, currentValue) => currentValue === 2 ? accumulator + 1 : accumulator, 0);
    $('#tasksComplete').html(tasksComplete);
    if (tasksComplete === Object.keys(checklist).length) {
        $('#fireworks').show();
    } else {
        $('#fireworks').hide();
    }
}

function showLoader() {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
}

document.addEventListener('DOMContentLoaded',  (event) => {
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

    $('#annotationCount').html(annotationCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
    $('#individualCount').html(individualCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
    $('#quickCheckTotalRecords').html(annotationCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));

    if (!annotationCount) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    for (const checkbox of Object.keys(checklist)) { // checklist was passed from the server
        const checkboxName = checkbox.split('_').map((word, index) => {
            return index > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : word;
        }).join('') + 'Checkbox';
        $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
        $(`#${checkboxName}`).on('click', async () => {
            checklist[checkbox] = checklist[checkbox] < 2 ? checklist[checkbox] + 1 : 0;
            $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
            updateTaskCount();
            const res = await fetch('/vars/qaqc-checklist', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sequences: sequences.join('&'),
                    [checkbox]: checklist[checkbox],
                }),
            });
            if (!res.ok) {
                console.error('Error updating checklist');
            }
        });
        updateTaskCount();
    }

    $('#multipleAssociationAnchor').attr('href', `/vars/qaqc/multiple-associations?sequence=${sequences.join('&sequence=')}`);
    $('#multipleAssociationAnchor').on('click', () => showLoader());
    $('#primarySubstrateAnchor').attr('href', `/vars/qaqc/missing-primary-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#primarySubstrateAnchor').on('click', () => showLoader());
    $('#identicalS1S2Anchor').attr('href', `/vars/qaqc/identical-s1-&-s2?sequence=${sequences.join('&sequence=')}`);
    $('#identicalS1S2Anchor').on('click', () => showLoader());
    $('#duplicateS2Anchor').attr('href', `/vars/qaqc/duplicate-s2?sequence=${sequences.join('&sequence=')}`);
    $('#duplicateS2Anchor').on('click', () => showLoader());
    $('#uponSubstrateAnchor').attr('href', `/vars/qaqc/missing-upon-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#uponSubstrateAnchor').on('click', () => showLoader());
    $('#timestampSubstrateAnchor').attr('href', `/vars/qaqc/mismatched-substrates?sequence=${sequences.join('&sequence=')}#sort=Timestamp`);
    $('#timestampSubstrateAnchor').on('click', () => showLoader());
    $('#missingUponAnchor').attr('href', `/vars/qaqc/missing-upon?sequence=${sequences.join('&sequence=')}`);
    $('#missingUponAnchor').on('click', () => showLoader());
    $('#refIdConceptNameAnchor').attr('href', `/vars/qaqc/id-ref-concept-name?sequence=${sequences.join('&sequence=')}#sort=Timestamp`);
    $('#refIdConceptNameAnchor').on('click', () => showLoader());
    $('#refIdAssociationsAnchor').attr('href', `/vars/qaqc/id-ref-associations?sequence=${sequences.join('&sequence=')}#sort=Timestamp`);
    $('#refIdAssociationsAnchor').on('click', () => showLoader());
    $('#blankAssociationsAnchor').attr('href', `/vars/qaqc/blank-associations?sequence=${sequences.join('&sequence=')}`);
    $('#blankAssociationsAnchor').on('click', () => showLoader());
    $('#suspiciousHostAnchor').attr('href', `/vars/qaqc/suspicious-hosts?sequence=${sequences.join('&sequence=')}`);
    $('#suspiciousHostAnchor').on('click', () => showLoader());
    $('#expectedAssociationAnchor').attr('href', `/vars/qaqc/expected-associations?sequence=${sequences.join('&sequence=')}`);
    $('#expectedAssociationAnchor').on('click', () => showLoader());
    $('#timeDiffHostUponAnchor').attr('href', `/vars/qaqc/host-associate-time-diff?sequence=${sequences.join('&sequence=')}`);
    $('#timeDiffHostUponAnchor').on('click', () => showLoader());
    $('#uniqueFieldsAnchor').attr('href', `/vars/qaqc/unique-fields?sequence=${sequences.join('&sequence=')}#unique=concept-names`);
    $('#uniqueFieldsAnchor').on('click', () => showLoader());

    $('#missingAncillaryAnchor').on('click', async () => {
        $('#quickCheckModalHeader').html('Missing Ancillary Data')
        $('#quickCheckCheck').html('missing ancillary data');
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        const res = await fetch(`/vars/qaqc/quick/missing-ancillary-data?sequence=${sequences.join('&sequence=')}`);
        const json = await res.json();
        $('#load-overlay').removeClass('loader-bg');
        $('#load-overlay').addClass('loader-bg-hidden');
        $('#quickCheckNumProblemRecords').html(json.num_records.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
        $('#quickCheckSeeDetailsBtn').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
            window.location.href = `/vars/qaqc/missing-ancillary-data?sequence=${sequences.join('&sequence=')}`
        });
    });

});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
