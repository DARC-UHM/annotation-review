import { updateFlashMessages } from '../../static/js/util/updateFlashMessages.js';
import { TatorLocalizationType } from '../../static/js/util/tatorLocalizationType.js';
import { externalReviewNoteSection } from './external-review-note-section.js';

export const tatorLocalizationRow = (localization, externalComment) => {
    const previewFrameUrl = localization.frame_url ? `${localization.frame_url}?preview=true` : localization.image_url;
    let localizationBoxId = null;
    let imageRefKey = localization.scientific_name;
    let scientificTentative = localization.scientific_name;
    if (localization.tentative_id) {
      imageRefKey += `~tid=${localization.tentative_id}`;
      scientificTentative += ` (${localization.tentative_id}?)`;
    }
    if (localization.morphospecies) {
      imageRefKey += `~m=${localization.morphospecies}`;
      scientificTentative += ` (${localization.morphospecies})`;
    }
    const notInImageRefs = !imageReferences || !imageReferences[imageRefKey];
    const thisSpecificImageInImageRefs = !notInImageRefs && imageReferences[imageRefKey] && imageReferences[imageRefKey].includes(localization.observation_uuid);
    for (const loco of localization.all_localizations) {
        if (loco.type === TatorLocalizationType.BOX) {
            localizationBoxId = loco.id;
            break;
        }
    }
    return (`
        <tr>
            <td class="ps-5 small">
                <div class="row" style="${localization.problems?.includes('Scientific Name') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Scientific Name:
                    </div>
                    <div class="col values">
                        <button
                            class="m-0 p-0 values"
                            style="background: none; color: #eee; border: none; cursor: text; user-select: text; width: fit-content;"
                            data-toggle="tooltip"
                            data-bs-placement="right"
                            data-bs-html="true"
                            title="<div class='text-start' style='max-width: none; white-space: nowrap;'>
                                       Phylum: ${localization.phylum ?? 'N/A'}<br>
                                       Class: ${localization.class ?? 'N/A'}<br>
                                       Order: ${localization.order ?? 'N/A'}<br>
                                       Family: ${localization.family ?? 'N/A'}<br>
                                       Genus: ${localization.genus ? `<i>${localization.genus}</i>` : 'N/A'}<br>
                                       Species: ${localization.species ? `<i>${localization.species}</i>` : 'N/A'}
                                   </div>"
                        >
                            ${localization.scientific_name}<br>
                        </button>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Annotator:
                    </div>
                    <div class="col values">
                        ${localization.annotator}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Count:
                    </div>
                    <div class="col values">
                        ${localization.count || '-'}<br>
                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('Attracted') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Attracted:
                    </div>
                    <div class="col values">
                        ${localization.attracted || '-'} <span class="small" style="color: var(--darc-text); font-weight: normal">
                            ${attractedConcepts
                                ? `${attractedConcepts[localization.scientific_name] === 0 ? '(Expected not attracted)'
                                        : attractedConcepts[localization.scientific_name] === 1 ? '(Expected attracted)'
                                            : attractedConcepts[localization.scientific_name] === 2 ? '(Expected either)'
                                                : '(Unknown - not in list)'
                                    }`
                                : ''
                            }
                        </span><br>

                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('Qualifier') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Qualifier:
                    </div>
                    <div class="col values">
                        ${localization.qualifier || '-'}<br>
                    </div>
                </div>
                ${localization.type === TatorLocalizationType.DOT
                    ? (`
                        <div class="row">
                            <div class="col-4">
                                Cat. Abundance:
                            </div>
                            <div class="col values">
                                ${localization.categorical_abundance || '-'}<br>
                            </div>
                        </div>
                    `) : ''
                }
                <div class="row" style="${localization.problems?.includes('Reason') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Reason:
                    </div>
                    <div class="col values">
                        ${localization.reason || '-'}<br>
                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('Tentative ID') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Tentative ID:
                    </div>
                    <div class="col values">
                        ${localization.tentative_id || '-'}
                        ${localization.problems?.includes('Tentative ID phylogeny no match') ? '<div style="color: red;">^ That\'s not my child!</div>' : '<br>'}
                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('Morphospecies') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Morphospecies:
                    </div>
                    <div class="col values">
                        ${localization.morphospecies || '-'}<br>
                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('ID Remarks') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        ID Remarks:
                    </div>
                    <div class="col values">
                        ${localization.identification_remarks || '-'}
                        <br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Identified By:
                    </div>
                    <div class="col values">
                        ${localization.identified_by || '-'}<br>
                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('Notes') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Notes:
                    </div>
                    <div class="col values">
                        ${localization.notes || '-'}
                        <br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Deployment:
                    </div>
                    <div class="col values">
                        ${localization.video_sequence_name || '-'}<br>
                    </div>
                </div>
                ${externalComment ? externalReviewNoteSection(externalComment, localization.uuid) : ''}
                <div class="row mt-2">
                    <div class="col-4">
                        <button
                            type="button"
                            data-bs-toggle="modal"
                            data-anno='${ JSON.stringify(localization) }'
                            data-bs-target="#editTatorLocalizationModal"
                            class="editButton"
                        >
                            Edit annotation
                        </button>
                        <br>
                        <a
                            class="editButton"
                            href="https://cloud.tator.io/26/annotation/${localization.media_id}?frame=${localization.frame}&selected_entity=${localization.observation_uuid}"
                            target="_blank"
                        >
                            View on Tator
                        </a>
                    </div>
                    <div class="col values">
                        ${ externalComment ? (
                            `<button
                                type="button"
                                data-bs-toggle="modal"
                                data-anno='${ JSON.stringify(localization) }'
                                data-bs-target="#externalReviewModal"
                                class="editButton"
                                onclick="updateReviewerName('${localization.observation_uuid}')">
                                    Change reviewer
                            </button>
                            <br>
                            <button
                                type="button"
                                data-bs-toggle="modal"
                                data-anno='${JSON.stringify(localization)}'
                                data-bs-target="#deleteReviewModal"
                                class="editButton">
                                    Delete from external review
                            </button>`
                        ) : (
                            `<button
                                type="button"
                                data-bs-toggle="modal"
                                data-anno='${ JSON.stringify(localization) }'
                                data-bs-target="#externalReviewModal"
                                class="editButton">
                                    Add to external review
                            </button>`
                        )}
                    </div>
                </div>
            </td>
            <td class="text-center" style="width: 50%;">
                ${localization.scientific_name
                    ? (`
                        <a href="${localization.frame_url || localization.image_url}" target="_blank">
                            <div
                                id="${localization.observation_uuid}_image"
                                class="position-relative"
                                style="width: 580px;"
                            >
                                <img
                                    id="${localization.observation_uuid}_img"
                                    src="${previewFrameUrl}"
                                    style="width: 580px;"
                                    alt="${localization.scientific_name}"
                                    onmouseout="mouseOut('${localization.observation_uuid}', '${previewFrameUrl}')"
                                />
                                <div id="${localization.observation_uuid}_overlay">
                                ${localization.all_localizations.map((loco, index) => {
                                    if (loco.type === TatorLocalizationType.BOX) {
                                        return `<span
                                                    class="position-absolute tator-box"
                                                    style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%; width: ${loco.dimensions[0] * 100}%; height: ${loco.dimensions[1] * 100}%;"
                                                    onmouseover="mouseOver('${localization.observation_uuid}', '${localizationBoxId}')"
                                                ></span>`;
                                    }
                                    return `<span class="position-absolute tator-dot" style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%;"></span>`;
                                }).join('')}
                                </div>
                                <div class="tator-loader-container">
                                    <div id="${localization.observation_uuid}_loading" class="tator-loader"></div>
                                </div>
                            </div>
                        </a>
                    `) : (`
                        <div class="d-flex" style="width: 580px; height: 300px; background: #191d24;">
                            <div class="m-auto">
                                Not logged in to Tator -
                                <a href="${window.location.origin}?login=tator" class="aquaLink">
                                    log in
                                </a>
                                to see image and details
                            </div>
                        </div>
                    `)
                }
                ${localization.all_localizations[0].type === TatorLocalizationType.BOX && localization.scientific_name
                    ? `
                        <div class="mt-2 small d-flex justify-content-center position-relative">
                            <div class="my-auto">
                                Good Image
                            </div>
                            <div class="checkbox-wrapper-5 ms-2 pt-1">
                                <div class="check">
                                    <input
                                        id="goodImage${localization.observation_uuid}"
                                        type="checkbox"
                                        ${localization.good_image ? 'checked' : ''}
                                        onchange="updateGoodImage('${JSON.stringify(localization.all_localizations.map((loco) => loco.elemental_id)).replaceAll('"', '*')}', '${localization.all_localizations[0].version}', this.checked)"
                                    >
                                    <label for="goodImage${localization.observation_uuid}"></label>
                                </div>
                            </div>
                            <div
                                class="position-absolute"
                                style="right: 0; top: 0; width: 1.5rem; height: 1.5rem;"
                            >
                                <div
                                    class="position-relative"
                                    data-toggle="tooltip"
                                    data-bs-placement="left"
                                    data-bs-html="true"
                                    title="${scientificTentative} ${
                                        notInImageRefs
                                            ? 'not saved in image reference list'
                                            : thisSpecificImageInImageRefs
                                                ? 'saved in image references (this specific image is saved)'
                                                : 'saved in image references (this specific image is not saved)'
                                      }"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6" style="opacity: 50%;">
                                      <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                                    </svg>
                                    <div class="position-absolute" style="left: -1rem; bottom: -0.5rem; width: 2rem; height: 2rem; color: #58da72">
                                        ${
                                            notInImageRefs
                                                ? ''
                                                : thisSpecificImageInImageRefs
                                                    ? (
                                                        `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check-all" viewBox="0 0 16 16">
                                                            <path d="M8.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L2.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093L8.95 4.992zm-.92 5.14.92.92a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 1 0-1.091-1.028L9.477 9.417l-.485-.486z"/>
                                                        </svg>`
                                                    ) : (
                                                      `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
                                                          <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                                                      </svg>`
                                                    )
                                        }
                                    </div>
                                </div>
                            </div>
                            ${thisSpecificImageInImageRefs
                                ? ''
                                : `
                                    <div class="position-absolute" style="right: -1.4rem; top: 0">
                                        <button
                                            class="aquaLink"
                                            data-toggle="tooltip"
                                            data-bs-placement="left"
                                            data-bs-html="true"
                                            data-localization='${ JSON.stringify(localization) }'
                                            data-bs-toggle="modal"
                                            data-bs-target="#addToImageReferencesModal"
                                            title="Add to image reference list"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16" stroke="currentColor" stroke-width="0.8">
                                                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4"/>
                                            </svg> 
                                        </button>
                                    </div>
                                `
                            }
                        </div>
                    ` : ''
                }
            </td>
        </tr>
    `);
};

