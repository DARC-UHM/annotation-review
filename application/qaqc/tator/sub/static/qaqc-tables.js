import { formattedNumber } from '../../../../static/js/util/formattedNumber.js';
import { downloadTsv } from '../../../static/downloadTsv.js';
import { caretDownFill, caretUpFill } from '../../../../static/js/icons.js';

function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc/tator/sub/checklist${url.substring(url.indexOf('?'))}`;
}

window.returnToCheckList = returnToCheckList;

function updateHash() {
    $('#annotationTable').find('tbody').html('');
    if (Object.keys(sizes).length) {
        // size table
        $('#countLabel').html('Unique Size/Taxa Combinations:&nbsp;&nbsp;');
        $('#totalCount').html(formattedNumber(Object.keys(sizes).length));

        $('#annotationTable').find('thead').html(`
            <tr class="thead-dark sticky-top" style="background-color: #1c2128; color: #eee;">
                <th scope="col">Scientific Name</th>
                <th scope="col">Tentative ID</th>
                <th scope="col">Morphospecies</th>
                <th scope="col">Size</th>
                <th scope="col">Count</th>
            </tr>
        `);
        for (const taxa of Object.keys(sizes).sort()) {
            $('#annotationTable').find('tbody').append(`
                <tr class="text-start">
                    <td>${sizes[taxa].scientific_name}</td>
                    <td>${sizes[taxa].tentative_id}</td>
                    <td>${sizes[taxa].morphospecies}</td>
                    <td>${sizes[taxa].size}</td>
                    <td>${sizes[taxa].count}</td>
                </tr>
            `);
        }
    } else if (Object.keys(uniqueTaxa).length) {
        // unique taxa table
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

        const substratesByMediaId = Object.fromEntries(substrates.map(group => [group.media_id, group.substrates]));
        let totalMedia = 0;

        $('#annotationTable').find('thead').html(`
            <tr class="text-start sticky-top" style="background-color: #1c2128; color: #eee;">
                <th scope="col">Media Name</th>
                <th scope="col">Megahabitat</th>
                <th scope="col">Substrates</th>
                <th scope="col">Quality</th>
                <th scope="col">Quality Notes</th>
            </tr>
        `);

        for (const media of mediaAttributes) {
            const megahabitat = media.attributes.Megahabitat;
            const mediaSubstrates = substratesByMediaId[media.id] ?? [];
            const substrateHtml = mediaSubstrates.map(substrate => `
                <div class="mb-2">
                    <div><strong>${substrate.timestamp ?? '??:??'}</strong></div>
                    <div class="ms-2">
                        <div><span>Primary:</span> ${substrate['Primary Substrate']}</div>
                        <div><span>Secondary:</span> ${substrate['Secondary Substrate']}</div>
                        <div><span>Relief:</span> ${substrate['Relief']} &nbsp;|&nbsp; <span>Bedforms:</span> ${substrate['Bedforms']}</div>
                    </div>
                </div>`).join('');
            totalMedia++;
            $('#annotationTable').find('tbody').append(`
                <tr class="text-start">
                    <td>${media.name}</td>
                    <td style="${megahabitat === undefined || megahabitat === 'Unset' ? 'color: yellow;' : ''}">${media.attributes.Megahabitat}</td>
                    <td>${substrateHtml}</td>
                    <td>${media.attributes['Video Quality']}</td>
                    <td>${media.attributes['Quality Notes']}</td>
                </tr>
            `);
        }

        $('#countLabel').html('Total Media:&nbsp;&nbsp;');
        $('#totalCount').html(formattedNumber(totalMedia));
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
            if (['count', 'depth_m'].includes(tempSortKey)) {
                filtered.sort((a, b) => b[tempSortKey] > a[tempSortKey]);
            } else {
                filtered.sort((a, b) => b[tempSortKey]?.localeCompare(a[tempSortKey]));
            }
            sortedAnnotations = filtered.concat(annotations.filter((anno) => !anno[tempSortKey]));
        } else {
            let filtered = annotations.filter((anno) => anno[sortKey]);
            if (['count', 'depth_m'].includes(sortKey)) {
                filtered.sort((a, b) => b[sortKey] < a[sortKey]);
            } else {
                filtered.sort((a, b) => a[sortKey]?.localeCompare(b[sortKey]));
            }
            sortedAnnotations = filtered.concat(annotations.filter((anno) => !anno[sortKey]));
        }

        $('#headerContainer').css('max-width', '100%');
        $('#tableContainer').removeClass('d-flex');
        $('#backButtonText').removeClass('d-xxl-inline');
        $('#downloadTsvButton').show();
        $('#downloadTsvButton').on('click', () => {
            downloadSummaryTsv();
        });
        $('#annotationTable').find('thead').html(`
            <tr class="text-start sticky-top" style="background: #1c2128; cursor: pointer;">
                <th
                  scope="col"
                  style="position: sticky; left: 0; background: #1c2128; z-index: 1;"
                  onclick="setSort('scientific_name')"
                  class="table-header-hover"
                >
                    <div class="d-flex">
                        scientificName
                        ${sortKey=== 'scientific_name' ? caretUpFill : sortKey=== 'scientific_name-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" style="cursor: default;">deployment</th>
                <th scope="col" onclick="setSort('rank')" class="table-header-hover">
                    <div class="d-flex">
                        taxonRank
                        ${sortKey=== 'rank' ? caretUpFill : sortKey=== 'rank-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" style="cursor: default;">aphiaId</th>
                <th scope="col" onclick="setSort('phylum')" class="table-header-hover">
                    <div class="d-flex">
                        phylum
                        ${sortKey=== 'phylum' ? caretUpFill : sortKey=== 'phylum-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('class')" class="table-header-hover">
                    <div class="d-flex">
                        class
                        ${sortKey=== 'class' ? caretUpFill : sortKey=== 'class-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subclass')" class="table-header-hover">
                    <div class="d-flex">
                        subclass
                        ${sortKey=== 'subclass' ? caretUpFill : sortKey=== 'subclass-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('order')" class="table-header-hover">
                    <div class="d-flex">
                        order
                        ${sortKey=== 'order' ? caretUpFill : sortKey=== 'order-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('suborder')" class="table-header-hover">
                    <div class="d-flex">
                        suborder
                        ${sortKey=== 'suborder' ? caretUpFill : sortKey=== 'suborder-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('family')" class="table-header-hover">
                    <div class="d-flex">
                        family
                        ${sortKey=== 'family' ? caretUpFill : sortKey=== 'family-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subfamily')" class="table-header-hover">
                    <div class="d-flex">
                        subfamily
                        ${sortKey=== 'subfamily' ? caretUpFill : sortKey=== 'subfamily-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('genus')" class="table-header-hover">
                    <div class="d-flex">
                        genus
                        ${sortKey=== 'genus' ? caretUpFill : sortKey=== 'genus-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subgenus')" class="table-header-hover">
                    <div class="d-flex">
                        subgenus
                        ${sortKey=== 'subgenus' ? caretUpFill : sortKey=== 'subgenus-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('species')" class="table-header-hover">
                    <div class="d-flex">
                        species
                        ${sortKey=== 'species' ? caretUpFill : sortKey=== 'species-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('subspecies')" class="table-header-hover">
                    <div class="d-flex">
                        subspecies
                        ${sortKey=== 'subspecies' ? caretUpFill : sortKey=== 'subspecies-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('morphospecies')" class="table-header-hover">
                    <div class="d-flex">
                        morphospecies
                        ${sortKey=== 'morphospecies' ? caretUpFill : sortKey=== 'morphospecies-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('tentative_id')" class="table-header-hover">
                    <div class="d-flex">
                        tentativeId
                        ${sortKey=== 'tentative_id' ? caretUpFill : sortKey=== 'tentative_id-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('timestamp')" class="table-header-hover">
                    <div class="d-flex">
                        observationTimestamp
                        ${sortKey=== 'timestamp' ? caretUpFill : sortKey=== 'timestamp-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('count')" class="table-header-hover">
                    <div class="d-flex">
                        individualCount
                        ${sortKey=== 'count' ? caretUpFill : sortKey=== 'count-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('categorical_abundance')" class="table-header-hover">
                    <div class="d-flex">
                        categoricalAbundance
                        ${sortKey=== 'categorical_abundance' ? caretUpFill : sortKey=== 'categorical_abundance-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('identification_remarks')" class="table-header-hover">
                    <div class="d-flex">
                        identificationRemarks
                        ${sortKey=== 'identification_remarks' ? caretUpFill : sortKey=== 'identification_remarks-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('size')" class="table-header-hover">
                    <div class="d-flex">
                        size
                        ${sortKey=== 'size' ? caretUpFill : sortKey=== 'size-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('annotator')" class="table-header-hover">
                    <div class="d-flex">
                        identifiedBy
                        ${sortKey=== 'annotator' ? caretUpFill : sortKey=== 'annotator-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('qualifier')" class="table-header-hover">
                    <div class="d-flex">
                        identificationQualifier
                        ${sortKey=== 'qualifier' ? caretUpFill : sortKey=== 'qualifier-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('reason')" class="table-header-hover">
                    <div class="d-flex">
                        reason
                        ${sortKey=== 'reason' ? caretUpFill : sortKey=== 'reason-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('notes')" class="table-header-hover">
                    <div class="d-flex">
                        notes
                        ${sortKey=== 'notes' ? caretUpFill : sortKey=== 'notes-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('upon')" class="table-header-hover">
                    <div class="d-flex">
                        upon
                        ${sortKey=== 'upon' ? caretUpFill : sortKey=== 'upon-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" style="cursor: default;">latitude</th>
                <th scope="col" style="cursor: default;">longitude</th>
                <th scope="col" onclick="setSort('depth_m')" class="table-header-hover">
                    <div class="d-flex">
                        depth(m)
                        ${sortKey=== 'depth_m' ? caretUpFill : sortKey=== 'depth_m-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" style="cursor: default;">doTemperature(C)</th>
                <th scope="col" style="cursor: default;">doSalinityComp(mol/L)</th>
                <th scope="col" onclick="setSort('primary_substrate')" class="table-header-hover">
                    <div class="d-flex">
                        primarySubstrate
                        ${sortKey=== 'primary_substrate' ? caretUpFill : sortKey=== 'primary_substrate-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('secondary_substrate')" class="table-header-hover">
                    <div class="d-flex">
                        secondarySubstrate
                        ${sortKey=== 'secondary_substrate' ? caretUpFill : sortKey=== 'secondary_substrate-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('relief')" class="table-header-hover">
                    <div class="d-flex">
                        relief
                        ${sortKey=== 'relief' ? caretUpFill : sortKey=== 'relief-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('bedforms')" class="table-header-hover">
                    <div class="d-flex">
                        bedforms
                        ${sortKey=== 'bedforms' ? caretUpFill : sortKey=== 'bedforms-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('substrate_notes')" class="table-header-hover">
                    <div class="d-flex">
                        substrateNotes
                        ${sortKey=== 'substrate_notes' ? caretUpFill : sortKey=== 'substrate_notes-desc' ? caretDownFill : ''}
                    </div>
                </th>
                <th scope="col" onclick="setSort('deployment_notes')" class="table-header-hover">
                    <div class="d-flex">
                        deploymentNotes
                        ${sortKey=== 'deployment_notes' ? caretUpFill : sortKey=== 'deployment_notes-desc' ? caretDownFill : ''}
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
                <tr class="text-start">
                    <td style="position: sticky; left: 0; background: ${dark ? '#212730' : 'var(--darc-bg)'}; z-index: 5;">
                        <a
                            class="editButton"
                            href="https://cloud.tator.io/26/annotation/${annotation.media_id}?frame=${annotation.frame}&selected_entity=${annotation.observation_uuid}"
                            target="_blank"
                        >
                            ${annotation.scientific_name}
                        </a>
                    </td>
                    <td style="z-index: 0;">${annotation.video_sequence_name}</td>
                    <td>${annotation.rank}</td>
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
                    <td>${annotation.morphospecies || '-'}</td>
                    <td>${annotation.tentative_id || '-'}</td>
                    <td>${annotation.timestamp || '-'}</td>
                    <td>${annotation.count || '-'}</td>
                    <td>${annotation.categorical_abundance || '-'}</td>
                    <td>${annotation.identification_remarks || '-'}</td>
                    <td>${annotation.size || '-'}</td>
                    <td>${annotation.identified_by || annotation.annotator}</td>
                    <td>${annotation.qualifier}</td>
                    <td>${annotation.reason}</td>
                    <td>${annotation.notes}</td>
                    <td>${annotation.upon}</td>
                    <td>${annotation.lat || '-'}</td>
                    <td>${annotation.long || '-'}</td>
                    <td>${annotation.depth_m || '-'}</td>
                    <td>${annotation.do_temp_c || '-'}</td>
                    <td>${annotation.do_concentration_salin_comp_mol_L || '-'}</td>
                    <td>${annotation.primary_substrate || '-'}</td>
                    <td>${annotation.secondary_substrate || '-'}</td>
                    <td>${annotation.relief || '-'}</td>
                    <td>${annotation.bedforms || '-'}</td>
                    <td>${annotation.substrate_notes || '-'}</td>
                    <td>${annotation.deployment_notes || '-'}</td>
                </tr>
            `);
            dark = !dark;
        }
    }
}

function downloadSummaryTsv() {
    const headers = [
        'scientificName',
        'deployment',
        'taxonRank',
        'aphiaId',
        'phylum',
        'class',
        'subclass',
        'order',
        'suborder',
        'family',
        'subfamily',
        'genus',
        'subgenus',
        'species',
        'subspecies',
        'morphospecies',
        'tentativeId',
        'observationTimestamp',
        'individualCount',
        'categoricalAbundance',
        'identificationRemarks',
        'size',
        'identifiedBy',
        'identificationQualifier',
        'reason',
        'notes',
        'upon',
        'latitude',
        'longitude',
        'depth(m)',
        'doTemperature(C)',
        'doSalinityComp(mol/L)',
        'primarySubstrate',
        'secondarySubstrate',
        'relief',
        'bedforms',
        'substrateNotes',
        'deploymentNotes',
    ];
    const rows = annotations.map((annotation) => [
        annotation.scientific_name,
        annotation.video_sequence_name,
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
        annotation.morphospecies,
        annotation.tentative_id,
        annotation.timestamp,
        annotation.count,
        annotation.categorical_abundance,
        annotation.identification_remarks,
        annotation.size,
        annotation.identified_by || annotation.annotator,
        annotation.qualifier,
        annotation.reason,
        annotation.notes,
        annotation.upon,
        annotation.lat,
        annotation.long,
        annotation.depth_m,
        annotation.do_temp_c,
        annotation.do_concentration_salin_comp_mol_L,
        annotation.primary_substrate,
        annotation.secondary_substrate,
        annotation.relief,
        annotation.bedforms,
        annotation.substrate_notes,
        annotation.deployment_notes,
    ]);
    downloadTsv(headers, rows, 'summary');
}

document.addEventListener('DOMContentLoaded', () => {
    $('#deploymentList').html(mediaNames.join(', '));
    updateHash();
});

window.onhashchange = () => {
    updateHash();
};
