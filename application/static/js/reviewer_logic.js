document.addEventListener('DOMContentLoaded', function(event) {
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
                </button><br>
                <button 
                    type="button" 
                    data-bs-toggle="modal" 
                    data-reviewer='${ JSON.stringify(reviewer) }' 
                    data-bs-target="#deleteReviewerModal" 
                    class="editButton">
                        Remove
                </button>
            </td>
        </tr>
        `);
    }
});
