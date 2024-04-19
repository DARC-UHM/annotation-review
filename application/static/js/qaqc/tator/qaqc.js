function returnToCheckList() {
    const url = window.location.href;
    const projectId = url.split('/')[url.split('/').length - 3];
    const sectionId = url.split('/')[url.split('/').length - 2];
    window.location.href = `/tator/qaqc-checklist/${projectId}/${sectionId}${url.substring(url.indexOf('?'))}`;
}

function viewAttractedList() {
    window.open('/attracted-list','name','height=900,width=600');
}

window.returnToCheckList = returnToCheckList;
window.viewAttractedList = viewAttractedList;

document.addEventListener('DOMContentLoaded',  (event) => {
    if (window.location.href.includes('attracted-not-attracted')) {
        document.getElementById('attractedNotAttractedSubHeading').style.display = 'block';
    }
});
