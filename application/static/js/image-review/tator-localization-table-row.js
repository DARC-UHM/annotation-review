export const tatorLocalizationRow = (localization, externalComment) => {
    console.log(localization)
    return (`
        <tr>
            <td class="ps-5">
                <div class="row" style="${localization.problems?.includes('Scientific Name') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        Scientific Name:
                    </div>
                    <div class="col values">
                        ${localization.scientific_name}<br>
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
                        ${localization.attracted || '-'}<br>
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
                        ${localization.problems?.includes('Tentative ID phylogeny no match') ? '<div style="color: red;">^ Does not match phylogeny of scientific name</div>' : '<br>'}
                    </div>
                </div>
                <div class="row" style="${localization.problems?.includes('ID Remarks') ? 'color: yellow;' : ''}">
                    <div class="col-4">
                        ID Remarks:
                    </div>
                    <div class="col values">
                        ${localization.identification_remarks || '-'}<br>
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
                        ${localization.notes?.includes(',') ? '<div style="color: red;">^ REMOVE COMMAS ^</div>' : ''}
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
                                ${externalComment.reviewer_comments.map(item => {
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
                            class="editButton">
                                Edit annotation
                        </button>
                        <br>
                        <a
                            class="editButton"
                            href="https://cloud.tator.io/26/annotation/${localization.media_id}?playQuality=720&playbackRate=1&frame=${localization.frame}&version=45&lock=0&fill_boxes=1&toggle_text=1&selected_entity=${localization.observation_uuid}&selected_type=dot_49"
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
                <a href="${localization.frame_url || localization.image_url}" target="_blank">
                    <div id="${localization.observation_uuid}_image" class="position-relative" style="width: 580px;">
                        <img src="${localization.frame_url || localization.image_url}" style="width: 580px;" alt="${localization.scientific_name}"/>
                        <div id="${localization.observation_uuid}_overlay">
                        ${localization.all_localizations.map((loco, index) => {
                            if (loco.type === 48) {
                                return `<span
                                            class="position-absolute tator-box"
                                            style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%; width: ${loco.dimensions[0] * 100}%; height: ${loco.dimensions[1] * 100}%;"
                                        ></span>`;
                            }
                            return `<span class="position-absolute tator-dot" style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%;"></span>`;
                        }).join('')}
                        </div>
                    </div>
                </a>
            </td>
        </tr>
    `);
};
