const slideshows = {}; // { fullName: { currentIndex, maxIndex, depthColors } }
const taxonRanks = ['phylum', 'class', 'order', 'family', 'genus'];
const phyla = {};

let filteredImageReferences = imageReferences;
let phylogenyFilter = {};
let keywordFilter = '';

$(document).ready(() => {
    populatePhyla();
    getFiltersFromHash();
    updatePhylogenyFilterSelects();
    updateImageGrid();
    $('#keywordFilterInput').on('input', (e) => {
        keywordFilter = e.target.value;
        updateHash();
    });
});

window.onhashchange = () => {
    getFiltersFromHash();
    updatePhylogenyFilterSelects();
    updateImageGrid();
};

function updateHash() {
    location.hash = Object.keys(phylogenyFilter)
        .map((key) => `${key}=${phylogenyFilter[key]}`)
        .join('&');
    if (keywordFilter) {
        location.hash += location.hash.length > 0 ? '&' : '#';
        location.hash += `keyword=${keywordFilter}`;
    }
}

function updateImageGrid() {
    $('#imageGrid').empty();
    filteredImageReferences = imageReferences;
    for (const key of Object.keys(phylogenyFilter)) {
        filteredImageReferences = filteredImageReferences.filter((imageRef) => {
            return imageRef[key === 'class' ? 'class_name' : key]?.toLowerCase().includes(phylogenyFilter[key].toLowerCase());
        });
    }
    if (keywordFilter) {
        filteredImageReferences = filteredImageReferences.filter((imageRef) => {
            const properties = [
                'scientific_name',
                'expedition_added',
                'phylum',
                'class_name',
                'order',
                'family',
                'genus',
                'species',
                'tentative_id',
                'morphospecies',
            ];
            return properties.some((property) => imageRef[property]?.toLowerCase().includes(keywordFilter.toLowerCase()));
        });
    }
    filteredImageReferences.forEach((imageRef) => {
        const nameSuffix = imageRef.tentative_id
            ? ` (${imageRef.tentative_id}?)`
            : imageRef.morphospecies
                ? ` (${imageRef.morphospecies})`
                : '';
        const fullName = imageRef.scientific_name + nameSuffix;
        const photoKey = fullName.replaceAll(' ', '-');
        slideshows[photoKey] = { currentIndex: 0, maxIndex: imageRef.photo_records.length - 1, depthColors: [] };
        $('#imageGrid').append(`
            <div class="col-lg-3 col-md-4 col-sm-6 col-12 p-1">
                <div class="rounded-3 small h-100" style="background: #1b1f26;">
                    <div class="py-2 fw-bold rounded-top m-0 position-relative" style="background: #171a1f;">
                        ${fullName}
                        <div class="position-absolute d-flex h-100" style="right: 0; top: 0;">
                            <div
                                id="${photoKey}-depthColor"
                                class="my-auto me-2"
                                style="width: 1.5rem; height: 1rem; background: orange; border-radius: 0.1rem;"
                            ></div>
                        </div>
                    </div>
                    <div
                        class="d-flex justify-content-center w-100 position-relative"
                        style="aspect-ratio: 1.5 / 1;"
                    >
                        ${imageRef.photo_records.map((photoRecord, index) => {
                            const imageUrl = `https://hurlstor.soest.hawaii.edu:5000/tator-localization-image/${photoRecord.tator_id}`;
                            if (photoRecord.depth_m >= 1000) {
                                slideshows[photoKey].depthColors.push('#000');
                            } else if (photoRecord.depth_m >= 800) {
                                slideshows[photoKey].depthColors.push('#ca1ec9');
                            } else if (photoRecord.depth_m >= 600) {
                                slideshows[photoKey].depthColors.push('#0b24fb');
                            } else if (photoRecord.depth_m >= 400) {
                                slideshows[photoKey].depthColors.push('#19af54');
                            } else if (photoRecord.depth_m >= 200) {
                                slideshows[photoKey].depthColors.push('#fffd38');
                            } else {
                                slideshows[photoKey].depthColors.push('#fc0d1b');
                            }
                            return `<div id="${photoKey}-${index}" style="display: ${index > 0 ? 'none' : 'block'};" class="position-relative pb-1 px-1">
                                <a href="${imageUrl}" target="_blank">
                                    <img src="${imageUrl}" class="mw-100 mh-100 d-block rounded-1 m-auto" alt="${fullName}">
                                </a>
                                ${imageRef.photo_records.length > 1 
                                    ? `<div class="photo-slideshow-numbers" style="margin-left: -0.25rem;">${index + 1} / ${imageRef.photo_records.length}</div>`
                                    : ''
                                }
                            </div>`;
                        }).join('')}
                        <a
                            class="photo-slideshow-arrows photo-slideshow-prev"
                            onclick="changeSlide('${photoKey}', -1)"
                            ${imageRef.photo_records.length < 2 ? "hidden" : ""}
                        >
                            &#10094;
                        </a>
                        <a
                            class="photo-slideshow-arrows photo-slideshow-next"
                            onclick="changeSlide('${photoKey}', 1)"
                            ${imageRef.photo_records.length < 2 ? "hidden" : ""}
                        >
                            &#10095;
                        </a>
                    </div>
                    
                </div>
            </div>
        `);
        const depthIndicatorElement = document.getElementById(`${photoKey}-depthColor`);
        depthIndicatorElement.style.background = slideshows[photoKey].depthColors[0];
        depthIndicatorElement.title = `Depth: ${imageRef.photo_records[0].depth_m}m`;
    });
}

function getFiltersFromHash() {
    phylogenyFilter = {};
    keywordFilter = '';
    const hash = window.location.hash.substring(1);
    if (hash === '') {
        return;
    }
    for (const hashPair of hash.split('&')) {
        const key = hashPair.split('=')[0];
        const value = hashPair.split('=')[1].replaceAll('%20', ' ');
        if (key === 'keyword') {
            keywordFilter = value;
            continue;
        }
        phylogenyFilter[key] = value;
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
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum]));
            break;
        case 'order':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum][phylogenyFilter.class]));
            break;
        case 'family':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum][phylogenyFilter.class][phylogenyFilter.order]));
            break;
        case 'genus':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum][phylogenyFilter.class][phylogenyFilter.order][phylogenyFilter.family]));
            break;
        default:
            rankOptions = [];
    }
    $('#filterList').append(`
        <span id="${taxonRank}Filter">
            <span class="position-relative">
                <select
                    id="${taxonRank}FilterSelect"
                    onchange="updatePhylogenyFilter('${taxonRank}')"
                    style="background: var(--darc-input-bg); height: 2rem;"
                >
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
        delete phylogenyFilter[taxonRank];
    } else {
        phylogenyFilter[taxonRank] = selected;
    }
    // remove all lower ranks
    for (let i = taxonRanks.indexOf(taxonRank) + 1; i < taxonRanks.length; i++) {
        delete phylogenyFilter[taxonRanks[i]];
    }
    updateHash();
}

window.updatePhylogenyFilter = updatePhylogenyFilter;

function updatePhylogenyFilterSelects() {
    $('#filterList').empty();
    for (const filterName of Object.keys(phylogenyFilter)) {
        addPhylogenyFilterSelect(filterName, phylogenyFilter[filterName]);
        if (filterName !== 'genus') {
            $('#filterList').append('→');
        }
    }
    for (const taxonRank of taxonRanks) {
        if (!phylogenyFilter[taxonRank]) {
            addPhylogenyFilterSelect(taxonRank, '');
            break;
        }
    }
}

function changeSlide(photoKey, slideMod) {
    const { currentIndex, maxIndex } = slideshows[photoKey];
    const slideIndex = (currentIndex + slideMod + maxIndex + 1) % (maxIndex + 1);
    slideshows[photoKey].currentIndex = slideIndex;
    // hide all slides except the current one
    for (let i = 0; i <= slideshows[photoKey].maxIndex; i++) {
        document.getElementById(`${photoKey}-${i}`).style.display = i === slideIndex ? 'block' : 'none';
    }
    document.getElementById(`${photoKey}-depthColor`).style.background = slideshows[photoKey].depthColors[slideIndex];
}

window.changeSlide = changeSlide;
