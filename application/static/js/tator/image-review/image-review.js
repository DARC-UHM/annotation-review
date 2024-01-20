const knownAnnotators = {
    22: 'Jeff Drazen',
    24: 'Meagan Putts',
    25: 'Sarah Bingo',
    332: 'Nikki Cunanan',
    433: 'Aaron Judah',
};

$('#annotationTable tbody').remove();
$('#annotationTable').append('<tbody class="text-start"></tbody>');

for (const localization of localizations) {
    console.log(localization);
    $('#annotationTable').find('tbody').append(`
        <tr>
            <td class="ps-5">
                <div class="row">
                    <div class="col-4">
                        Scientific Name:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Scientific Name']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Tentative ID:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Tentative ID']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Annotator:
                    </div>
                    <div class="col values">
                        ${knownAnnotators[localization.created_by]}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Attracted:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Attracted']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Categorical Abundance:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Categorical Abundance']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Identification Remarks:
                    </div>
                    <div class="col values">
                        ${localization.attributes['IdentificationRemarks']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Identified By:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Identified By']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Notes:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Notes']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Qualifier:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Qualifier']}<br>
                    </div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Reason:
                    </div>
                    <div class="col values">
                        ${localization.attributes['Reason']}<br>
                    </div>
                </div>
                <br>
                <a class="editButton" href="https://cloud.tator.io/26/annotation/${localization.media}?frame=${localization.frame}" target="_blank">View on Tator</a>
            </td>
            <td class="text-center">
                <a href="${localization.frame_url}" target="_blank">
                    <img src="${localization.image_url}" style="width: 580px;" alt="${localization.attributes['Scientific Name']}"/>
                </a>
            </td>
        </tr>
    `);
}

/*
"Categorical Abundance": "--"
IdentificationRemarks: ""
"Identified By": ""
Notes: ""
"Public URL": ""
Qualifier: "indet."
Reason: "--"
"Scientific Name": "Neolithodes"
"Tentative ID": ""
 */

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
