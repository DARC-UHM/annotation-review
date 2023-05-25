$(document).ready(function () {
    for (const reviewer of reviewers) {
        $('#reviewerTable').find('tbody').append(`
        <tr>
            <td>${reviewer.name}</td>
            <td>${reviewer.phylum}</td>
            <td>${reviewer.focus}</td>
            <td>${reviewer.organization}</td>
            <td>${reviewer.email}</td>
            <td>${reviewer.last_contacted ? reviewer.last_contacted : 'NA'}</td>
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

        $(this).find('#editReviewerName').val(reviewer.name);
        $(this).find('#editPhylum').val(reviewer.phylum);
        $(this).find('#editFocus').val(reviewer.focus);
        $(this).find('#editOrganization').val(reviewer.organization);
        $(this).find('#editEmail').val(reviewer.email);
        $(this).find('#lastContacted').val(reviewer.last_contacted);

    });
});
