import { updateFlashMessages } from '../../util/updateFlashMessages.js';

$('#deleteAttractedConceptModal').on('show.bs.modal', (e) => {
    $('#conceptToDeleteText').text($(e.relatedTarget).data('concept'));
    $('#conceptToDelete').val($(e.relatedTarget).data('concept'));
});

async function addAttractedConcept() {
    event.preventDefault();
    const formData = new FormData($('#addAttractedConceptForm')[0]);
    const response = await fetch('/attracted', {
        method: 'POST',
        body: formData,
    });
    if (response.ok) {
        location.reload();
    } else {
        updateFlashMessages('Failed to add concept', 'danger');
    }
}

async function deleteAttractedConcept() {
    event.preventDefault();
    const response = await fetch(`/attracted/${$('#conceptToDelete').val()}`, {
        method: 'DELETE',
    });
    if (response.ok) {
        location.reload();
    } else {
        updateFlashMessages('Failed to delete concept', 'danger');
    }
}

window.addAttractedConcept = addAttractedConcept;
window.deleteAttractedConcept = deleteAttractedConcept;
