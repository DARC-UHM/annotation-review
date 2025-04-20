let filteredImageReferences = imageReferences;
let filter = {};

function updateImageGrid() {
    $('#imageGrid').empty();
    filteredImageReferences = imageReferences;
    for (const key of Object.keys(filter)) {
        filteredImageReferences = filteredImageReferences.filter((imageRef) => {
            return imageRef[key]?.toLowerCase().includes(filter[key].toLowerCase());
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
        filter[hashPair.split('=')[0]] = hashPair.split('=')[1];
    }
}

$(document).ready(() => {
    getFiltersFromHash();
    updateImageGrid();
});

window.onhashchange = () => {
    getFiltersFromHash();
    updateImageGrid();
};
