document.addEventListener('DOMContentLoaded', function(event) {
    const url = new URL(window.location.href);
    const sequences = [];
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
    $('#vesselName').html(vesselName);
    $('#sequenceList').html(`${sequences.join(', ')}<br>`);

    $('#annotationCount').html(annotationCount);

    if (!annotationCount) {
        $('#404').show();
    } else {
        $('#404').hide();
    }
});
