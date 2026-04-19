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
    $('#imageRefDeleteTentativeId').val(anno.tentative_id ?? null);
    $('#imageRefDeleteMorphospecies').val(anno.morphospecies ?? null);
    $('#imageRefDeleteElementalId').val(elementalIdToDelete);
    $('#externalDeleteUuid').val(anno.observation_uuid);
});

window.deleteFromImageReferences = deleteFromImageReferences;
