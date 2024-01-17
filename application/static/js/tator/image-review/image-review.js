
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
                    ${localization.created_by}<br>
                </div>
            </div>
            <td class="text-center">
                <a href="${localization.media}" target="_blank">
                    <img src="${localization.media}" style="width: 580px;"/>
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
