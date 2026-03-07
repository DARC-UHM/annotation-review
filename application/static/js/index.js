import { updateFlashMessages } from './util/updateFlashMessages.js';
import { autocomplete } from './util/autocomplete.js';

// just hardcoding 26 (NGS-ExTech Project) as I suspect it will never change. easy enough to update if it does
const TATOR_PROJECT = 26;
const ANNOTATION_PLATFORM_STORAGE_KEY = 'annotationPlatform';
const TATOR_SECTION_STORAGE_KEY = 'tatorSection';
const TATOR_FOLDER_STORAGE_KEY = 'tatorFolder';
const TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX = 'tatorDeployment';

let numSequences = 1; // VARS
let numDeployments = 1; // TATOR
let numTransects = 1; // TATOR sub
let deploymentList = [];
let tatorExpeditions = [];
let tatorTransects = [];

function checkSequence() {
    let disabled = false;
    for (let i = 1; i <= numSequences; i++) {
        if ($(`#sequence${i}`)[0] && !sequences.includes($(`#sequence${i}`)[0].value)) {
            disabled = true;
        }
    }
    $('#varsImageReviewButton')[0].disabled = disabled;
    $('#varsQaqcButton')[0].disabled = disabled;
}

async function getTatorSections() {
    const res = await fetch(`/tator/sections?project=${TATOR_PROJECT}`);
    tatorExpeditions = await res.json();
    if (res.status === 200) {
        $('#tatorExpedition').html('<option value="" selected disabled>Select an expedition</option>');
        for (const expedition of tatorExpeditions) {
            $('#tatorExpedition').append(`<option value="${expedition.id}">${expedition.name}</option>`);
        }
        // load default section from local storage
        let sectionId = tatorExpeditions[0]?.id;
        if (localStorage.getItem(TATOR_SECTION_STORAGE_KEY)) {
            sectionId = localStorage.getItem(TATOR_SECTION_STORAGE_KEY);
        }
        $('#tatorExpedition').val(sectionId);

        await updateTatorFolders(sectionId);
    }
}

async function updateTatorFolders(sectionId) {
    if (!sectionId) {
        return;
    }
    const expedition = tatorExpeditions.find((expedition) => expedition.id.toString() === sectionId.toString());
    const folderNames = Object.keys(expedition.folders);
    if (folderNames.length === 0) {
        $('#tatorFolder').html('<option value="" selected disabled>No folders found</option>');
        $('#deployment1').html('<option value="" selected disabled>No deployments found</option>');
        return;
    }

    $('#tatorFolder').html('<option value="" selected disabled>Select a folder</option>');
    for (const folderName of folderNames) {
        $('#tatorFolder').append(`<option value="${folderName}">${folderName}</option>`);
    }

    // load default section from local storage
    let folderName = folderNames[0];
    if (localStorage.getItem(TATOR_FOLDER_STORAGE_KEY)) {
        folderName = localStorage.getItem(TATOR_FOLDER_STORAGE_KEY);
    }

    $('#tatorFolder').val(folderName);
    await updateTatorDeployments(sectionId, folderName);
}

async function updateTatorDeployments(topLevelSectionId, folderName) {
    const localStorageKey = `${TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX}_${topLevelSectionId}_${folderName}`;
    const expedition = tatorExpeditions.find((expedition) => expedition.id.toString() === topLevelSectionId.toString());
    deploymentList = expedition.folders[folderName];

    $('#deployment1').html('<option value="" selected disabled>Select a deployment</option>');

    for (const deployment of deploymentList) {
        $('#deployment1').append(`<option value="${deployment.id}">${deployment.name}</option>`);
    }

    // load default section from local storage
    let deploymentSectionId = deploymentList[0]?.id;
    if (localStorage.getItem(localStorageKey)) {
        deploymentSectionId = localStorage.getItem(localStorageKey);
    }
    $('#deployment1').val(deploymentSectionId);

    if (folderName === 'sub') {
        $('#tatorTransectList').show();
        await updateTatorTransects();
    } else {
        $('#tatorTransectList').hide();
        // clear transect selects and reset count in case user switched from sub to non-sub folder
        $('.addedTransectSelect').remove();
        $('#transect1').val(null);
        numTransects = 1;
    }
}