async function updateGoodImage(localization_elemental_ids, version, checked) {
    const formData = new FormData();
    formData.append('version', version);
    for (const elemental_id of JSON.parse(localization_elemental_ids.replaceAll('*', '"'))) {
        formData.append('localization_elemental_ids', elemental_id);
    }
    formData.append('good_image', checked);
    const res = await fetch('/tator/localization/good-image', {
        method: 'PATCH',
        body: formData,
    });
    if (res.ok) {
        updateFlashMessages('Image status updated', 'success');
    } else {
        updateFlashMessages('Error updating image status', 'danger');
    }
}

window.updateGoodImage = updateGoodImage;

function mouseOver(uuid, boxId) {
    if (boxId === 'null') return;

    const mainImage = $(`#${uuid}_img`);
    const newImageUrl = `/tator/localization-image/${boxId}`;
    const newImage = new Image();

    $(`#${uuid}_loading`).show();
    newImage.src = newImageUrl;
    newImage.onload = () => {
        mainImage.attr('src', newImageUrl);
        $(`#${uuid}_overlay`).hide();
        $(`#${uuid}_loading`).hide();
    };
}

window.mouseOver = mouseOver;

function mouseOut(uuid, frameUrl) {
    $(`#${uuid}_img`).attr('src', frameUrl);
    $(`#${uuid}_overlay`).show();
}

