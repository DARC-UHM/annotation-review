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
    if (url.hash === `#sort=${sort}`) {
        url.hash = `sort=${sort}-desc`;
    } else {
        url.hash = `sort=${sort}`;
    }
    window.location.href = url;
}

window.setSort = setSort;

function updateHash() {
    $('#annotationTable').find('tbody').html('');
    if (Object.keys(uniqueTaxa).length) {
        // unique taxa table
        $('#downloadCsvButton').hide();
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

            if (firstBox && firstDot && firstBox < firstDot) {
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
    } else if (Object.keys(mediaAttributes).length) {
        // media table
        let totalMedia = 0;
        $('#downloadCsvButton').hide();
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
        let sortKey = hash.split('=')[1] || 'timestamp';
        let dark = true;
        let sortedAnnotations;

        if (sortKey.includes('-desc')) {
            const tempSortKey = sortKey.split('-')[0];
            let filtered = annotations.filter((anno) => anno[tempSortKey]);
            if (sortKey.includes('count')) {
                filtered.sort((a, b) => b[tempSortKey] > a[tempSortKey]);
            } else {
                filtered.sort((a, b) => b[tempSortKey]?.localeCompare(a[tempSortKey]));
            }
            sortedAnnotations = filtered.concat(annotations.filter((anno) => !anno[tempSortKey]));
        } else {
            let filtered = annotations.filter((anno) => anno[sortKey]);
            if (sortKey.includes('count')) {
                filtered.sort((a, b) => b[sortKey] < a[sortKey]);
            } else {
                filtered.sort((a, b) => b[sortKey]?.localeCompare(a[sortKey]));
            }
            sortedAnnotations = filtered.concat(annotations.filter((anno) => !anno[sortKey]));
        }

        $('#headerContainer').css('max-width', '100%');
        $('#tableContainer').removeClass('d-flex');
        $('#backButtonText').removeClass('d-xxl-inline');
        $('#downloadCsvButton').show();
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
                        ${sortKey=== 'scientific_name' ? caretUpFill : sortKey=== 'scientific_name-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('rank')" class="table-header-hover">
                    <div class="d-flex">
                        TaxonRank
                        ${sortKey=== 'rank' ? caretUpFill : sortKey=== 'rank-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" style="cursor: default;">AphiaID</th>
                <th scope="col" onclick="setSort('phylum')" class="table-header-hover">
                    <div class="d-flex">
                        Phylum
                        ${sortKey=== 'phylum' ? caretUpFill : sortKey=== 'phylum-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('class')" class="table-header-hover">
                    <div class="d-flex">
                        Class
                        ${sortKey=== 'class' ? caretUpFill : sortKey=== 'class-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subclass')" class="table-header-hover">
                    <div class="d-flex">
                        Subclass
                        ${sortKey=== 'subclass' ? caretUpFill : sortKey=== 'subclass-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('order')" class="table-header-hover">
                    <div class="d-flex">
                        Order
                        ${sortKey=== 'order' ? caretUpFill : sortKey=== 'order-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('suborder')" class="table-header-hover">
                    <div class="d-flex">
                        Suborder
                        ${sortKey=== 'suborder' ? caretUpFill : sortKey=== 'suborder-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('family')" class="table-header-hover">
                    <div class="d-flex">
                        Family
                        ${sortKey=== 'family' ? caretUpFill : sortKey=== 'family-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subfamily')" class="table-header-hover">
                    <div class="d-flex">
                        Subfamily
                        ${sortKey=== 'subfamily' ? caretUpFill : sortKey=== 'subfamily-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('genus')" class="table-header-hover">
                    <div class="d-flex">
                        Genus
                        ${sortKey=== 'genus' ? caretUpFill : sortKey=== 'genus-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subgenus')" class="table-header-hover">
                    <div class="d-flex">
                        Subgenus
                        ${sortKey=== 'subgenus' ? caretUpFill : sortKey=== 'subgenus-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('species')" class="table-header-hover">
                    <div class="d-flex">
                        Species
                        ${sortKey=== 'species' ? caretUpFill : sortKey=== 'species-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subspecies')" class="table-header-hover">
                    <div class="d-flex">
                        Subspecies
                        ${sortKey=== 'subspecies' ? caretUpFill : sortKey=== 'subspecies-desc' ? caretDownFill : ''}
                    </div>
                </th>
                
                <th scope="col">ObservationTimestamp</th> <!-- todo  <<<< -->
                
                <th scope="col" onclick="setSort('identification_remarks')" class="table-header-hover">
                    <div class="d-flex">
                        IdentificationRemarks
                        ${sortKey=== 'identification_remarks' ? caretUpFill : sortKey=== 'identification_remarks-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('annotator')" class="table-header-hover">
                    <div class="d-flex">
                        IdentifiedBy
                        ${sortKey=== 'annotator' ? caretUpFill : sortKey=== 'annotator-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('qualifier')" class="table-header-hover">
                    <div class="d-flex">
                        IdentificationQualifier
                        ${sortKey=== 'qualifier' ? caretUpFill : sortKey=== 'qualifier-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('reason')" class="table-header-hover">
                    <div class="d-flex">
                        Reason
                        ${sortKey=== 'reason' ? caretUpFill : sortKey=== 'reason-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('notes')" class="table-header-hover">
                    <div class="d-flex">
                        Notes
                        ${sortKey=== 'notes' ? caretUpFill : sortKey=== 'notes-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('attracted')" class="table-header-hover">
                    <div class="d-flex">
                        Attracted
                        ${sortKey=== 'attracted' ? caretUpFill : sortKey=== 'attracted-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" style="cursor: default;">Latitude</th>
                <th scope="col" style="cursor: default;">Longitude</th>
                <th scope="col" onclick="setSort('depth')" class="table-header-hover">
                    <div class="d-flex">
                        DepthInMeters
                        ${sortKey=== 'depth' ? caretUpFill : sortKey=== 'depth-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('count')" class="table-header-hover">
                    <div class="d-flex">
                        IndividualCount
                        ${sortKey=== 'count' ? caretUpFill : sortKey=== 'count-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('categorical_abundance')" class="table-header-hover">
                    <div class="d-flex">
                        CategoricalAbundance
                        ${sortKey=== 'categorical_abundance' ? caretUpFill : sortKey=== 'categorical_abundance-desc' ? caretDownFill : ''}
                    </div>
                </th>
            </tr>
        `);
        for (const annotation of sortedAnnotations) {
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

function downloadCsv() {
    const headers = [
        'ScientificName',
        'TaxonRank',
        'AphiaID',
        'Phylum',
        'Class',
        'Subclass',
        'Order',
        'Suborder',
        'Family',
        'Subfamily',
        'Genus',
        'Subgenus',
        'Species',
        'Subspecies',
        'ObservationTimestamp',
        'IdentificationRemarks',
        'IdentifiedBy',
        'IdentificationQualifier',
        'Reason',
        'Notes',
        'Attracted',
        'Latitude',
        'Longitude',
        'DepthInMeters',
        'IndividualCount',
        'CategoricalAbundance',
    ];
    const rows = annotations.map((annotation) => [
        annotation.scientific_name,
        annotation.rank,
        annotation.aphia_id,
        annotation.phylum,
        annotation.class,
        annotation.subclass,
        annotation.order,
        annotation.suborder,
        annotation.family,
        annotation.subfamily,
        annotation.genus,
        annotation.subgenus,
        annotation.species,
        annotation.subspecies,
        annotation.timestamp,
        annotation.identification_remarks,
        annotation.identified_by || annotation.annotator,
        annotation.qualifier,
        annotation.reason,
        annotation.notes,
        annotation.attracted,
        annotation.lat,
        annotation.long,
        annotation.depth,
        annotation.count,
        annotation.categorical_abundance,
    ]);

    let csvContent = 'data:text/csv;charset=utf-8,';
    csvContent += headers.join(',') + '\n';
    rows.forEach((rowArray) => {
        const row = rowArray.join(',');
        csvContent += row + '\n';
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${deployments.join('|')}.csv`);
    document.body.appendChild(link);
    link.click();
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

    $('#downloadCsvButton').on('click', () => {
        downloadCsv();
    });

    updateHash();
});

window.onhashchange = () => {
    updateHash();
};