async function updateTatorTransects() {
    if ($('#tatorFolder').val() !== 'sub') {
        return;
    }

    showLoader();
    $('.addedTransectSelect').remove(); // just keep it simple and remove any added transect selects any time a deployment changes
    numTransects = 1;

    // get all selected deployment section ids
    const deploymentSectionIds = $('.deploymentSelect').get().map(select => select.value).filter(Boolean);

    // get corresponding transects for selected deployment section ids
    const res = await fetch(`/tator/transects?project=${TATOR_PROJECT}&section=${deploymentSectionIds.join('&section=')}`);
    if (res.status === 200) {
        tatorTransects = await res.json();
        $('#transect1').html('<option value="" selected disabled>Select a transect</option>');
        for (const transect of tatorTransects) {
            $('#transect1').append(`<option value="${transect.id}">${transect.name}</option>`);
        }
        $('#transect1').val(tatorTransects[0]?.id);
    }

    hideLoader();
}

async function tatorLogin() {
    event.preventDefault();
    showLoader();
    const formData = new FormData($('#tatorLogin')[0]);
    const res = await fetch('/tator/login', {
        method: 'POST',
        body: formData,
    });
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorLogin').hide();
        $('#password').val('');
        $('#tatorLoggedInUser').html(json.username);
        $('#tatorIndexForm').show();
        await getTatorSections();
        updateFlashMessages('Logged in to Tator', 'success');
    } else {
        updateFlashMessages('Could not log in to Tator', 'danger');
    }

    hideLoader();
}

window.tatorLogin = tatorLogin;

async function showTatorForm() {
    showLoader();
    localStorage.setItem(ANNOTATION_PLATFORM_STORAGE_KEY, 'Tator');
    $('#varsIndexForm').hide();
    $('#platformSelectBtn').html('Tator ');
    const res = await fetch('/tator/token');
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorLoggedInUser').html(json.username);
        $('#tatorIndexForm').show();
        await getTatorSections();
    } else {
        $('#tatorLogin').show();
    }
    hideLoader();
}

window.showTatorForm = showTatorForm;

$('#tatorSelect').on('click', showTatorForm);

$('#tatorExpedition').on('change', async () => {
    localStorage.setItem(TATOR_SECTION_STORAGE_KEY, $('#tatorExpedition').val());
    await updateTatorFolders($('#tatorExpedition').val());
});

$('#tatorFolder').on('change', async () => {
    localStorage.setItem(TATOR_FOLDER_STORAGE_KEY, $('#tatorFolder').val());
    await updateTatorDeployments($('#tatorExpedition').val(), $('#tatorFolder').val());
});

$('#deployment1').on('change', async () => {
    const storageKey = `${TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX}_${$('#tatorExpedition').val()}_${$('#tatorFolder').val()}`;
    localStorage.setItem(storageKey, $('#deployment1').val());
    await onDeploymentChange();
});

async function onDeploymentChange() {
    await updateTatorTransects();
}

window.onDeploymentChange = onDeploymentChange;

$('#varsSelect').on('click', () => {
    localStorage.setItem(ANNOTATION_PLATFORM_STORAGE_KEY, 'VARS');
    $('#tatorLogin').hide();
    $('#tatorIndexForm').hide();
    $('#varsIndexForm').show();
    $('#platformSelectBtn').html('VARS ');
});

$('#logoutBtn').on('click', async () => {
    showLoader();
    const res = await fetch('/tator/logout');
    if (res.status === 200) {
        $('#tatorLogin').show();
        $('#tatorIndexForm').hide();
        updateFlashMessages('Logged out of Tator', 'success');
    } else {
        updateFlashMessages('Error logging out', 'danger');
    }
    hideLoader();
});

