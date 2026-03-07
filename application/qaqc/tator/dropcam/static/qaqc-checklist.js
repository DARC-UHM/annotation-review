import { getCheckboxName, updateCheckbox, updateTaskCount } from '../../../static/qaqcCheckboxes.js';
import { formattedNumber } from '../../../../static/js/util/formattedNumber.js';

function showLoader() {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
}

document.addEventListener('DOMContentLoaded',  (event) => {
    const url = new URL(window.location.href);
    const projectId = url.searchParams.get('project');
    const sectionIds = url.searchParams.getAll('section');
    const sectionParam = sectionIds.map(id => `section=${id}`).join('&');
    const urlParams = `project=${projectId}&${sectionParam}`;

    $('#localizationCount').html(formattedNumber(localizationCount));
    $('#individualCount').html(formattedNumber(individualCount));
    $('#deploymentList').html(deploymentNames.join(', '));

    if (!localizationCount) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    for (const checkbox of Object.keys(checklist)) { // checklist was passed from the server
        const checkboxName = getCheckboxName(checkbox);
        $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
        $(`#${checkboxName}`).on('click', async () => {
            checklist[checkbox] = checklist[checkbox] < 2 ? checklist[checkbox] + 1 : 0;
            $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
            updateTaskCount(checklist);
            const res = await fetch('/qaqc/tator/dropcam/checklist', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    deployments: deploymentNames.join('&'),
                    [checkbox]: checklist[checkbox],
                }),
            });
            if (!res.ok) {
                console.error('Error updating checklist');
            }
        });
        updateTaskCount(checklist);
    }

    $('#fireworksToggleButton').on('click', () => {
        $('#fireworks').toggle();
    });

    $('#namesAcceptedAnchor').attr('href', `/qaqc/tator/dropcam/check/names-accepted?${urlParams}`);
    $('#namesAcceptedAnchor').on('click', () => showLoader());
    $('#missingQualifierAnchor').attr('href', `/qaqc/tator/dropcam/check/missing-qualifier?${urlParams}`);
    $('#missingQualifierAnchor').on('click', () => showLoader());
    $('#stetReasonAnchor').attr('href', `/qaqc/tator/dropcam/check/stet-missing-reason?${urlParams}`);
    $('#stetReasonAnchor').on('click', () => showLoader());
    $('#sameNameQualifierAnchor').attr('href', `/qaqc/tator/dropcam/check/same-name-qualifier?${urlParams}`);
    $('#sameNameQualifierAnchor').on('click', () => showLoader());
    $('#nonTargetNotAttractedAnchor').attr('href', `/qaqc/tator/dropcam/check/non-target-not-attracted?${urlParams}`);
    $('#nonTargetNotAttractedAnchor').on('click', () => showLoader());
    $('#existsInImageRefsAnchor').attr('href', `/qaqc/tator/dropcam/check/exists-in-image-references?${urlParams}`);
    $('#existsInImageRefsAnchor').on('click', () => showLoader());
    $('#attractedAnchor').attr('href', `/qaqc/tator/dropcam/check/attracted-not-attracted?${urlParams}`);
    $('#attractedAnchor').on('click', () => showLoader());
    $('#tentativeIdAnchor').attr('href', `/qaqc/tator/dropcam/check/all-tentative-ids?${urlParams}`);
    $('#tentativeIdAnchor').on('click', () => showLoader());
    $('#notesRemarksAnchor').attr('href', `/qaqc/tator/dropcam/check/notes-and-remarks?${urlParams}`);
    $('#notesRemarksAnchor').on('click', () => showLoader());
    $('#reExaminedAnchor').attr('href', `/qaqc/tator/dropcam/check/re-examined?${urlParams}`);
    $('#reExaminedAnchor').on('click', () => showLoader());
    $('#uniqueTaxaAnchor').attr('href', `/qaqc/tator/dropcam/check/unique-taxa?${urlParams}`);
    $('#uniqueTaxaAnchor').on('click', () => showLoader());
    $('#mediaAttributesAnchor').attr('href', `/qaqc/tator/dropcam/check/media-attributes?${urlParams}`);
    $('#mediaAttributesAnchor').on('click', () => showLoader());
    $('#summaryAnchor').attr('href', `/qaqc/tator/dropcam/check/summary?${urlParams}`);
    $('#summaryAnchor').on('click', () => showLoader());
    $('#maxNAnchor').attr('href', `/qaqc/tator/dropcam/check/max-n?${urlParams}`);
    $('#maxNAnchor').on('click', () => showLoader());
    $('#tofaAnchor').attr('href', `/qaqc/tator/dropcam/check/tofa?${urlParams}`);
    $('#tofaAnchor').on('click', () => showLoader());
    $('#imageGuideAnchor').attr('href', `/qaqc/tator/dropcam/check/image-guide?${urlParams}`);
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
