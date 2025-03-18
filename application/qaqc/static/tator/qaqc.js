function returnToCheckList() {
    const url = new URL(window.location.href);
    const projectId = url.searchParams.get('project');
    const sectionId = url.searchParams.get('section');
    const deployments = url.searchParams.getAll('deployment');
    window.location.href = `/qaqc/tator/checklist?project=${projectId}&section=${sectionId}&deployment=${deployments.join('&')}`;
}

function viewAttractedList() {
    window.open('/qaqc/tator/attracted-list','name','height=900,width=550');
}

window.returnToCheckList = returnToCheckList;
window.viewAttractedList = viewAttractedList;

$(document).ready(()=> {
    if (window.location.href.includes('attracted-not-attracted')) {
        $('#attractedNotAttractedSubHeading').css('display', 'inline-block');
        $('#attractedNotAttractedPopupButton').css('display', 'inline-block');
    }
});
