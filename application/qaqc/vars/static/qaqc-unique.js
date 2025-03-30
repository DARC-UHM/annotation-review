import { formattedNumber } from '../../../static/js/util/formattedNumber.js';

const sequences = [];

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc/vars/checklist${url.substring(url.indexOf('?'))}`;
}

window.returnToCheckList = returnToCheckList;

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
        $('#annotationTable').append(`
            <thead class="text-start sticky-top" style="background-color: #1c2128; color: #eee;">
                <tr>
                    <th>Concept</th>
                    <th>Upon</th>
                    <th>Records</th>
                    <th>Individuals</th>
                </tr>
            </thead>
        `);
        for (const combo of Object.keys(listToDisplay)) {
            $('#annotationTable').find('tbody').append(`
                <tr>
                    <td>${combo.split(':')[0]}</td>
                    <td>${combo.split(':')[1].replace('None', '-')}</td>
                    <td>${formattedNumber(listToDisplay[combo].records)}</td>
                    <td>${formattedNumber(listToDisplay[combo].individuals)}</td>
                </tr>
            `);
        }
    } else {
        $('#annotationTable').append(`
            <thead class="text-start sticky-top" style="background-color: #1c2128; color: #eee;">
                <tr>
                    <th style="text-transform: capitalize; width: 60%;">${fieldToCheck.replace('-', ' ')}</th>
                    <th style="width: 20%;">Records</th>
                    <th style="width: 20%;">Individuals</th>
                </tr>
            </thead>
        `);
        for (const name of Object.keys(listToDisplay)) {
            $('#annotationTable').find('tbody').append(`
                <tr>
                    <td>${name.replace('None', '-')}</td>
                    <td>${formattedNumber(listToDisplay[name].records)}</td>
                    <td>${formattedNumber(listToDisplay[name].individuals)}</td>
                </tr>
            `);
        }
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
