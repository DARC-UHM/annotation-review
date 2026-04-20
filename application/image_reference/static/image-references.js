import { updateFlashMessages } from '../../static/js/util/updateFlashMessages.js';

window.canEdit = true;

$('#deleteImageReferenceModal').on('show.bs.modal', function (e) {
    const anno = $(e.relatedTarget).data('anno');
    const elementalIdToDelete = $(e.relatedTarget).data('elemental-id');

    if (elementalIdToDelete) {
        $('#deleteImageRefTitle').text('Delete This Photo');
        $('#deleteFromImageReferenceBody').text('Are you sure you want to delete this photo from image references?' +
            ' (This will not delete the other photos that are part of this record.)')
    } else {
        $('#deleteImageRefTitle').text('Delete Image Reference');
        $('#deleteFromImageReferenceBody').text('Are you sure you want to delete this record from image references?')
    }
    $('#imageRefDeleteScientificName').val(anno.scientific_name);
    $('#imageRefDeleteTentativeId').val(anno.tentative_id);
    $('#imageRefDeleteMorphospecies').val(anno.morphospecies);
    $('#imageRefDeleteElementalId').val(elementalIdToDelete);
});

async function refreshImageReference(imageReferenceId) {
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const res = await fetch(`/image-reference/refresh/${imageReferenceId}`);
    if (res.status === 200) {
        const updatedImageReference = await res.json();
        const indexToUpdate = imageReferences.findIndex(imageReference => imageReference.id === updatedImageReference.id);
        imageReferences[indexToUpdate] = updatedImageReference;
        updateFlashMessages('Successfully refreshed image reference', 'success');
        updateImageGrid();
    } else {
        const errorJson = await res.json();
        updateFlashMessages(errorJson.error, 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.refreshImageReference = refreshImageReference;

// Deletes an entire image reference or a specific photo from the image reference db
async function deleteFromImageReferences() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    $('#deleteImageReferenceModal').modal('hide');

    const formData = new FormData($('#deleteFromImageReferenceForm')[0]);
    const res = await fetch('/image-reference', {
        method: 'DELETE',
        body: formData,
    });
    if (res.status === 200) {
        let recordType;
        const indexToDelete = imageReferences.findIndex((imageReference => {
            return imageReference.scientific_name === formData.get('scientific_name')
                && (imageReference.tentative_id ?? '') === formData.get('tentative_id')
                && (imageReference.morphospecies ?? '') === formData.get('morphospecies');
        }));
        if (formData.get('elemental_id')) {
            recordType = 'photo';
            // delete photo from image references list
            imageReferences[indexToDelete].photo_records = imageReferences[indexToDelete].photo_records.filter(photo => {
                return photo.tator_elemental_id !== formData.get('elemental_id');
            });
        } else {
            recordType = 'record';
            imageReferences.splice(indexToDelete, 1);
        }
        updateFlashMessages(`Deleted ${recordType} from image references`, 'success');
        updateImageGrid();
    } else {
        updateFlashMessages('Error removing annotation from external review', 'danger');
    }
    $('#load-overlay').addClass('loader-bg-hidden');
    $('#load-overlay').removeClass('loader-bg');
}

window.deleteFromImageReferences = deleteFromImageReferences;
