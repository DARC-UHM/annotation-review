import { updateFlashMessages } from './util/updateFlashMessages.js';
import { autocomplete } from './util/autocomplete.js';
import * as Icons from './icons.js';

// just hardcoding 26 (NGS-ExTech Project) as I suspect it will never change. easy enough to update if it does
const TATOR_PROJECT = 26;
const ANNOTATION_PLATFORM_STORAGE_KEY = 'annotationPlatform';
const TATOR_SECTION_STORAGE_KEY = 'tatorSection';
const TATOR_FOLDER_STORAGE_KEY = 'tatorFolder';
const TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX = 'tatorDeployment';
const TATOR_SUBFOLDER_STORAGE_KEY = 'tatorSubFolder';

let numSequences = 1; // VARS
let numDeployments = 1; // TATOR
let numMedia = 1; // TATOR sub
let deploymentList = [];
let tatorExpeditions = [];
let tatorMedia = [];

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
    const expedition = tatorExpeditions.find((expedition) => expedition.id.toString() === topLevelSectionId.toString());
    const folderData = expedition.folders[folderName];

    $('.addedDeploymentSelect').remove();
    numDeployments = 1;
    $('#tatorDeploymentLabel')[0].innerText = 'Deployment:';

    if (folderName === 'sub') {
        // sub structure: subfolder (exploratory/transect) -> deployments
        const subFolderNames = Object.keys(folderData);
        if (subFolderNames.length === 0) {
            $('#tatorSubFolderContainer').hide();
            $('#deployment1').html('<option value="" selected disabled>No deployments found</option>');
            return;
        }
        $('#tatorSubFolder').html('');
        for (const subFolderName of subFolderNames) {
            $('#tatorSubFolder').append(`<option value="${subFolderName}">${subFolderName}</option>`);
        }
        let subFolderName = subFolderNames[0];
        const stored = localStorage.getItem(TATOR_SUBFOLDER_STORAGE_KEY);
        if (stored && subFolderNames.includes(stored)) {
            subFolderName = stored;
        }
        $('#tatorSubFolder').val(subFolderName);
        $('#tatorSubFolderContainer').show();
        await updateSubDeployments(topLevelSectionId, folderData, subFolderName);
    } else {
        // dropcam structure: deployments directly under folder
        $('#tatorSubFolderContainer').hide();
        $('#tatorMediaList').hide();
        deploymentList = folderData || [];

        if (deploymentList.length === 0) {
            $('#deployment1').html('<option value="" selected disabled>No deployments found</option>');
            return;
        }
        $('#deployment1').html('<option value="" selected disabled>Select a deployment</option>');
        for (const deployment of deploymentList) {
            $('#deployment1').append(`<option value="${deployment.id}">${deployment.name}</option>`);
        }
        const localStorageKey = `${TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX}_${topLevelSectionId}_${folderName}`;
        let deploymentSectionId = deploymentList[0]?.id;
        if (localStorage.getItem(localStorageKey)) {
            deploymentSectionId = localStorage.getItem(localStorageKey);
        }
        $('#deployment1').val(deploymentSectionId);
    }
}

async function updateSubDeployments(topLevelSectionId, subFolderData, subFolderName) {
    deploymentList = subFolderData[subFolderName] || [];
    const localStorageKey = `${TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX}_${topLevelSectionId}_sub_${subFolderName}`;

    if (deploymentList.length === 0) {
        $('#deployment1').html('<option value="" selected disabled>No deployments found</option>');
        $('#tatorMediaList').hide();
        return;
    }
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
    await updateTatorMedia();
}

