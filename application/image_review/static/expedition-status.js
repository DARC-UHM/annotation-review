import { updateCheckbox } from '../../qaqc/static/qaqcCheckboxes.js';
import { updateFlashMessages } from '../../static/js/util/updateFlashMessages.js';

document.addEventListener('DOMContentLoaded', () => {
    $('.expedition-status-key').each(function () {
        const $box = $(this);
        $box.html(updateCheckbox(Number($box.attr('data-status')) || 0));
    });

    $('.expedition-status-checkbox').each(function () {
        const $box = $(this);
        let status = Number($box.attr('data-status')) || 0;
        let saving = false;
        $box.html(updateCheckbox(status));

        $box.on('click', async () => {
            // ignore clicks until the last save finishes, so requests can't arrive out of order
            if (saving) return;
            saving = true;
            const nextStatus = status < 2 ? status + 1 : 0;
            $box.html(updateCheckbox(nextStatus)).css('opacity', 0.5).attr('aria-busy', 'true');

            try {
                const res = await fetch('/image-review/expedition-status', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        expedition_name: $box.attr('data-expedition'),
                        status: nextStatus,
                    }),
                });
                if (!res.ok) throw new Error(`Status ${res.status}`);
                status = nextStatus;
                $box.attr('data-status', status);
            } catch (error) {
                console.error('Error updating expedition status', error);
                // put the checkbox back so it shows what is actually saved
                $box.html(updateCheckbox(status));
                updateFlashMessages('Unable to save the expedition status. Please try again.', 'danger');
            } finally {
                saving = false;
                $box.css('opacity', '').removeAttr('aria-busy');
            }
        });
    });
});
