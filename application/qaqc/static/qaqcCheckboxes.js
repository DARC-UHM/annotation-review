import * as Icons from '../../static/js/icons.js';

/** Returns the appropriate checkbox svg based on the number passed in (0 = not done, 1 = in progress, 2 = complete) */
export function updateCheckbox(num) {
    switch (num) {
        case 0: // not done
            return Icons.checkboxBlank;
        case 1: // in progress
            return Icons.checkboxInProgress;
        case 2:
            return Icons.checkboxComplete;
    }
}

/** Counts number of completed tasks and updates the task count display. If all tasks are complete, shows fireworks */
export function updateTaskCount(checklist) {
    const tasksComplete = Object.values(checklist).reduce((accumulator, currentValue) => currentValue === 2 ? accumulator + 1 : accumulator, 0);
    $('#tasksComplete').html(tasksComplete);
    if (tasksComplete === Object.keys(checklist).length) {
        $('#fireworks').show();
        $('#fireworksToggleButton').show();
    } else {
        $('#fireworks').hide();
        $('#fireworksToggleButton').hide();
    }
}

/** Converts checklist item from snake case to camel case and returns checkbox name */
export function getCheckboxName(checklistItem) {
    return checklistItem.split('_')
        .map((word, index) => index > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : word)
        .join('') + 'Checkbox';
}
