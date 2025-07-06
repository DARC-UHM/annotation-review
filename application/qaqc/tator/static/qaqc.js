function returnToCheckList() {
    const url = new URL(window.location.href);
    const projectId = url.searchParams.get('project');
    const sectionId = url.searchParams.get('section');
    const deployments = url.searchParams.getAll('deployment');
    const deploymentList = deployments.map(dep => `&deployment=${dep}`).join('');
    window.location.href = `/qaqc/tator/checklist?project=${projectId}&section=${sectionId}${deploymentList}`;
}

function viewAttractedList() {
    window.open('/qaqc/tator/attracted-list','name','height=900,width=550');
}

function viewImageReferences() {
    window.open('/image-reference','name','height=900,width=550');
}

window.returnToCheckList = returnToCheckList;
window.viewAttractedList = viewAttractedList;
window.viewImageReferences = viewImageReferences;

$(document).ready(()=> {
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
