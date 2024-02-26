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

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('deployment')) {
            const param = pair[1].split(' ');
            deployments.push(param.pop());
        }
    }
    $('#deploymentList').html(`${deployments.join(', ')}<br>`);
    $('#uniqueTaxaCount').html(Object.keys(uniqueTaxa).length.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));

    for (const taxa of Object.keys(uniqueTaxa).sort()) {
        const firstBox = uniqueTaxa[taxa].first_box;
        const firstDot = uniqueTaxa[taxa].first_dot;
        let boxBeforeDot = false;

        if (firstBox.split(':')[0] < firstDot.split(':')[0]) {
            boxBeforeDot = true;
        } else if (firstBox.split(':')[0] === firstDot.split(':')[0] && parseInt(firstBox.split(':')[1]) < parseInt(firstDot.split(':')[1]) - 1) {
            boxBeforeDot = true;
        }

        $('#annotationTable').find('tbody').append(`
            <tr class="text-start">
                <td>${taxa}</td>
                <td>${uniqueTaxa[taxa].max_n}</td>
                <td style="${boxBeforeDot ? 'color: yellow; font-weight: bold;' : ''}">${uniqueTaxa[taxa].first_dot}</td>
                <td style="${boxBeforeDot ? 'color: yellow; font-weight: bold;' : ''}">${uniqueTaxa[taxa].first_box}</td>
                <td style="${uniqueTaxa[taxa].dot_count === 0 ? 'color: yellow; font-weight: bold;' : ''}">${uniqueTaxa[taxa].dot_count}</td>
                <td style="${uniqueTaxa[taxa].box_count === 0 ? 'color: yellow; font-weight: bold;' : ''}">${uniqueTaxa[taxa].box_count}</td>
            </tr>
        `);
    }
});

window.onhashchange = () => {
    updateHash();
};
