import { updateFlashMessages } from '../../../static/js/util/updateFlashMessages.js';

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

async function editAttractedConcept() {
    event.preventDefault();
    const formData = new FormData($('#editAttractedConceptForm')[0]);
    const response = await fetch(`/qaqc/tator/attracted/${$('#conceptToEdit').val()}`, {
        method: 'PATCH',
        body: formData,
    });
    if (response.ok) {
        location.reload();
    } else {
        updateFlashMessages('Failed to edit concept', 'danger');
    }
}

async function deleteAttractedConcept() {
    event.preventDefault();
    const response = await fetch(`/qaqc/tator/attracted/${$('#conceptToDelete').val()}`, {
        method: 'DELETE',
    });
    if (response.ok) {
        location.reload();
    } else {
        updateFlashMessages('Failed to delete concept', 'danger');
    }
}

$(document).ready(() => {
    window.editAttractedConcept = editAttractedConcept;
    window.addAttractedConcept = addAttractedConcept;
    window.deleteAttractedConcept = deleteAttractedConcept;

    $('#deleteAttractedConceptModal').on('show.bs.modal', (e) => {
        $('#conceptToDeleteText').text($(e.relatedTarget).data('concept'));
        $('#conceptToDelete').val($(e.relatedTarget).data('concept'));
    });

    $('#editAttractedConceptModal').on('show.bs.modal', (e) => {
        $('#conceptToEditText').text($(e.relatedTarget).data('concept'));
        $('#conceptToEdit').val($(e.relatedTarget).data('concept'));
        $('#editAttracted').val($(e.relatedTarget).data('attracted'));
    });
});
