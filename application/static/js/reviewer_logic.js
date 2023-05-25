function checkEmpty(str1, str2) {
    $('#editReviewerSubmitButton')[0].disabled = !(str1.length > 0 && str2.length > 0);
}

$(document).ready(function () {
    for (const reviewer of reviewers) {
        $('#reviewerTable').find('tbody').append(`
        <tr>
            <td>${reviewer.name}</td>
            <td>${reviewer.phylum}</td>
            <td>${reviewer.focus}</td>
            <td>${reviewer.organization}</td>
            <td>${reviewer.email}</td>
            <td class="text-center">
                <button 
                    type="button" 
                    data-bs-toggle="modal" 
                    data-reviewer='${ JSON.stringify(reviewer) }' 
                    data-bs-target="#editReviewerModal" 
                    class="editButton">
                        Edit
                </button>
            </td>
        </tr>
        `);
    }

    $('#editReviewerModal').on('show.bs.modal', function (e) {
        const reviewer = $(e.relatedTarget).data('reviewer');
        const nameField = $(this).find('#editReviewerName');
        const phylumField = $(this).find('#editPhylum');

        nameField.val(reviewer.name);
        phylumField.val(reviewer.phylum);
        $(this).find('#ogReviewerName').val(reviewer.name);
        $(this).find('#editFocus').val(reviewer.focus);
        $(this).find('#editOrganization').val(reviewer.organization);
        $(this).find('#editEmail').val(reviewer.email);
        $(this).find('#lastContacted').val(reviewer.last_contacted);

        $('#deleteReviewerName').html(reviewer.name);
        $('#deleteReviewerButton').attr('href', `/delete_reviewer/${reviewer.name}`);

        nameField.on('input', () => checkEmpty(phylumField.val(), nameField.val()));
        phylumField.on('input', () => checkEmpty(phylumField.val(), nameField.val()));
        checkEmpty(phylumField.val(), nameField.val());
    });

});
