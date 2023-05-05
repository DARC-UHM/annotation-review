let numSequences = 1;
let sequenceNameInput = $('#sequence1');

function checkSequence() {
    let disabled = false;
    for (let i = 1; i <= numSequences; i++) {
        if ($(`#sequence${i}`)[0] && !sequences.includes($(`#sequence${i}`)[0].value)) {
            disabled = true;
        }
    }
    $('#goButton')[0].disabled = disabled;
}

function xClick(num) {
    $(`#seqList${num}`)[0].remove();
}

function nextDive(inputDive) {
    let index = sequences.indexOf(inputDive);
    return index < 0 ? '' : sequences[index + 1];
}

function plusClick() {
    $('#seqNameLabel')[0].innerText = 'Sequence Names:';
    const inputDive = $(`#sequence${numSequences}`).val();
    numSequences++;

    $('#sequenceList').append(`
            <div id="seqList${numSequences}">
                <div class="row d-inline-flex">
                    <div class="col-1"></div>
                    <div class="col-10 p-0">
                        <div class="autocomplete">
                            <input type="text" id="sequence${numSequences}" name="sequence${numSequences}" class="sequenceName" placeholder="Hercules 1011715" autocomplete="off">
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
    $(`#sequence${numSequences}`).val(nextDive(inputDive));

    const currentNum = numSequences;
    $(`#xButton${numSequences}`).on('click', () => xClick(currentNum));
    $(`#sequence${numSequences}`).on('input', checkSequence);
    autocomplete($(`#sequence${numSequences}`)[0], sequences);
}

autocomplete(sequenceNameInput[0], sequences);

$('#plusButton').on('click', plusClick);
sequenceNameInput.on('input', checkSequence);
$('#index').on('click', checkSequence);
$('#taxonRankSelect').on('change', () => $('#taxonRankEntry').attr('placeholder', `Enter ${$('#taxonRankSelect').val().toLowerCase()}`));
$('#indexForm').submit(() => {
    if ($('#taxonRankEntry').val().length < 1) {
        $('#taxonRankEntry').prop('name', '');
        $('#taxonRankSelect').prop('name', '');
    }
});
