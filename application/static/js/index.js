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
    $('#imageReviewButton')[0].disabled = disabled;
    $('#qaqcButton')[0].disabled = disabled;
}

async function getTatorProjects() {
    const res = await fetch('/tator-projects');
    const json = await res.json();
    if (res.status === 200) {
        $('#tatorProject').html('');
        for (const project of json) {
            $('#tatorProject').append(`<option value="${project.id}">${project.name}</option>`);
        }
        $('#tatorProject').val(json[0].name);
    } else {
        updateFlashMessages('Unable to get Tator projects', 'danger');
    }
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
        updateFlashMessages('Logged in to Tator', 'success');
        $('#tatorLogin').hide();
        $('#password').val('');
        $('#tatorLoggedInUser').html(json.username);
        $('#tatorIndexForm').show();
        getTatorProjects();
    } else {
        updateFlashMessages('Unable to log in to Tator', 'danger');
    }

    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.tatorLogin = tatorLogin;

$('#tatorLogin').hide();
$('#tatorIndexForm').hide();

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
        getTatorProjects();
    } else {
        $('#tatorLogin').show();
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
});

$('#varsSelect').on('click', () => {
    $('#tatorLogin').hide();
    $('#tatorIndexForm').hide();
    $('#varsIndexForm').show();
    $('#platformSelectBtn').html('VARS ');
});

$('#logoutBtn').on('click', async () => {
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

$('#imageReviewButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const sequences = new FormData($('#varsIndexForm')[0]).getAll('sequence');
    window.location.href = `/image-review?sequence=${sequences.join('&sequence=')}`;
});

$('#qaqcButton').on('click', () => {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const sequences = new FormData($('#varsIndexForm')[0]).getAll('sequence');
    window.location.href = `/qaqc-checklist?sequence=${sequences.join('&sequence=')}`;
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