async function updateTatorMedia() {
    if ($('#tatorFolder').val() !== 'sub') {
        return;
    }
    showLoader();
    $('.addedMediaSelect').remove();
    numMedia = 1;
    $('#tatorMediaLabel')[0].innerText = 'Media:';
    const deploymentSectionIds = $('.deploymentSelect').get().map(select => select.value).filter(Boolean);
    if (!deploymentSectionIds || deploymentSectionIds.length === 0) {
        $('#tatorMediaList').hide();
        hideLoader();
        return;
    }

    // get corresponding transects for selected deployment section ids
    const res = await fetch(`/tator/media?project=${TATOR_PROJECT}&section=${deploymentSectionIds.join('&section=')}`);
    if (res.status === 200) {
        tatorMedia = await res.json();
        if (tatorMedia.length === 0) {
            $('#tatorMediaList').hide();
            hideLoader();
            return;
        }
        $('#media1').html('<option value="" selected disabled>Select media</option>');
        for (const media of tatorMedia) {
            $('#media1').append(`<option value="${media.id}">${media.name}</option>`);
        }
        $('#media1').val(tatorMedia[0]?.id);
        $('#tatorMediaList').show();
    }
    hideLoader();
}

window.updateTatorMedia = updateTatorMedia;

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

$('#tatorSubFolder').on('change', () => {
    const subFolderName = $('#tatorSubFolder').val();
    localStorage.setItem(TATOR_SUBFOLDER_STORAGE_KEY, subFolderName);
    const expedition = tatorExpeditions.find((exp) => exp.id.toString() === $('#tatorExpedition').val().toString());
    updateSubDeployments($('#tatorExpedition').val(), expedition.folders['sub'], subFolderName);
});

$('#deployment1').on('change', async () => {
    const folderName = $('#tatorFolder').val();
    const subFolderName = $('#tatorSubFolder').val();
    const storageKey = (folderName === 'sub' && subFolderName)
        ? `${TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX}_${$('#tatorExpedition').val()}_sub_${subFolderName}`
        : `${TATOR_DEPLOYMENT_STORAGE_KEY_PREFIX}_${$('#tatorExpedition').val()}_${folderName}`;
    localStorage.setItem(storageKey, $('#deployment1').val());
    if (folderName === 'sub') {
        $('.addedDeploymentSelect').remove();
        numDeployments = 1;
        await updateTatorMedia();
    }
});

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
                        <button id="xButton${numSequences}" type="button" class="xButton">${Icons.x}</button>
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
        <div id="depList${numDeployments}" class="addedDeploymentSelect">
            <div class="row d-inline-flex">
                <div class="col-1"></div>
                <div class="col-10 p-0">
                    <select id="deployment${numDeployments}" name="section" class="sequenceName deploymentSelect" onchange="updateTatorMedia()">
                    </select>
                </div>
                <div class="col-1 ps-0">
                    <button id="xButton${numDeployments}" type="button" class="xButton">${Icons.x}</button>
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
        if ($('#tatorFolder').val() === 'sub') {
            await updateTatorMedia();
        }
    });

    if ($('#tatorFolder').val() === 'sub') {
        await updateTatorMedia();
    }
});

$('#tatorPlusMediaButton').on('click', () => {
    $('#tatorMediaLabel')[0].innerText = 'Media:';
    const prevSelected = $(`#media${numMedia}`).val();
    numMedia++;

    $('#tatorMediaList').append(`
        <div id="mediaList${numMedia}" class="addedMediaSelect">
            <div class="row d-inline-flex">
                <div class="col-1"></div>
                <div class="col-10 p-0">
                    <select id="media${numMedia}" name="media_id" class="sequenceName"></select>
                </div>
                <div class="col-1 ps-0">
                    <button id="xMediaButton${numMedia}" type="button" class="xButton">${Icons.x}</button>
                </div>
            </div>
        </div>
    `);
    for (const media of tatorMedia) {
        $(`#media${numMedia}`).append(`<option value="${media.id}">${media.name}</option>`);
    }
    $(`#media${numMedia}`).val(() => {
        const index = tatorMedia.findIndex(media => media.id?.toString() === prevSelected?.toString());
        return index < 0 ? '' : tatorMedia[index + 1]?.id;
    });

    const currentNum = numMedia;
    $(`#xMediaButton${numMedia}`).on('click', () => $(`#mediaList${currentNum}`)[0].remove());
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
    const isSub = $('#tatorFolder').val() === 'sub';
    $('#tatorQaqcButton').attr('formaction', isSub ? '/qaqc/tator/sub/checklist' : '/qaqc/tator/dropcam/checklist');
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
