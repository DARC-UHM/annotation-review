import { updateFlashMessages } from './util/updateFlashMessages.js';
import { autocomplete } from './util/autocomplete.js';

let numSequences = 1;

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

async function getTatorProjects() {
    const res = await fetch('/tator-projects');
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorProject').html('<option value="" selected disabled>Select a project</option>');
        for (const project of json) {
            $('#tatorProject').append(`<option value="${project.id}">${project.name}</option>`);
        }
        $('#tatorProject').val(json[0].id);
        await getTatorSections(json[0].id);
    } else {
        updateFlashMessages('Unable to get Tator projects', 'danger');
    }
}

async function getTatorSections(projectId) {
    if (!projectId) {
        return;
    }
    const res = await fetch(`/tator-sections/${projectId}`);
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorSection').html('<option value="" selected disabled>Select a section</option>');
        for (const section of json) {
            $('#tatorSection').append(`<option value="${section.id}">${section.name}</option>`);
        }
        $('#tatorSection').val(json[0].id);
        await getTatorDeployments(projectId, json[0].id);
    }
}

async function getTatorDeployments(projectId, sectionId) {
    if (!projectId || !sectionId) {
        return;
    }
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
    const res = await fetch(`/tator-deployments/${projectId}/${sectionId}`);
    const json = await res.json();
    console.log(json);
    if (res.status === 200) {
        $('#tatorDeployment').html('<option value="" selected disabled>Select a deployment</option>');
        for (const deployment of json) {
            $('#tatorDeployment').append(`<option value="${deployment}">${deployment}</option>`);
        }
        $('#tatorDeployment').val(json[0]);
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

async function tatorLogin() {
    event.preventDefault();
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
    const formData = new FormData($('#tatorLogin')[0]);
    const res = await fetch('/tator-login', {
        method: 'POST',
        body: formData,
    });
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorLogin').hide();
        $('#password').val('');
        $('#tatorLoggedInUser').html(json.username);
        $('#tatorIndexForm').show();
        await getTatorProjects();
        $('#tatorQaqcButton')[0].disabled = false;
        $('#tatorImageReviewButton')[0].disabled = false;
        updateFlashMessages('Logged in to Tator', 'success');
    } else {
        updateFlashMessages('Could not log in to Tator', 'danger');
    }

    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.tatorLogin = tatorLogin;

$('#tatorSelect').on('click', async () => {
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#varsIndexForm').hide();
    $('#platformSelectBtn').html('Tator ');
    const res = await fetch('/check-tator-token');
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorLoggedInUser').html(json.username);
        $('#tatorIndexForm').show();
        await getTatorProjects();
    } else {
        $('#tatorLogin').show();
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
});

$('#tatorProject').on('change', () => getTatorSections($('#tatorProject').val()));
$('#tatorSection').on('change', () => getTatorDeployments($('#tatorProject').val(), $('#tatorSection').val()));

$('#varsSelect').on('click', () => {
    $('#tatorLogin').hide();
    $('#tatorIndexForm').hide();
    $('#varsIndexForm').show();
    $('#platformSelectBtn').html('VARS ');
});

$('#logoutBtn').on('click', async () => {
    console.log('wat')
    $('#load-overlay').addClass('loader-bg');
    $('#load-overlay').removeClass('loader-bg-hidden');
    const res = await fetch('/tator-logout');
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

$('#varsImageReviewButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const sequences = new FormData($('#varsIndexForm')[0]).getAll('sequence');
    window.location.href = `/vars-image-review?sequence=${sequences.join('&sequence=')}`;
});

$('#varsQaqcButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const sequences = new FormData($('#varsIndexForm')[0]).getAll('sequence');
    window.location.href = `/vars-qaqc-checklist?sequence=${sequences.join('&sequence=')}`;
});

$('#tatorImageReviewButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const formData = new FormData($('#tatorIndexForm')[0]);
    window.location.href = `/tator-image-review/${formData.get('project')}/${formData.get('section')}`;
});

$('a.external-review-link').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
});

$('#sequence1').on('input', checkSequence);
$('#index').on('click', checkSequence);

autocomplete($('#sequence1'), sequences);

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
