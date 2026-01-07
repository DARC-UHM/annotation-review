import { autocomplete, removeAllLists, removeAutocomplete } from './autocomplete.js';

function validateName(name, nameList, button) {
    let disabled = false;
    if (name && !nameList.includes(name)) {
        disabled = true;
    }
    button.disabled = disabled;
}

export async function getWormsAutocomplete(scientificNameInputId, spinnerId, submitButtonId) {
    const scientificNameInputObject = $(`#${scientificNameInputId}`);
    const spinnerObject = $(`#${spinnerId}`);
    const submitButtonObject = $(`#${submitButtonId}`);
    const scientificName = scientificNameInputObject.val();
    if (scientificName.length > 2) {
        removeAutocomplete(scientificNameInputObject);
        removeAllLists();
        spinnerObject.show();
        const res = await fetch(`https://www.marinespecies.org/rest/AphiaRecordsByName/${scientificName}?like=true&marine_only=true`);
        let scientificNameList = [];
        if (res.status === 200) {
            const data = await res.json();
            scientificNameList = data.map((record) => record.scientificname);
        }
        autocomplete(scientificNameInputObject, scientificNameList);
        scientificNameInputObject.on('input', () => getWormsAutocomplete(scientificNameInputId, spinnerId, submitButtonId));

        validateName(scientificNameInputObject.val(), scientificNameList, submitButtonObject[0]);
        scientificNameInputObject.on('input', () => validateName(scientificNameInputObject.val(), scientificNameList, submitButtonObject[0]));
        scientificNameInputObject.on('change', () => validateName(scientificNameInputObject.val(), scientificNameList, submitButtonObject[0]));
        spinnerObject.hide();
    } else {
        submitButtonObject[0].disabled = true;
        removeAllLists(); // only show autocomplete if there are more than 2 characters
    }
}
