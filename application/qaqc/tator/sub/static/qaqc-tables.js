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
        $('#subheader').html('Highlights taxa that do not have both a box and a dot');

        $('#annotationTable').find('thead').html(`
            <tr class="thead-dark sticky-top" style="background-color: #1c2128; color: #eee;">
                <th scope="col">Scientific Name</th>
                <th scope="col">Tentative ID</th>
                <th scope="col">Morphospecies</th>
                <th scope="col">Dots</th>
                <th scope="col">Boxes</th>
            </tr>
        `);
        for (const taxa of Object.keys(uniqueTaxa).sort()) {
            $('#annotationTable').find('tbody').append(`
                <tr class="text-start">
                    <td>${uniqueTaxa[taxa].scientific_name}</td>
                    <td>${uniqueTaxa[taxa].tentative_id}</td>
                    <td>${uniqueTaxa[taxa].morphospecies}</td>
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
                <th scope="col">Megahabitat</th>
                <th scope="col">Substrate</th>
                <th scope="col">Quality</th>
                <th scope="col">Quality Notes</th>
            </tr>
        `);
        for (const media of mediaAttributes) {
            const megahabitat = media.attributes.Megahabitat;
            totalMedia++;
            $('#annotationTable').find('tbody').append(`
                <tr class="text-start">
                    <td>${media.name}</td>
                    <td style="${megahabitat === undefined || megahabitat === 'Unset' ? 'color: yellow;' : ''}">${media.attributes.Megahabitat}</td>
                    <td>${media.attributes.Substrate}</td>
                    <td>${media.attributes['Video Quality']}</td>
                    <td>${media.attributes['Quality Notes']}</td>
                </tr>
            `);
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
