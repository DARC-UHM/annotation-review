import { updateCheckbox } from '../../static/qaqcCheckboxes.js';
import { formattedNumber } from '../../../static/js/util/formattedNumber.js';

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

    $('#annotationCount').html(formattedNumber(annotationCount));
    $('#individualCount').html(formattedNumber(individualCount));
    $('#quickCheckTotalRecords').html(formattedNumber(annotationCount));
    $('#trueLocalizationCount').html(formattedNumber(trueLocalizationCount));
    $('#groupLocalizationCount').html(formattedNumber(groupLocalizationCount));

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
            const res = await fetch('/qaqc/vars/checklist', {
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

    $('#multipleAssociationsAnchor').attr('href', `/qaqc/vars/check/multiple-associations?sequence=${sequences.join('&sequence=')}`);
    $('#multipleAssociationsAnchor').on('click', () => showLoader());
    $('#primarySubstrateAnchor').attr('href', `/qaqc/vars/check/missing-primary-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#primarySubstrateAnchor').on('click', () => showLoader());
    $('#identicalS1S2Anchor').attr('href', `/qaqc/vars/check/identical-s1-&-s2?sequence=${sequences.join('&sequence=')}`);
    $('#identicalS1S2Anchor').on('click', () => showLoader());
    $('#duplicateS2Anchor').attr('href', `/qaqc/vars/check/duplicate-s2?sequence=${sequences.join('&sequence=')}`);
    $('#duplicateS2Anchor').on('click', () => showLoader());
    $('#uponSubstrateAnchor').attr('href', `/qaqc/vars/check/missing-upon-substrate?sequence=${sequences.join('&sequence=')}`);
    $('#uponSubstrateAnchor').on('click', () => showLoader());
    $('#timestampSubstrateAnchor').attr('href', `/qaqc/vars/check/mismatched-substrates?sequence=${sequences.join('&sequence=')}#sort=Timestamp`);
    $('#timestampSubstrateAnchor').on('click', () => showLoader());
    $('#missingUponAnchor').attr('href', `/qaqc/vars/check/missing-upon?sequence=${sequences.join('&sequence=')}`);
    $('#missingUponAnchor').on('click', () => showLoader());
    $('#refIdConceptNameAnchor').attr('href', `/qaqc/vars/check/id-ref-concept-name?sequence=${sequences.join('&sequence=')}#sort=Timestamp`);
    $('#refIdConceptNameAnchor').on('click', () => showLoader());
    $('#refIdAssociationsAnchor').attr('href', `/qaqc/vars/check/id-ref-associations?sequence=${sequences.join('&sequence=')}#sort=Timestamp`);
    $('#refIdAssociationsAnchor').on('click', () => showLoader());
    $('#blankAssociationsAnchor').attr('href', `/qaqc/vars/check/blank-associations?sequence=${sequences.join('&sequence=')}`);
    $('#blankAssociationsAnchor').on('click', () => showLoader());
    $('#suspiciousHostAnchor').attr('href', `/qaqc/vars/check/suspicious-hosts?sequence=${sequences.join('&sequence=')}`);
    $('#suspiciousHostAnchor').on('click', () => showLoader());
    $('#expectedAssociationAnchor').attr('href', `/qaqc/vars/check/expected-associations?sequence=${sequences.join('&sequence=')}`);
    $('#expectedAssociationAnchor').on('click', () => showLoader());
    $('#timeDiffHostUponAnchor').attr('href', `/qaqc/vars/check/host-associate-time-diff?sequence=${sequences.join('&sequence=')}`);
    $('#timeDiffHostUponAnchor').on('click', () => showLoader());
    $('#boundingBoxesAnchor').attr('href', `/qaqc/vars/check/number-of-bounding-boxes?sequence=${sequences.join('&sequence=')}`);
    $('#boundingBoxesAnchor').on('click', () => showLoader());
    $('#uniqueFieldsAnchor').attr('href', `/qaqc/vars/check/unique-fields?sequence=${sequences.join('&sequence=')}#unique=concept-names`);
    $('#uniqueFieldsAnchor').on('click', () => showLoader());

    $('#missingAncillaryAnchor').on('click', async () => {
        $('#quickCheckModalHeader').html('Missing Ancillary Data')
        $('#quickCheckCheck').html('missing ancillary data');
        $('#load-overlay').removeClass('loader-bg-hidden');
        $('#load-overlay').addClass('loader-bg');
        const res = await fetch(`/qaqc/vars/quick-check/missing-ancillary-data?sequence=${sequences.join('&sequence=')}`);
        const json = await res.json();
        $('#load-overlay').removeClass('loader-bg');
        $('#load-overlay').addClass('loader-bg-hidden');
        $('#quickCheckNumProblemRecords').html(formattedNumber(json.num_records));
        $('#quickCheckSeeDetailsBtn').on('click', () => {
            $('#load-overlay').removeClass('loader-bg-hidden');
            $('#load-overlay').addClass('loader-bg');
            window.location.href = `/qaqc/vars/check/missing-ancillary-data?sequence=${sequences.join('&sequence=')}`
        });
    });

});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
