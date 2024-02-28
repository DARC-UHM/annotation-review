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

    if (Object.keys(uniqueTaxa).length) {
        console.log(Object.keys(uniqueTaxa).length);
        $('#countLabel').html('Unique Taxa:&nbsp;&nbsp');
        $('#totalCount').html(Object.keys(uniqueTaxa).length.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
        $('#subheader').html('Highlights taxa that have a box occur before the first dot or do not have both a box and a dot');
        $('#annotationTable').find('thead').html(`
            <tr>
                <th scope="col">Scientific Name</th>
                <th scope="col">Max N</th>
                <th scope="col">First Dot (TOFA)</th>
                <th scope="col">First Box</th>
                <th scope="col">Num Dots</th>
                <th scope="col">Num Boxes</th>
            </tr>
        `);
        for (const taxa of Object.keys(uniqueTaxa).sort()) {
            const firstBox = uniqueTaxa[taxa].first_box;
            const firstDot = uniqueTaxa[taxa].first_dot;
            let boxBeforeDot = false;

            if (firstBox && firstDot) {
                if (firstBox.split(':')[0] < firstDot.split(':')[0]) {
                    boxBeforeDot = true;
                } else if (firstBox.split(':')[0] === firstDot.split(':')[0] && parseInt(firstBox.split(':')[1]) < parseInt(firstDot.split(':')[1]) - 1) {
                    boxBeforeDot = true;
                }
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
    } else if (Object.keys(mediaAttributes).length) {
        let totalMedia = 0;
        $('#annotationTable').find('thead').html(`
            <tr>
                <th scope="col">Media Name</th>
                <th scope="col">FOV</th>
                <th scope="col">Substrate</th>
                <th scope="col">Quality</th>
                <th scope="col">Quality Notes</th>
            </tr>
        `);
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
        $('#countLabel').html('Total Media:&nbsp;&nbsp');
        $('#totalCount').html(totalMedia.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','));
    } else {
        // summary table
    }
});

window.onhashchange = () => {
    updateHash();
};
