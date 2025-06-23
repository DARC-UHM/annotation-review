export const externalReviewNoteSection = (externalComment, uuid) => {
    return `
        <div class="row mt-2">
            <div class="col-4">
                <br>
                <br>
                Reviewer comments:
                <br>
                ${externalComment.unread
                    ? `
                        <button class="editButton" onclick="markCommentRead('${uuid}')">
                            Mark read
                        </button>
                    ` : ''
                }
            </div>
            <div class="col values">
                <hr>
                ${externalComment.reviewer_comments?.map(item => {
                    return item.comment || item.id_consensus
                        ? `
                            ID consensus:
                            <span class="fw-normal">
                                ${item.id_consensus ? `${formattedConsensus(item.id_consensus)} ${item.id_at_time_of_response}` : 'N/A'}
                            </span>
                            <br>
                            Comment:
                            <span class="fw-normal">
                                ${item.comment.length ? item.comment : 'None'}<br>
                            <span class="small fw-normal">
                                - <a href="https://darc.soest.hawaii.edu/review/${item.reviewer}" class="aquaLink" target="_blank">
                                    ${item.reviewer}
                                </a>
                                ${item.date_modified}
                            </span>
                            <hr>
                    ` : `
                        <span class="fw-normal">
                            Awaiting comment from
                            <a href="https://darc.soest.hawaii.edu/review/${item.reviewer}" class="aquaLink" target="_blank">
                                ${item.reviewer}
                            </a>
                            <div class="small">Added ${item.date_modified.substring(0, 6)}</div>
                        </span>
                        <hr>
                    `;
                }).join('')}
            </div>
        </div>
    `;
};

const formattedConsensus = (consensus) => {
  if (!consensus) return '';
  switch (consensus) {
    case 'agree':
      return 'Agree with';
    case 'disagree':
      return 'Disagree with';
    default:
      return 'Uncertain of';
  }
}
