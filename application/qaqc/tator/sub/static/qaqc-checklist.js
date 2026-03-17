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
        updateTaskCount(checklist);
    }

    $('#fireworksToggleButton').on('click', () => {
        $('#fireworks').toggle();
    });

    $('#namesAcceptedAnchor').attr('href', `/qaqc/tator/sub/check/names-accepted?${urlParams}`);
    $('#namesAcceptedAnchor').on('click', () => showLoader());
    $('#missingQualifierAnchor').attr('href', `/qaqc/tator/sub/check/missing-qualifier?${urlParams}`);
    $('#missingQualifierAnchor').on('click', () => showLoader());
    $('#stetReasonAnchor').attr('href', `/qaqc/tator/sub/check/stet-missing-reason?${urlParams}`);
    $('#stetReasonAnchor').on('click', () => showLoader());
    // $('#missingSubstrateAnchor').attr('href', `/qaqc/tator/sub/check/substrate-present?${urlParams}`);
    // $('#missingSubstrateAnchor').on('click', () => showLoader());
    // $('#missingAncillaryAnchor').attr('href', `/qaqc/tator/sub/check/substrate-present?${urlParams}`);
    // $('#missingAncillaryAnchor').on('click', () => showLoader());
    // $('#missingUponAnchor').attr('href', `/qaqc/tator/sub/check/upon-present?${urlParams}`);
    // $('#missingUponAnchor').on('click', () => showLoader());
    // $('#uponSubstrateAnchor').attr('href', `/qaqc/tator/sub/check/upon-present?${urlParams}`);
    // $('#uponSubstrateAnchor').on('click', () => showLoader());
    // $('#suspiciousHostAnchor').attr('href', `/qaqc/tator/sub/check/suspicious-hosts?${urlParams}`);
    // $('#suspiciousHostAnchor').on('click', () => showLoader());
    // $('#timeDiffHostUponAnchor').attr('href', `/qaqc/tator/sub/check/host-timestamp?${urlParams}`);
    // $('#timeDiffHostUponAnchor').on('click', () => showLoader());
    $('#tentativeIdAnchor').attr('href', `/qaqc/tator/sub/check/all-tentative-ids?${urlParams}`);
    $('#tentativeIdAnchor').on('click', () => showLoader());
    $('#notesRemarksAnchor').attr('href', `/qaqc/tator/sub/check/notes-and-remarks?${urlParams}`);
    $('#notesRemarksAnchor').on('click', () => showLoader());
    $('#reExaminedAnchor').attr('href', `/qaqc/tator/sub/check/re-examined?${urlParams}`);
    $('#reExaminedAnchor').on('click', () => showLoader());
    // $('#reviewSizesAnchor').attr('href', `/qaqc/tator/sub/check/re-examined?${urlParams}`);
    // $('#reviewSizesAnchor').on('click', () => showLoader());
    // TODO add counts check to external review schema, remove megahabitat check
    // $('#reviewCountsAnchor').attr('href', `/qaqc/tator/sub/check/re-examined?${urlParams}`);
    // $('#reviewCountsAnchor').on('click', () => showLoader());
    // $('#reviewExploratorySegmentsAnchor').attr('href', `/qaqc/tator/sub/check/exploratory-segments?${urlParams}`);
    // $('#reviewExploratorySegmentsAnchor').on('click', () => showLoader());
    $('#uniqueTaxaAnchor').attr('href', `/qaqc/tator/sub/check/unique-taxa?${urlParams}`);
    $('#uniqueTaxaAnchor').on('click', () => showLoader());
    $('#mediaAttributesAnchor').attr('href', `/qaqc/tator/sub/check/media-attributes?${urlParams}`);
    $('#mediaAttributesAnchor').on('click', () => showLoader());
    // $('#summaryAnchor').attr('href', `/qaqc/tator/sub/check/summary?${urlParams}`);
    // $('#summaryAnchor').on('click', () => showLoader());
    // $('#imageGuideAnchor').attr('href', `/qaqc/tator/sub/check/image-guide?${urlParams}`);
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
