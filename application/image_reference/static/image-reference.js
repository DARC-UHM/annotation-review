const taxonRanks = ['phylum', 'class', 'order', 'family', 'genus', 'species'];
const phyla = {};

let filteredImageReferences = imageReferences;
let filter = {};

$(document).ready(() => {
    populatePhyla();
    console.log(phyla);
    getFiltersFromHash();
    updatePhylogenyFilterSelects();
    updateImageGrid();
});

window.onhashchange = () => {
    getFiltersFromHash();
    updatePhylogenyFilterSelects();
    updateImageGrid();
};

function updateImageGrid() {
    $('#imageGrid').empty();
    filteredImageReferences = imageReferences;
    for (const key of Object.keys(filter)) {
        filteredImageReferences = filteredImageReferences.filter((imageRef) => {
            return imageRef[key === 'class' ? 'class_name' : key]?.toLowerCase().includes(filter[key].toLowerCase());
        });
    }
    filteredImageReferences.forEach((imageRef) => {
        const hurlUrl = 'https://hurlstor.soest.hawaii.edu:5000';
        const nameSuffix = imageRef.tentative_id
            ? ` (${imageRef.tentative_id}?)`
            : imageRef.morphospecies
                ? ` (${imageRef.morphospecies})`
                : '';
        $('#imageGrid').append(`
            <div class="col-lg-3 col-md-4 col-sm-6 col-12 p-1">
                <div class="rounded-3 small p-2 h-100" style="background: #1b1f26">
                    <div
                        class="d-flex justify-content-center align-items-center w-100"
                        style="aspect-ratio: 1.5 / 1;"
                    >
                        <img
                            src="${hurlUrl}${imageRef.photos[0]}"
                            class="mw-100 mh-100 rounded-2"
                            alt="${imageRef.scientific_name}${nameSuffix}"
                        >
                    </div>
                    <p class="my-2">
                        ${imageRef.scientific_name}${nameSuffix}
                    </p>
                </div>
            </div>
        `);
    });
}

function getFiltersFromHash() {
    filter = {};
    const hash = window.location.hash.substring(1);
    if (hash === '') {
        return;
    }
    for (const hashPair of hash.split('&')) {
        filter[hashPair.split('=')[0]] = hashPair.split('=')[1].replaceAll('%20', ' ');
    }
}

function populatePhyla() {
    // populate available phylogeny (probs should just save this info on the backend)
    imageReferences.forEach((imageRef) => {
        if (!phyla[imageRef.phylum]) {
            phyla[imageRef.phylum] = {};
        }
        if (!phyla[imageRef.phylum][imageRef.class_name]) {
            phyla[imageRef.phylum][imageRef.class_name] = {};
        }
        if (!phyla[imageRef.phylum][imageRef.class_name][imageRef.order]) {
            phyla[imageRef.phylum][imageRef.class_name][imageRef.order] = {};
        }
        if (!phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family]) {
            phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family] = {};
        }
        if (!phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family][imageRef.genus]) {
            phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family][imageRef.genus] = {};
        }
    });
}

function addPhylogenyFilterSelect(taxonRank, selectedValue) {
    let rankOptions;
    switch (taxonRank) {
        case 'phylum':
            rankOptions = (Object.keys(phyla));
            break;
        case 'class':
            rankOptions = (Object.keys(phyla[filter.phylum]));
            break;
        case 'order':
            rankOptions = (Object.keys(phyla[filter.phylum][filter.class]));
            break;
        case 'family':
            rankOptions = (Object.keys(phyla[filter.phylum][filter.class][filter.order]));
            break;
        case 'genus':
            rankOptions = (Object.keys(phyla[filter.phylum][filter.class][filter.order][filter.family]));
            break;
    }
    $('#filterList').append(`
        <span id="${taxonRank}Filter" class="small">
            <span class="position-relative">
                <select id="${taxonRank}FilterSelect" onchange="updatePhylogenyFilter('${taxonRank}')" style="background: #2d3541;">
                    <option value="all">Any ${taxonRank}</option>
                    ${rankOptions.map((option) => 
                        `<option value="${option}" ${selectedValue === option ? 'selected' : ''}>${option}</option>`
                    )}
                </select>
                <span class="position-absolute dropdown-chev">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-down" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
                    </svg>
                </span>
            </span>
        </span>
    `);
}

function updatePhylogenyFilter(taxonRank) {
    const selected = $(`#${taxonRank}FilterSelect`).val();
    if (selected === 'all') {
        delete filter[taxonRank];
    } else {
        filter[taxonRank] = selected;
    }
    // remove all lower ranks
    for (let i = taxonRanks.indexOf(taxonRank) + 1; i < taxonRanks.length; i++) {
        delete filter[taxonRanks[i]];
    }
    location.hash = Object.keys(filter)
        .map((key) => `${key}=${filter[key]}`)
        .join('&');
}

window.updatePhylogenyFilter = updatePhylogenyFilter;

function updatePhylogenyFilterSelects() {
    $('#filterList').empty();
    for (const filterName of Object.keys(filter)) {
        addPhylogenyFilterSelect(filterName, filter[filterName]);
        if (filterName !== 'genus') {
            $('#filterList').append('→');
        }
    }
    for (const taxonRank of taxonRanks) {
        if (!filter[taxonRank]) {
            addPhylogenyFilterSelect(taxonRank, '');
            break;
        }
    }
}
