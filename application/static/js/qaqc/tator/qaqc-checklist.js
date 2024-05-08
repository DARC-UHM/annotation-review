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
    const projectId = url.href.split('/').slice(-2)[0];
    const sectionId = url.href.split('/').slice(-1)[0].split('?')[0];
    const deployments = [];

    for (const pair of url.searchParams.entries()) { // the only search params we expect here are deployments
        deployments.push(pair[1]);
    }

    $('#deploymentList').html(deployments.map((seq) => seq.split(' ').slice(-1)).join(', '));

    $('#localizationCount').html(localizationCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
    $('#individualCount').html(individualCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));

    if (!localizationCount) {
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
            const res = await fetch('/tator/qaqc-checklist', {
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

    $('#namesAcceptedAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/names-accepted?deployment=${deployments.join('&deployment=')}`);
    $('#namesAcceptedAnchor').on('click', () => showLoader());
    $('#missingQualifierAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/missing-qualifier?deployment=${deployments.join('&deployment=')}`);
    $('#missingQualifierAnchor').on('click', () => showLoader());
    $('#stetReasonAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/stet-missing-reason?deployment=${deployments.join('&deployment=')}`);
    $('#stetReasonAnchor').on('click', () => showLoader());
    $('#sameNameQualifierAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/same-name-qualifier?deployment=${deployments.join('&deployment=')}`);
    $('#sameNameQualifierAnchor').on('click', () => showLoader());
    $('#nonTargetNotAttractedAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/non-target-not-attracted?deployment=${deployments.join('&deployment=')}`);
    $('#nonTargetNotAttractedAnchor').on('click', () => showLoader());
    $('#attractedAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/attracted-not-attracted?deployment=${deployments.join('&deployment=')}`);
    $('#attractedAnchor').on('click', () => showLoader());
    $('#tentativeIdAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/all-tentative-ids?deployment=${deployments.join('&deployment=')}`);
    $('#tentativeIdAnchor').on('click', () => showLoader());
    $('#notesRemarksAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/notes-and-remarks?deployment=${deployments.join('&deployment=')}`);
    $('#notesRemarksAnchor').on('click', () => showLoader());
    $('#uniqueTaxaAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/unique-taxa?deployment=${deployments.join('&deployment=')}`);
    $('#uniqueTaxaAnchor').on('click', () => showLoader());
    $('#mediaAttributesAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/media-attributes?deployment=${deployments.join('&deployment=')}`);
    $('#mediaAttributesAnchor').on('click', () => showLoader());
    $('#summaryAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/summary?deployment=${deployments.join('&deployment=')}`);
    $('#summaryAnchor').on('click', () => showLoader());
    $('#imageGuideAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/image-guide?deployment=${deployments.join('&deployment=')}`);
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
