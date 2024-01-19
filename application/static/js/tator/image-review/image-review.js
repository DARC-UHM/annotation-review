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
                    Annotator:
                </div>
                <div class="col values">
                    ${knownAnnotators[localization.created_by]}<br>
                </div>
            </div>
            <td class="text-center">
                <a href="${localization}" target="_blank">
                    <img src="${localization.image_url}" style="width: 580px;"/>
                </a>
            </td>
        </tr>
    `);
}

// get rid of loading screen if back button is pressed (mozilla)
$(window).bind('pageshow', (event) => {
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
});
