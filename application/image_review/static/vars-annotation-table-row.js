import { externalReviewNoteSection } from './external-review-note-section.js';

export const varsAnnotationTableRow = (annotation, externalComment) => {
    let videoUrl = annotation.video_url;
    if (videoUrl) {
        videoUrl = `/video?link=${videoUrl.split('#t=')[0]}&time=${videoUrl.split('#t=')[1]}`;
    }
    let commentExists = false;
    if (externalComment) {
        for (const comment of externalComment.reviewer_comments) {
            if (comment.comment) {
                commentExists = true;
                break;
            }
        }
    }
    return (`
        <tr>
            <td class="ps-5 small">
                <div class="row">
                    <div class="col-4">
                        Concept:
                    </div>
                    <div class="col">
                        <button
                            class="m-0 p-0 values"
                            style="background: none; color: #eee; border: none; cursor: text; user-select: text;"
                            data-toggle="tooltip"
                            data-bs-placement="right"
                            data-bs-html="true"
                            title="<div class='text-start' style='max-width: none; white-space: nowrap;'>
                                       Phylum: ${annotation.phylum ?? 'N/A'}<br>
                                       Class: ${annotation.class ?? 'N/A'}<br>
                                       Order: ${annotation.order ?? 'N/A'}<br>
                                       Family: ${annotation.family ?? 'N/A'}<br>
                                       Genus: ${annotation.genus ? `<i>${annotation.genus}</i>` : 'N/A'}<br>
                                       Species: ${annotation.species ? `<i>${annotation.species}</i>` : 'N/A'}
                                   </div>"
                        >
                            ${annotation.concept}<br>
                        </button>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Annotator:
                    </div>
                    <div class="col values">
                        ${annotation.annotator}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        ID certainty:<br>
                    </div>
                    <div class="col values">
                        ${annotation.identity_certainty ? annotation.identity_certainty : '-'}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        ID reference:<br>
                    </div>
                    <div class="col values">
                        ${annotation.identity_reference ? annotation.identity_reference : '-'}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Upon:<br>
                    </div>
                    <div class="col values">
                        ${annotation.upon ? annotation.upon : '-'}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Comments:<br>
                    </div>
                    <div class="col values">
                        ${annotation.comment ? annotation.comment : '-'}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Guide photo:<br>
                    </div>
                    <div class="col values">
                        ${annotation.guide_photo ? annotation.guide_photo : '-'}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Depth:
                    </div>
                    <div class="col values">
                        ${annotation.depth || '?'} m<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Timestamp:
                    </div>
                    <div class="col values">
                        ${annotation.recorded_timestamp}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Video sequence:
                    </div>
                    <div class="col values">
                        ${annotation.video_sequence_name}<br>
                    </div>
                </div>
                ${externalComment ? externalReviewNoteSection(externalComment, annotation.observation_uuid) : ''}
                <div class="row mt-2">
                    <div class="col-4">
                        <button 
                            type="button" 
                            data-bs-toggle="modal" 
                            data-anno='${JSON.stringify(annotation)}' 
                            data-bs-target="#editVarsAnnotationModal" 
                            class="editButton">
                                Edit annotation
                        </button>
                        <br>
                        ${videoUrl
                            ? `<a class="editButton" href="${videoUrl}" target="_blank">See video</a>`
                            : '<span style="opacity: 50%;">Video not available</span>'
                        }
                        <br>
                    </div>
                    <div class="col values">
                        ${externalComment ? (
                            `<button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${JSON.stringify(annotation)}'
                                data-bs-target="#externalReviewModal" 
                                class="editButton" 
                                onclick="updateReviewerName('${annotation.observation_uuid}')">
                                    Change reviewer
                            </button>
                            <br>
                            <button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${JSON.stringify(annotation)}'
                                data-bs-target="#deleteReviewModal" 
                                class="editButton">
                                    Delete from external review
                            </button>`
                        ) : (
                            `<button 
                                type="button" 
                                data-bs-toggle="modal" 
                                data-anno='${JSON.stringify(annotation)}' 
                                data-bs-target="#externalReviewModal" 
                                class="editButton">
                                    Add to external review
                            </button>`
                        )}
                    </div>
                </div>
            </td>
            <td class="text-center">
                <a href="${annotation.image_url}" target="_blank">
                    <img src="${annotation.image_url}" style="width: 580px;"/>
                </a>
            </td>
        </tr>
    `);
};
