import { updateCheckbox } from '../../static/qaqcCheckboxes.js';
import { formattedNumber } from '../../../static/js/util/formattedNumber.js';

function updateTaskCount() {
    const tasksComplete = Object.values(checklist).reduce((accumulator, currentValue) => currentValue === 2 ? accumulator + 1 : accumulator, 0);
    $('#tasksComplete').html(tasksComplete);
    if (tasksComplete === Object.keys(checklist).length) {
        $('#fireworks').show();
        $('#fireworksToggleButton').show();
    } else {
        $('#fireworks').hide();
        $('#fireworksToggleButton').hide();
    }
}

function showLoader() {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
}

document.addEventListener('DOMContentLoaded',  (event) => {
    const url = new URL(window.location.href);
    const projectId = url.searchParams.get('project');
    const sectionId = url.searchParams.get('section');
    const deployments = url.searchParams.getAll('deployment');

    $('#deploymentList').html(deployments.map((seq) => seq.split(' ').slice(-1)).join(', '));

    $('#localizationCount').html(formattedNumber(localizationCount));
    $('#individualCount').html(formattedNumber(individualCount));

    if (!localizationCount) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    for (const checkbox of Object.keys(checklist)) { // checklist was passed from the server
        // convert snake case to camel case for checkbox name
        const checkboxName = checkbox.split('_').map((word, index) => {
            return index > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : word;
        }).join('') + 'Checkbox';
        $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
        $(`#${checkboxName}`).on('click', async () => {
            checklist[checkbox] = checklist[checkbox] < 2 ? checklist[checkbox] + 1 : 0;
            $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
            updateTaskCount();
            const res = await fetch('/qaqc/tator/checklist', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    deployments: deployments.join('&'),
                    [checkbox]: checklist[checkbox],
                }),
            });
            if (!res.ok) {
                console.error('Error updating checklist');
            }
        });
        updateTaskCount();
    }

    $('#fireworksToggleButton').on('click', () => {
        $('#fireworks').toggle();
    });

    $('#namesAcceptedAnchor').attr('href', `/qaqc/tator/check/names-accepted?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#namesAcceptedAnchor').on('click', () => showLoader());
    $('#missingQualifierAnchor').attr('href', `/qaqc/tator/check/missing-qualifier?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#missingQualifierAnchor').on('click', () => showLoader());
    $('#stetReasonAnchor').attr('href', `/qaqc/tator/check/stet-missing-reason?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#stetReasonAnchor').on('click', () => showLoader());
    $('#sameNameQualifierAnchor').attr('href', `/qaqc/tator/check/same-name-qualifier?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#sameNameQualifierAnchor').on('click', () => showLoader());
    $('#nonTargetNotAttractedAnchor').attr('href', `/qaqc/tator/check/non-target-not-attracted?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#nonTargetNotAttractedAnchor').on('click', () => showLoader());
    $('#existsInImageRefsAnchor').attr('href', `/qaqc/tator/check/exists-in-image-references?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#existsInImageRefsAnchor').on('click', () => showLoader());
    $('#attractedAnchor').attr('href', `/qaqc/tator/check/attracted-not-attracted?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#attractedAnchor').on('click', () => showLoader());
    $('#tentativeIdAnchor').attr('href', `/qaqc/tator/check/all-tentative-ids?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#tentativeIdAnchor').on('click', () => showLoader());
    $('#notesRemarksAnchor').attr('href', `/qaqc/tator/check/notes-and-remarks?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#notesRemarksAnchor').on('click', () => showLoader());
    $('#reExaminedAnchor').attr('href', `/qaqc/tator/check/re-examined?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#reExaminedAnchor').on('click', () => showLoader());
    $('#uniqueTaxaAnchor').attr('href', `/qaqc/tator/check/unique-taxa?project=${projectId}&section=${sectionId}&deployment=${deployments[0]}&deploymentList=${deployments.join(',')}`);
    $('#uniqueTaxaAnchor').on('click', () => showLoader());
    $('#mediaAttributesAnchor').attr('href', `/qaqc/tator/check/media-attributes?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#mediaAttributesAnchor').on('click', () => showLoader());
    $('#summaryAnchor').attr('href', `/qaqc/tator/check/summary?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#summaryAnchor').on('click', () => showLoader());
    $('#maxNAnchor').attr('href', `/qaqc/tator/check/max-n?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#maxNAnchor').on('click', () => showLoader());
    $('#tofaAnchor').attr('href', `/qaqc/tator/check/tofa?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
    $('#tofaAnchor').on('click', () => showLoader());
    $('#imageGuideAnchor').attr('href', `/qaqc/tator/check/image-guide?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&deployment=')}`);
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
