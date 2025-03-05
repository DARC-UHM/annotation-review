import { updateFlashMessages } from '../util/updateFlashMessages.js';

export const tatorLocalizationRow = (localization, externalComment) => {
    const previewFrameUrl = localization.frame_url ? `${localization.frame_url}?preview=true` : localization.image_url;
    let localizationBoxId = null;
    for (const loco of localization.all_localizations) {
        if (loco.type === 48) {
            localizationBoxId = loco.id;
            break;
        }
    }
    return (`
        <tr>
            <td class="ps-5">
                <div class="row" style="${localization.problems?.includes('Scientific Name') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Scientific Name:
                    </div>
                    <div class="col values">
                        <button
                            class="m-0 p-0 values"
                            style="background: none; color: #eee; border: none; cursor: default;"
                            data-toggle="tooltip"
                            data-bs-placement="right"
                            data-bs-html="true"
                            title="Phylum: ${localization.phylum ?? 'N/A'}<br>
                                   Class: ${localization.class ?? 'N/A'}<br>
                                   Order: ${localization.order ?? 'N/A'}<br>
                                   Family: ${localization.family ?? 'N/A'}<br>
                                   Genus: ${localization.genus ?? 'N/A'}<br>
                                   Species: ${localization.species ?? 'N/A'}"
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
                <div class="row">
                    <div class="col-4">
                        Cat. Abundance:
                    </div>
                    <div class="col values">
                        ${localization.categorical_abundance || '-'}<br>
                    </div>
                </div>
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
                ${externalComment
                    ? `
                        <div class="row mt-2">
                            <div class="col-4">
                                Reviewer comments:<br>
                                ${externalComment.unread
                                    ? `
                                        <button class="editButton" onclick="markCommentRead('${localization.observation_uuid}')">
                                            Mark read
                                        </button>
                                    ` : ''
                                }
                            </div>
                            <div class="col values">
                                ${externalComment.reviewer_comments?.map(item => {
                                    return item.comment
                                        ? `
                                            ${item.comment.length
                                                ? `
                                                    ${item.comment}<br>
                                                    <span class="small fw-normal">
                                                        - <a href="https://hurlstor.soest.hawaii.edu:5000/review/${item.reviewer}" class="aquaLink" target="_blank">
                                                            ${item.reviewer}
                                                        </a> ${item.date_modified}
                                                    </span>
                                                ` : 'N/A'}<br><br>`
                                        : `
                                            <span class="fw-normal">
                                                Awaiting comment from <a href="https://hurlstor.soest.hawaii.edu:5000/review/${item.reviewer}" class="aquaLink" target="_blank">${item.reviewer}</a>
                                                <div class="small">Added ${item.date_modified.substring(0, 6)}</div>
                                            </span><br>
                                        `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''
                }
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
                                    onmouseover="mouseOver('${localization.observation_uuid}', '${localizationBoxId}')"
                                    onmouseout="mouseOut('${localization.observation_uuid}', '${previewFrameUrl}')"
                                />
                                <div id="${localization.observation_uuid}_overlay">
                                ${localization.all_localizations.map((loco, index) => {
                                    if (loco.type === 48) { // 48 is a box
                                        return `<span
                                                    class="position-absolute tator-box"
                                                    style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%; width: ${loco.dimensions[0] * 100}%; height: ${loco.dimensions[1] * 100}%;"
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
                ${localization.all_localizations[0].type === 48 && localization.scientific_name
                    ? `
                        <div class="mt-2 small d-flex justify-content-center">
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
    const newImageUrl = `/tator-localization/${boxId}`;
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
