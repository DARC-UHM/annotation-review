function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc/tator/sub/checklist${url.substring(url.indexOf('?'))}`;
}

function viewImageReferences() {
    window.open('/image-reference','name','height=900,width=550');
}

window.returnToCheckList = returnToCheckList;
window.viewImageReferences = viewImageReferences;

$(document).ready(()=> {
    $('#deploymentList').html(mediaNames.join(', '));

    if (window.location.href.includes('notes-and-remarks')) {
        $('#filterCtdNotes').css('display', 'inline-block');
    }
});
