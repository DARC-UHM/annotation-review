const deployments = [];

const caretDownFill = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill ms-1 pt-1" viewBox="0 0 16 16">
    <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
</svg>`;

const caretUpFill = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-up-fill ms-1 pt-1" viewBox="0 0 16 16">
    <path d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"/>
</svg>`;

function returnToCheckList() {
    const url = window.location.href;
    const projectId = url.split('/')[url.split('/').length - 3];
    const sectionId = url.split('/')[url.split('/').length - 2];
    window.location.href = `/tator/qaqc-checklist/${projectId}/${sectionId}${url.substring(url.indexOf('?'))}`;
}

window.returnToCheckList = returnToCheckList;

function setSort(sort) {
    const url = new URL(window.location.href);
    url.hash = `sort=${sort}`;
    window.location.href = url;
}

window.setSort = setSort;

function updateHash() {
    $('#annotationTable').find('tbody').html('');
    if (Object.keys(uniqueTaxa).length) {
        // unique taxa table
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
        // media table
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
        const url = new URL(window.location.href);
        const hash = url.hash.slice(1);
        const sort = hash.split('=')[1] || 'timestamp';
        let dark = true;

        $('#headerContainer').css('max-width', '100%');
        $('#tableContainer').removeClass('d-flex');
        $('#backButtonText').removeClass('d-xxl-inline');
        $('#annotationTable').find('thead').html(`
            <tr class="small text-start sticky-top" style="background: #1c2128; cursor: pointer;">
                <th
                  scope="col"
                  style="position: sticky; left: 0; background: #1c2128; z-index: 1;"
                  onclick="setSort('scientific_name')"
                  class="table-header-hover"
                >
                    <div class="d-flex">
                        ScientificName
                        ${sort === 'scientific_name' ? caretUpFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('rank')" class="table-header-hover">
                    <div class="d-flex">
                        TaxonRank
                        ${sort === 'rank' ? caretUpFill : ''}
                    </div>
                </th>
                <th scope="col">AphiaID</th>
                <th scope="col" onclick="setSort('phylum')" class="table-header-hover">
                    <div class="d-flex">
                        Phylum
                        ${sort === 'phylum' ? caretUpFill : ''}
                    </div>
                </th>
                <th scope="col">Class</th>
                <th scope="col">Subclass</th>
                <th scope="col">Order</th>
                <th scope="col">Suborder</th>
                <th scope="col">Family</th>
                <th scope="col">Subfamily</th>
                <th scope="col">Genus</th>
                <th scope="col">Subgenus</th>
                <th scope="col">Species</th>
                <th scope="col">Subspecies</th>
                <th scope="col">ObservationTimestamp</th>
                <th scope="col">IdentificationRemarks</th>
                <th scope="col">IdentifiedBy</th>
                <th scope="col">IdentificationQualifier</th>
                <th scope="col">Reason</th>
                <th scope="col">Notes</th>
                <th scope="col">Attracted</th>
                <th scope="col">Latitude</th>
                <th scope="col">Longitude</th>
                <th scope="col">DepthInMeters</th>
                <th scope="col">IndividualCount</th>
                <th scope="col">CategoricalAbundance</th>
            </tr>
        `);
        for (const annotation of annotations.sort((a, b) => a[sort]?.localeCompare(b[sort]))) {
            for (const rank of ['subspecies', 'species', 'subgenus', 'genus', 'subfamily', 'family', 'suborder', 'order', 'subclass', 'class', 'phylum']) {
                if (annotation[rank]) {
                    annotation.rank = rank.replace(/_/g, ' ');
                    annotation.rank = annotation.rank.charAt(0).toUpperCase() + annotation.rank.slice(1);
                    break;
                }
            }
            $('#annotationTable').find('tbody').append(`
                <tr class="small text-start">
                    <td style="position: sticky; left: 0; background: ${dark ? '#212730' : 'var(--darc-bg)'}; z-index: 5;">${annotation.scientific_name}</td>
                    <td style="z-index: 0;">${annotation.rank}</td>
                    <td>${annotation.aphia_id || '-'}</td>
                    <td>${annotation.phylum || '-'}</td>
                    <td>${annotation.class || '-'}</td>
                    <td>${annotation.subclass || '-'}</td>
                    <td>${annotation.order || '-'}</td>
                    <td>${annotation.suborder || '-'}</td>
                    <td>${annotation.family || '-'}</td>
                    <td>${annotation.subfamily || '-'}</td>
                    <td>${annotation.genus || '-'}</td>
                    <td>${annotation.subgenus || '-'}</td>
                    <td>${annotation.species || '-'}</td>
                    <td>${annotation.subspecies || '-'}</td>
                    <td>${annotation.timestamp || '-'}</td>
                    <td>${annotation.identification_remarks || '-'}</td>
                    <td>${annotation.identified_by || annotation.annotator}</td>
                    <td>${annotation.qualifier}</td>
                    <td>${annotation.reason}</td>
                    <td>${annotation.notes}</td>
                    <td>${annotation.attracted}</td>
                    <td>${annotation.lat || '-'}</td>
                    <td>${annotation.long || '-'}</td>
                    <td>${annotation.depth || '-'}</td>
                    <td>${annotation.count || '-'}</td>
                    <td>${annotation.categorical_abundance || '-'}</td>
                </tr>
            `);
            dark = !dark;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const url = new URL(window.location.href);

    for (const pair of url.searchParams.entries()) {
        if (pair[0].includes('deployment')) {
            const param = pair[1].split(' ');
            deployments.push(param.pop());
        }
    }
    $('#deploymentList').html(`${deployments.join(', ')}<br>`);

    updateHash();
});

window.onhashchange = () => {
    updateHash();
};
