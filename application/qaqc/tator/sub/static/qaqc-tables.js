import { formattedNumber } from '../../../../static/js/util/formattedNumber.js';

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc/tator/sub/checklist${url.substring(url.indexOf('?'))}`;
}

window.returnToCheckList = returnToCheckList;

function updateHash() {
    $('#annotationTable').find('tbody').html('');
    if (Object.keys(uniqueTaxa).length) {
        // unique taxa table
        $('#downloadTsvButton').hide();
        $('#countLabel').html('Unique Taxa:&nbsp;&nbsp;');
        $('#totalCount').html(formattedNumber(Object.keys(uniqueTaxa).length));
        $('#subheader').html('Highlights taxa that have a box occur before the first dot or do not have both a box and a dot');

        $('#annotationTable').find('thead').html(`
            <tr class="thead-dark sticky-top" style="background-color: #1c2128; color: #eee;">
                <th scope="col">Scientific Name</th>
                <th scope="col">Tentative ID</th>
                <th scope="col">Morphospecies</th>
                <th scope="col">First Dot</th>
                <th scope="col">First Box</th>
                <th scope="col">Dots</th>
                <th scope="col">Boxes</th>
            </tr>
        `);
        for (const taxa of Object.keys(uniqueTaxa).sort()) {
            const firstBox = uniqueTaxa[taxa].first_box;
            const firstDot = uniqueTaxa[taxa].first_dot;
            let boxBeforeDot = false;

            if (firstBox && firstDot && firstBox < firstDot) {
                boxBeforeDot = true;
            }

            $('#annotationTable').find('tbody').append(`
                <tr class="text-start">
                    <td>${uniqueTaxa[taxa].scientific_name}</td>
                    <td>${uniqueTaxa[taxa].tentative_id}</td>
                    <td>${uniqueTaxa[taxa].morphospecies}</td>
                    <td>
                        <a class="aquaLink" href="${uniqueTaxa[taxa].first_dot_url}" target="_blank" style="${boxBeforeDot ? 'color: yellow; font-weight: bold;' : ''}">
                            ${uniqueTaxa[taxa].first_dot}
                        </a>
                    </td>
                    <td>
                        <a class="aquaLink" href="${uniqueTaxa[taxa].first_box_url}" target="_blank" style="${boxBeforeDot ? 'color: yellow; font-weight: bold;' : ''}">
                            ${uniqueTaxa[taxa].first_box}
                        </a>
                    </td>
                    <td style="${uniqueTaxa[taxa].dot_count === 0 ? 'color: yellow; font-weight: bold;' : ''}">${uniqueTaxa[taxa].dot_count}</td>
                    <td style="${uniqueTaxa[taxa].box_count === 0 ? 'color: yellow; font-weight: bold;' : ''}">${uniqueTaxa[taxa].box_count}</td>
                </tr>
            `);
        }
    } else if (Object.keys(mediaAttributes).length) {
        // media table
        let totalMedia = 0;
        $('#downloadTsvButton').hide();
        $('#annotationTable').find('thead').html(`
            <tr class="text-start sticky-top" style="background-color: #1c2128; color: #eee;">
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
                        <td>${media.name}</td>
                        <td style="${media.attributes.FOV !== baselineFov ? 'color: yellow; font-weight: bold;' : ''}">${media.attributes.FOV}</td>
                        <td>${media.attributes.Substrate}</td>
                        <td>${media.attributes['Video Quality']}</td>
                        <td>${media.attributes['Quality Notes']}</td>
                    </tr>
                `);
            }
        }
        $('#countLabel').html('Total Media:&nbsp;&nbsp;');
        $('#totalCount').html(formattedNumber(totalMedia));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    $('#deploymentList').html(mediaNames.join(', '));
    updateHash();
});

window.onhashchange = () => {
    updateHash();
};
