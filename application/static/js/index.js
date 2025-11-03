import { updateFlashMessages } from './util/updateFlashMessages.js';
import { autocomplete } from './util/autocomplete.js';

// just hardcoding 26 (NGS-ExTech Project) as I suspect it will never change. easy enough to update if it does
const TATOR_PROJECT = 26;
const TATOR_SECTION_STORAGE_KEY = 'tatorSection';
const TATOR_FOLDER_STORAGE_KEY = 'tatorFolder';

let numSequences = 1; // VARS
let numDeployments = 1; // TATOR
let deploymentList = [];
let tatorExpeditions = [];

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
    const res = await fetch(`/tator/sections/${TATOR_PROJECT}`);
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

        updateTatorFolders(sectionId);
    }
}

function updateTatorFolders(sectionId) {
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
    updateTatorDeployments(sectionId, folderName);
}

function updateTatorDeployments(sectionId, folderName) {
    const expedition = tatorExpeditions.find((expedition) => expedition.id.toString() === sectionId.toString());
    const deployments = expedition.folders[folderName];
    deploymentList = deployments;

    $('#deployment1').html('<option value="" selected disabled>Select a deployment</option>');

    for (const deployment of deploymentList) {
        $('#deployment1').append(`<option value="${deployment.id}">${deployment.name}</option>`);
    }
    $('#deployment1').val(deployments[0].id);
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

async function tatorLogin() {
    event.preventDefault();
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
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
        // await getTatorProjects();  TODO??
        updateFlashMessages('Logged in to Tator', 'success');
    } else {
        updateFlashMessages('Could not log in to Tator', 'danger');
    }

    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.tatorLogin = tatorLogin;

async function showTatorForm() {
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
    localStorage.setItem('annotationPlatform', 'Tator');
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
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.showTatorForm = showTatorForm;

$('#tatorSelect').on('click', showTatorForm);

$('#tatorExpedition').on('change', () => {
    localStorage.setItem(TATOR_SECTION_STORAGE_KEY, $('#tatorExpedition').val());
    updateTatorFolders($('#tatorExpedition').val());
});

$('#tatorFolder').on('change', () => {
    localStorage.setItem(TATOR_FOLDER_STORAGE_KEY, $('#tatorFolder').val());
    updateTatorDeployments($('#tatorExpedition').val(), $('#tatorFolder').val());
});

$('#varsSelect').on('click', () => {
    localStorage.setItem('annotationPlatform', 'VARS');
    $('#tatorLogin').hide();
    $('#tatorIndexForm').hide();
    $('#varsIndexForm').show();
    $('#platformSelectBtn').html('VARS ');
});

$('#logoutBtn').on('click', async () => {
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
    const res = await fetch('/tator/logout');
    if (res.status === 200) {
        $('#tatorLogin').show();
        $('#tatorIndexForm').hide();
        updateFlashMessages('Logged out of Tator', 'success');
    } else {
        updateFlashMessages('Error logging out', 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
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

$('#tatorPlusButton').on('click', () => {
    $('#tatorDeploymentLabel')[0].innerText = 'Deployments:';
    const inputDeployment = $(`#deployment${numDeployments}`).val();
    numDeployments++;

    $('#tatorDeploymentList').append(`
        <div id="depList${numDeployments}">
            <div class="row d-inline-flex">
                <div class="col-1"></div>
                <div class="col-10 p-0">
                    <select id="deployment${numDeployments}" name="deployment" class="sequenceName"></select>
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
        let index = deploymentList.findIndex((dep) => dep.id.toString() === inputDeployment.toString());
        return index < 0 ? '' : deploymentList[index + 1].id;
    });

    const currentNum = numDeployments;
    $(`#xButton${numDeployments}`).on('click', () => $(`#depList${currentNum}`)[0].remove());
});

$('#varsImageReviewButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const sequences = new FormData($('#varsIndexForm')[0]).getAll('sequence');
    window.location.href = `image-review/vars?sequence=${sequences.join('&sequence=')}`;
});

$('#varsQaqcButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const sequences = new FormData($('#varsIndexForm')[0]).getAll('sequence');
    window.location.href = `qaqc/vars/checklist?sequence=${sequences.join('&sequence=')}`;
});

$('#tatorImageReviewButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const formData = new FormData($('#tatorIndexForm')[0]);
    window.location.href = `image-review/tator?project=${formData.get('project')}&section=${formData.get('section')}&deployment=${formData.getAll('deployment').join('&deployment=')}`;
});

$('#tatorQaqcButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const formData = new FormData($('#tatorIndexForm')[0]);
    window.location.href = `qaqc/tator/checklist?project=${formData.get('project')}&section=${formData.get('section')}&deployment=${formData.getAll('deployment').join('&deployment=')}`;
});

$('a.external-review-link').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
});

$('#sequence1').on('input', checkSequence);
$('#index').on('click', checkSequence);

document.addEventListener('DOMContentLoaded', async () => {
    autocomplete($('#sequence1'), sequences);
    if (localStorage.getItem('annotationPlatform') === 'Tator' || window.location.search.includes('login=tator')) {
        await showTatorForm();
    }
});

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
