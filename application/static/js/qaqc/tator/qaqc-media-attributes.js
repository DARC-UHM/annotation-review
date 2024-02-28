const deployments = [];

function returnToCheckList() {
    const url = window.location.href;
    const projectId = url.split('/')[url.split('/').length - 3];
    const sectionId = url.split('/')[url.split('/').length - 2];
    window.location.href = `/tator/qaqc-checklist/${projectId}/${sectionId}${url.substring(url.indexOf('?'))}`;
}

window.returnToCheckList = returnToCheckList;

document.addEventListener('DOMContentLoaded', () => {
    const url = new URL(window.location.href);
    let totalMedia = 0;

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('deployment')) {
            const param = pair[1].split(' ');
            deployments.push(param.pop());
        }
    }
    $('#deploymentList').html(`${deployments.join(', ')}<br>`);

    for (const deployment of Object.keys(mediaAttributes).sort()) {
        const baselineFov = mediaAttributes[deployment][0]?.attributes.FOV;
        for (const media of mediaAttributes[deployment]) {
            totalMedia++;
            $('#annotationTable').find('tbody').append(`
                <tr class="text-start">
                    <td class="small">${media.name}</td>
                    <td style="${media.attributes.FOV !== baselineFov ? 'color: yellow; font-weight: bold;' : ''}">${media.attributes.FOV}</td>
                    <td>${media.attributes.Substrate}</td>
                    <td>${media.attributes['Video Quality']}</td>
                    <td>${media.attributes['Quality Notes']}</td>
                </tr>
            `);
        }
    }

    $('#totalMediaCount').html(totalMedia.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
});

window.onhashchange = () => {
    updateHash();
};
