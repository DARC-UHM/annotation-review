export function updateFlashMessages(msg, cat) {
    $('#flash-messages-container').html(`
        <div class="alert alert-${cat} alert-dismissible px-5" style="position:fixed; left: 50%; transform: translate(-50%, 0);">
            <span class="px-2" style="font-weight: 500;">${msg}</span>
            <button type="button" class="btn-close small" data-bs-dismiss="alert" aria-label="Close"></button>
            <div class="alert-bottom-bar alert-bottom-bar-${cat}"></div>
        </div>
    `);
    $('#flash-messages-container').show();
    setTimeout(() => {
        $('#flash-messages-container').fadeOut(200);
    }, 5000);
}
