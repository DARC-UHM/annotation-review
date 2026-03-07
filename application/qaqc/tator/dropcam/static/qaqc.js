function returnToCheckList() {
    const url = window.location.href;
    window.location.href = `/qaqc/tator/dropcam/checklist${url.substring(url.indexOf('?'))}`;
}

function viewAttractedList() {
    window.open('/qaqc/tator/dropcam/attracted-list','name','height=900,width=550');
}

function viewImageReferences() {
    window.open('/image-reference','name','height=900,width=550');
}

window.returnToCheckList = returnToCheckList;
window.viewAttractedList = viewAttractedList;
window.viewImageReferences = viewImageReferences;

$(document).ready(()=> {
    $('#deploymentList').html(deploymentNames.join(', '));

    if (window.location.href.includes('attracted-not-attracted')) {
        $('#attractedNotAttractedSubHeading').css('display', 'inline-block');
        $('#attractedNotAttractedPopupButton').css('display', 'inline-block');
    } else if (window.location.href.includes('exists-in-image-references')) {
        $('#imageRefSubHeading').css('display', 'inline-block');
        $('#imageRefPopupButton').css('display', 'inline-block');
    } else if (window.location.href.includes('notes-and-remarks')) {
        $('#filterCtdNotes').css('display', 'inline-block');
    }
});