// vars plus button
$('#plusButton').on('click', () => {
    $('#seqNameLabel')[0].innerText = 'Sequence Names:';
    const inputDive = $(`#sequence${numSequences}`).val();
    numSequences++;

    $('#sequenceList').append(`
            <div id="seqList${numSequences}">
                <div class="row d-inline-flex">
                    <div class="col-1"></div>
                    <div class="col-10 p-0">
                        <div class="autocomplete">
                            <input type="text" id="sequence${numSequences}" name="sequence" class="sequenceName" placeholder="[Vessel] [Dive Number]" autocomplete="off">
                        </div>
                    </div>
                    <div class="col-1 ps-0">
                        <button id="xButton${numSequences}" type="button" class="xButton">
                            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                              <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `);
    $(`#sequence${numSequences}`).val(() => {
        let index = sequences.indexOf(inputDive);
        return index < 0 ? '' : sequences[index + 1];
    });

    const currentNum = numSequences;
    $(`#xButton${numSequences}`).on('click', () => $(`#seqList${currentNum}`)[0].remove());
    $(`#sequence${numSequences}`).on('input', checkSequence);
    autocomplete($(`#sequence${numSequences}`), sequences);
});

$('#tatorPlusButton').on('click', async () => {
    $('#tatorDeploymentLabel')[0].innerText = 'Deployments:';
    const inputDeployment = $(`#deployment${numDeployments}`).val();
    numDeployments++;

    $('#tatorDeploymentList').append(`
        <div id="depList${numDeployments}">
            <div class="row d-inline-flex">
                <div class="col-1"></div>
                <div class="col-10 p-0">
                    <select id="deployment${numDeployments}" name="section" class="sequenceName deploymentSelect" onchange="onDeploymentChange()"></select>
                </div>
                <div class="col-1 ps-0">
                    <button id="xButton${numDeployments}" type="button" class="xButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `);
    for (const deployment of deploymentList) {
        $(`#deployment${numDeployments}`).append(`<option value="${deployment.id}">${deployment.name}</option>`);
    }
    $(`#deployment${numDeployments}`).val(() => {
        let index = deploymentList.findIndex((dep) => dep.id?.toString() === inputDeployment?.toString());
        return index < 0 ? '' : deploymentList[index + 1]?.id;
    });

    const currentNum = numDeployments;
    $(`#xButton${numDeployments}`).on('click', async () => {
        $(`#depList${currentNum}`)[0].remove();
        await updateTatorTransects();
    });

    await onDeploymentChange();
});

$('#tatorPlusTransectButton').on('click', () => {
    const prevSelectedTransect = $(`#transect${numTransects}`).val();
    $('#tatorTransectLabel')[0].innerText = 'Transects:';
    numTransects++;

    const newTransectSelectId = `transect${numTransects}`;
    $('#tatorTransectList').append(`
        <div id="tranList${numTransects}" class="addedTransectSelect">
            <div class="row d-inline-flex">
                <div class="col-1"></div>
                <div class="col-10 p-0">
                    <select id="${newTransectSelectId}" name="transect" class="sequenceName transectSelect"></select>
                </div>
                <div class="col-1 ps-0">
                    <button id="xButton${numTransects}" type="button" class="xButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `);
    for (const transect of tatorTransects) {
        $(`#${newTransectSelectId}`).append(`<option value="${transect.id}">${transect.name}</option>`);
    }
    $(`#${newTransectSelectId}`).val(() => {
        let index = tatorTransects.findIndex((trans) => trans.id?.toString() === prevSelectedTransect?.toString());
        return index < 0 ? '' : tatorTransects[index + 1]?.id;
    });

    const currentNum = numTransects;
    $(`#xButton${numTransects}`).on('click', () => $(`#tranList${currentNum}`)[0].remove());
});

$('#varsImageReviewButton').on('click', () => {
    showLoader();
});

$('#varsQaqcButton').on('click', () => {
    showLoader();
});

$('#tatorImageReviewButton').on('click', () => {
    showLoader();
});

$('#tatorQaqcButton').on('click', () => {
    showLoader();
});

$('a.external-review-link').on('click', () => {
    showLoader();
});

$('#sequence1').on('input', checkSequence);
$('#index').on('click', checkSequence);

function showLoader() {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
}

function hideLoader() {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
}

document.addEventListener('DOMContentLoaded', async () => {
    autocomplete($('#sequence1'), sequences);
    if (localStorage.getItem(ANNOTATION_PLATFORM_STORAGE_KEY) === 'Tator' || window.location.search.includes('login=tator')) {
        await showTatorForm();
    }
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    const persisted = (event.originalEvent && event.originalEvent.persisted) || false;
    if (!persisted) {
        return; // Not a bfcache/back-navigation restore
    }
    hideLoader();
});