window.mouseOut = mouseOut;

let localizationToAddToImageReferences = {};

async function addToImageReferences() {
    event.preventDefault();
    const formData = new FormData();
    const boxLocalization = localizationToAddToImageReferences.all_localizations[0];
    formData.append('scientific_name', localizationToAddToImageReferences.scientific_name);
    formData.append('deployment_name', localizationToAddToImageReferences.video_sequence_name);
    formData.append('section_id', localizationToAddToImageReferences.section_id);
    formData.append('tator_elemental_id', localizationToAddToImageReferences.observation_uuid);
    formData.append('localization_media_id', localizationToAddToImageReferences.media_id);
    formData.append('localization_frame', localizationToAddToImageReferences.frame);
    formData.append('localization_type', localizationToAddToImageReferences.type);
    formData.append('x', boxLocalization.points[0]);
    formData.append('y', boxLocalization.points[1]);
    formData.append('width', boxLocalization.dimensions[0]);
    formData.append('height', boxLocalization.dimensions[1]);
    if (localizationToAddToImageReferences.depth_m) {
        formData.append('depth_m', localizationToAddToImageReferences.depth_m);
    }
    if (localizationToAddToImageReferences.do_temp_c) {
        formData.append('temp_c', localizationToAddToImageReferences.do_temp_c);
    }
    if (localizationToAddToImageReferences.do_concentration_salin_comp_mol_L) {
        formData.append('salinity_m_l', localizationToAddToImageReferences.do_concentration_salin_comp_mol_L);
    }
    if (localizationToAddToImageReferences.morphospecies) {
        formData.append('morphospecies', localizationToAddToImageReferences.morphospecies);
    }
    if (localizationToAddToImageReferences.tentative_id) {
        formData.append('tentative_id', localizationToAddToImageReferences.tentative_id);
    }

    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const response = await fetch('/image-reference', {
        method: 'POST',
        body: formData,
    });
    if (response.ok) {
        updateFlashMessages('Successfully added record', 'success');
        location.reload();
    } else {
        const jsonResponse = await response.json();
        updateFlashMessages(Object.values(jsonResponse), 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.addToImageReferences = addToImageReferences;

$(document).ready(() => {
    $('#addToImageReferencesModal').on('show.bs.modal', (e) => {
        localizationToAddToImageReferences = $(e.relatedTarget).data('localization');
        let imageRefKey = localizationToAddToImageReferences.scientific_name;
        let scientificTentative = localizationToAddToImageReferences.scientific_name;
        if (localizationToAddToImageReferences.tentative_id) {
            imageRefKey += `~tid=${localizationToAddToImageReferences.tentative_id}`;
            scientificTentative += ` (${localizationToAddToImageReferences.tentative_id}?)`;
        }
        if (localizationToAddToImageReferences.morphospecies) {
            imageRefKey += `~m=${localizationToAddToImageReferences.morphospecies}`;
            scientificTentative += ` (${localizationToAddToImageReferences.morphospecies})`;
        }
        if (!imageReferences || !imageReferences[imageRefKey]) {
            $('#addToImageReferencesModalDetails').html(`Add new record <b>${scientificTentative}</b> to image references?`);
        } else {
            const numPhotos = imageReferences[imageRefKey].length;
            $('#addToImageReferencesModalDetails')
              .html(`Add new photo for <b>${scientificTentative}</b> to image references?
                     There ${numPhotos === 1 ? 'is' : 'are'} currently ${numPhotos} photo${numPhotos === 1 ? '' : 's'} saved for this concept.`);
        }
    });
});
