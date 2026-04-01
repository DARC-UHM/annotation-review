import { getCheckboxName, updateCheckbox, updateTaskCount } from '../../../static/qaqcCheckboxes.js';
import { formattedNumber } from '../../../../static/js/util/formattedNumber.js';

function showLoader() {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
}

document.addEventListener('DOMContentLoaded', (event) => {
    const url = new URL(window.location.href);
    const projectId = url.searchParams.get('project');
    const sectionIds = url.searchParams.getAll('section');
    const transectIds = url.searchParams.getAll('transect');
    const sectionParam = sectionIds.map(id => `section=${id}`).join('&');
    const transectParam = transectIds.map(id => `transect=${id}`).join('&');
    const urlParams = `project=${projectId}&${sectionParam}&${transectParam}`;
    const qaqcCheckRoute = '/qaqc/tator/sub/check';

    $('#localizationCount').html(formattedNumber(localizationCount));
    $('#individualCount').html(formattedNumber(individualCount));
    $('#deploymentList').html(mediaNames.join(', '));

    if (!localizationCount) {
        $('#404').show();
    } else {
        $('#404').hide();
    }

    for (const checkbox of Object.keys(checklist)) {
        const checkboxName = getCheckboxName(checkbox);
        $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
        $(`#${checkboxName}`).on('click', async () => {
            checklist[checkbox] = checklist[checkbox] < 2 ? checklist[checkbox] + 1 : 0;
            $(`#${checkboxName}`).html(updateCheckbox(checklist[checkbox]));
            updateTaskCount(checklist);
            const res = await fetch('/qaqc/tator/sub/checklist', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    transectIds: transectIds.join('&'),
                    [checkbox]: checklist[checkbox],
                }),
            });
            if (!res.ok) {
                console.error('Error updating checklist');
            }
        });
    }
    updateTaskCount(checklist);

    $('#fireworksToggleButton').on('click', () => {
        $('#fireworks').toggle();
    });

    $('#namesAcceptedAnchor').attr('href', `${qaqcCheckRoute}/names-accepted?${urlParams}`);
    $('#namesAcceptedAnchor').on('click', () => showLoader());
    $('#missingQualifierAnchor').attr('href', `${qaqcCheckRoute}/missing-qualifier?${urlParams}`);
    $('#missingQualifierAnchor').on('click', () => showLoader());
    $('#stetReasonAnchor').attr('href', `${qaqcCheckRoute}/stet-missing-reason?${urlParams}`);
    $('#stetReasonAnchor').on('click', () => showLoader());
    $('#missingAncillaryAnchor').attr('href', `${qaqcCheckRoute}/missing-ancillary-data?${urlParams}`);
    $('#missingAncillaryAnchor').on('click', () => showLoader());
    $('#missingUponAnchor').attr('href', `${qaqcCheckRoute}/missing-upon?${urlParams}`);
    $('#missingUponAnchor').on('click', () => showLoader());
    $('#uponNotSubstrateAnchor').attr('href', `${qaqcCheckRoute}/upon-not-substrate?${urlParams}`);
    $('#uponNotSubstrateAnchor').on('click', () => showLoader());
    $('#suspiciousHostAnchor').attr('href', `${qaqcCheckRoute}/suspicious-hosts?${urlParams}`);
    $('#suspiciousHostAnchor').on('click', () => showLoader());
    $('#timeDiffHostUponAnchor').attr('href', `${qaqcCheckRoute}/host-associate-time-diff?${urlParams}`);
    $('#timeDiffHostUponAnchor').on('click', () => showLoader());
    $('#tentativeIdAnchor').attr('href', `${qaqcCheckRoute}/all-tentative-ids?${urlParams}`);
    $('#tentativeIdAnchor').on('click', () => showLoader());
    $('#notesRemarksAnchor').attr('href', `${qaqcCheckRoute}/notes-and-remarks?${urlParams}`);
    $('#notesRemarksAnchor').on('click', () => showLoader());
    $('#reExaminedAnchor').attr('href', `${qaqcCheckRoute}/re-examined?${urlParams}`);
    $('#reExaminedAnchor').on('click', () => showLoader());
    $('#reviewSizesAnchor').attr('href', `${qaqcCheckRoute}/sizes?${urlParams}`);
    $('#reviewSizesAnchor').on('click', () => showLoader());
    // $('#reviewCountsAnchor').attr('href', `${qaqcCheckRoute}/re-examined?${urlParams}`);
    // $('#reviewCountsAnchor').on('click', () => showLoader());
    $('#uniqueTaxaAnchor').attr('href', `${qaqcCheckRoute}/unique-taxa?${urlParams}`);
    $('#uniqueTaxaAnchor').on('click', () => showLoader());
    $('#mediaAttributesAnchor').attr('href', `${qaqcCheckRoute}/media-attributes?${urlParams}`);
    $('#mediaAttributesAnchor').on('click', () => showLoader());
    $('#summaryAnchor').attr('href', `${qaqcCheckRoute}/summary?${urlParams}`);
    $('#summaryAnchor').on('click', () => showLoader());
    $('#imageGuideAnchor').attr('href', `${qaqcCheckRoute}/image-guide?${urlParams}`);
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');

    $('[data-toggle="tooltip"]').tooltip();
});
