const sequences = [];

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc-checklist${url.substring(url.indexOf('?'))}`;
}

function updateHash() {
    const hash = window.location.hash.slice(1);
    const filterPairs = hash.split('&');
    const filter = {};

    if (filterPairs[0].length) {
        sortBy(filterPairs[0].split('=')[1]);
    }

    for (const key of Object.keys(filter)) {
        $('#filterList').append(`
            <span class="small filter-pill position-relative">
                ${key[0].toUpperCase()}${key.substring(1)}: ${filter[key]}
                <button type="button" class="position-absolute filter-x" onclick="removeFilter('${key}', '${filter[key]}')">×</button>
            </span>
        `);
    }

    $('#annotationCount').html(annotations.length);
    $('#annotationCountBottom').html(annotations.length);

    $('#annotationTable').empty();
    $('#annotationTable').append('<tbody class="text-start"></tbody>');
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
