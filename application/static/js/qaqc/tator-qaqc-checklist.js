const checkboxBlank = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#131818" class="bi bi-square-fill" viewBox="0 0 16 16">
                         <path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2z"/>
                       </svg>`;

const checkboxInProgress = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#c7b636" class="bi bi-dash-square-fill" viewBox="0 0 16 16">
                              <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2zm2.5 7.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1z"/>
                            </svg>`;

const checkboxComplete = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="#61c05a" class="bi bi-check-square-fill" viewBox="0 0 16 16">
                            <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2zm10.03 4.97a.75.75 0 0 1 .011 1.05l-3.992 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.75.75 0 0 1 1.08-.022z"/>
                          </svg>`;

/*
TATOR CHECKS:
- all scientific names and tentative ids are accepted in worms
- all taxa classified higher than species have qualifiers
- all records with 'stet' have a 'reason'
- attracted/not attracted taxa match expected (need to automatically flag taxa that are flagged as either)
- all taxa have at least one box and one dot
- all boxes occur at the same time of or after the first dot
- review all records with a tentative id (show id remarks/id'd by for this check)
- review all notes and remarks (no commas, review all vertical bars)
- review unique taxa
  - show the time that was first observed in a deployment (first dot)
    - get the time of arrival on bottom
    - find the difference between time of arrival on bottom and the first time of arrival for each taxa
  - max N in a deployment for each taxa
- review media attributes (FOV, quality, substrate)
  - FOV column: FOV should be the same for all videos in a deployment (highest FOV)
    - would be nice to have an option to change FOV for all clips in deployment
  - quality column that includes all qualities for each clip and clip comments (Quality Notes)
  - substrate column
- summary
  - annotator
  - include utc time
  - identified by
  - option to download as csv (similar to dscrtp)
 */
const checkboxStatus = {
    namesAcceptedCheckbox: 0,
    qualifiersCheckbox: 0,
    stetReasonCheckbox: 0,
    tentativeIdCheckbox: 0,
    attractedCheckbox: 0,
    allBoxDotCheckbox: 0,
    boxDotOrderCheckbox: 0,
    notesRemarksCheckbox: 0,
    uniqueTaxaCheckbox: 0,
    mediaAttributesCheckbox: 0,
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
    if (tasksComplete === Object.keys(checkboxStatus).length) {
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

    // check local storage for checkbox status, load values to checkboxes
    for (const checkbox of Object.keys(checkboxStatus)) {
        checkboxStatus[checkbox] = parseInt(localStorage.getItem(`${deployments.map((seq) => seq.split(' ').slice(-1)).join('&')}-${checkbox}`)) || 0;
        $(`#${checkbox}`).html(updateCheckbox(checkbox));
        $(`#${checkbox}`).on('click', () => {
            checkboxStatus[checkbox] = checkboxStatus[checkbox] < 2 ? checkboxStatus[checkbox] + 1 : 0;
           $(`#${checkbox}`).html(updateCheckbox(checkbox));
           updateTaskCount();
        });
        updateTaskCount();
    }

    window.onbeforeunload = (e) => {
        for (const checkbox of Object.keys(checkboxStatus)) {
            localStorage.setItem(`${deployments.map((seq) => seq.split(' ').slice(-1)).join('&')}-${checkbox}`, checkboxStatus[checkbox]);
        }
    };

    $('#namesAcceptedAnchor').attr('href', `/tator/qaqc/${projectId}/${sectionId}/names-accepted?deployment=${deployments.join('&deployment=')}`);
    $('#namesAcceptedAnchor').on('click', () => showLoader());
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
