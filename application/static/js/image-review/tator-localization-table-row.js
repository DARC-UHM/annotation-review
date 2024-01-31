export const tatorLocalizationRow = (localization, externalComment) => {
    return (`
        <tr>
            <td class="ps-5">
                <div class="row">
                    <div class="col-5">
                        Scientific Name:
                    </div>
                    <div class="col values">
                        ${localization.scientific_name}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Count:
                    </div>
                    <div class="col values">
                        ${localization.count}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Annotator:
                    </div>
                    <div class="col values">
                        ${localization.annotator}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Attracted:
                    </div>
                    <div class="col values">
                        ${localization.attracted}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Qualifier:
                    </div>
                    <div class="col values">
                        ${localization.qualifier}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Categorical Abundance:
                    </div>
                    <div class="col values">
                        ${localization.categorical_abundance}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Reason:
                    </div>
                    <div class="col values">
                        ${localization.reason}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Tentative ID:
                    </div>
                    <div class="col values">
                        ${localization.tentative_id}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Identification Remarks:
                    </div>
                    <div class="col values">
                        ${localization.identification_remarks}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Identified By:
                    </div>
                    <div class="col values">
                        ${localization.identified_by}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-5">
                        Notes:
                    </div>
                    <div class="col values">
                        ${localization.notes}<br>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-5">
                        <a class="editButton" href="https://cloud.tator.io/26/annotation/${localization.media_id}?frame=${localization.frame}" target="_blank">View on Tator</a>
                    </div>
                    <div class="col">
                        <button 
                            type="button" 
                            data-bs-toggle="modal" 
                            data-anno='${JSON.stringify(localization)}' 
                            data-bs-target="#externalReviewModal" 
                            class="editButton">
                                Add to external review
                        </button>
                    </div>
                </div>
            </td>
            <td class="text-center">
                <a href="${localization.frame_url}" target="_blank">
                    <div id="${localization.id}_image" class="position-relative" style="width: 580px;">
                        <img src="${localization.frame_url}" style="width: 580px;" alt="${localization.scientific_name}"/>
                        <div id="${localization.id}_overlay">
                        ${localization.type === 49
                            ? localization.points.map((point) => {
                                return `<span class="position-absolute tator-dot" style="top: ${point[1] * 100}%; left: ${point[0] * 100}%;"></span>`;
                            }).join('')
                            : localization.points.map((point, index) => {
                                if (index < 1) {
                                    return `<span
                                        class="position-absolute tator-box"
                                        style="top: ${point[1] * 100}%; left: ${point[0] * 100}%; width: ${localization.dimensions[0] * 100}%; height: ${localization.dimensions[1] * 100}%;"
                                    ></span>`
                                } else {
                                    return `<span class="position-absolute tator-dot" style="top: ${point[1] * 100}%; left: ${point[0] * 100}%;"></span>`;
                                }
                            }).join('')
                        }
                        </div>
                    </div>
                </a>
            </td>
        </tr>
    `);
};
