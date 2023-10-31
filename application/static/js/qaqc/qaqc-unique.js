const sequences = [];

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc-checklist${url.substring(url.indexOf('?'))}`;
}

function updateHash() {
    const hash = window.location.hash.slice(1);
    const fieldToCheck = hash.length ? hash.split('=')[1] : 'concept-names';
    let currentList;

    for (const list of uniqueList) {
        if (Object.keys(list).includes(fieldToCheck)) {
            currentList = list[fieldToCheck];
            break;
        }
    }

    const listToDisplay = Object.keys(currentList).sort().reduce((obj, key) => {
        obj[key] = currentList[key];
        return obj;
    }, {});

    $('#annotationTable').empty();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');

    if (fieldToCheck === 'concept-upon-combinations') {
        $('#annotationTable').append('<thead class="text-start"><tr><th>Concept</th><th>Upon</th><th>Number of records</th></tr></thead>');
        for (const combo of Object.keys(listToDisplay)) {
            $('#annotationTable').find('tbody').append(`<tr><td>${combo.split(':')[0]}</td><td>${combo.split(':')[1].replace('None', '-')}</td><td>${listToDisplay[combo]}</td></tr>`);
        }
    } else {
        for (const name of Object.keys(listToDisplay)) {
            $('#annotationTable').find('tbody').append(`<tr><td>${name.replace('None', '-')}</td><td>${listToDisplay[name]}</td></tr>`);
        }
        $('#annotationTable').append(`
            <thead class="text-start">
                <tr>
                    <th style="text-transform: capitalize;">${fieldToCheck.replace('-', ' ')}</th>
                    <th>Number of records</th>
                </tr>
            </thead>
        `);
    }
}

document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    let vesselName;

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('sequence')) {
            const param = pair[1].split(' ');
            sequences.push(param.pop());
            if (!vesselName) {
                vesselName = param.join(' ');
            }
        }
    }

    $('#sequenceList').html(`${sequences.join(', ')}<br>`);

    updateHash();

    $('#vesselName').html(vesselName);

    $('#uniqueSelect').on('change', () => {
        const hashList = window.location.hash.substring(1).split('&');
        hashList.shift();
        location.hash = `#unique=${$('#uniqueSelect').val().toLowerCase().replace('/', '-').replace(' ', '-')}`;
    });
});

window.onhashchange = () => {
    updateHash();
};
