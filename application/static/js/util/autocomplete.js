export function autocomplete(inputObj, itemsArray) {
    // inputObj = jquery object, text input
    // itemsArray = list of possible strings
    let currentFocus;
    if (inputObj.val()) {
        showList();
    }
    /* execute a function when someone writes in the text field */
    inputObj.on('input', function (e) {
        /* close any already open lists of autocompleted values */
        closeAllLists();
        if (!inputObj.val()) {
            return false;
        }
        currentFocus = -1;
        showList();
    });
    inputObj.on('keydown', function (e) {
        let x = document.getElementById(this.id + 'autocomplete-list');
        if (x) x = x.getElementsByTagName('div');
        if (e.keyCode === 40) {
            /* If the arrow DOWN key is pressed, increase the currentFocus variable */
            currentFocus++;
            /* and make the current item more visible */
            addActive(x);
        } else if (e.keyCode === 38) { //up
            /* If the arrow UP key is pressed, decrease the currentFocus variable */
            currentFocus--;
            /* and make the current item more visible */
            addActive(x);
        } else if (e.keyCode === 13) {
            /* If the ENTER key is pressed, prevent the form from being submitted */
            e.preventDefault();
            if (currentFocus > -1) {
                /* and simulate a click on the 'active' item */
                if (x) x[currentFocus].click();
            }
        }
    });

    function addActive(x) {
        /* classify an item as 'active' */
        if (!x) return false;
        /* start by removing the 'active' class on all items */
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class 'autocomplete-active':*/
        x[currentFocus].classList.add('autocomplete-active');
    }

    function removeActive(x) {
        /* remove the 'active' class from all autocomplete items */
        for (let i = 0; i < x.length; i++) {
            x[i].classList.remove('autocomplete-active');
        }
    }

    function closeAllLists(elmnt) {
        /* close all autocomplete lists in the document, except the one passed as an argument */
        const x = document.getElementsByClassName('autocomplete-items');
        for (let i = 0; i < x.length; i++) {
            if (elmnt !== x[i] && elmnt !== inputObj[0]) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }

    function showList() {
        /* create a DIV element that will contain the items (values) */
        const div = document.createElement('DIV');
        const val = inputObj.val();
        div.setAttribute('id', `${Math.random()}autocomplete-list`);
        div.setAttribute('class', 'autocomplete-items');
        /* append the DIV element as a child of the autocomplete container */
        inputObj[0].parentNode.appendChild(div);
        for (const name of itemsArray) {
            if (!name) continue;
            /* check if the item starts with the same letters as the text field value */
            if (name.toUpperCase().includes(val?.toUpperCase())) {
                /* create a DIV element for each matching element */
                const index = name.toUpperCase().indexOf(val?.toUpperCase());
                let row = document.createElement('DIV');
                /* make the matching letters bold */
                row.innerHTML = name.substring(0, index);
                row.innerHTML += '<strong>' + name.substring(index, index + val?.length) + '</strong>';
                row.innerHTML += name.substring(index + val?.length);
                /* insert a input field that will hold the current array item's value */
                row.innerHTML += '<input type="hidden" value="' + name + '">';
                row.addEventListener('click', function (e) {
                    /* insert the value for the autocomplete text field: */
                    inputObj[0].value = this.getElementsByTagName('input')[0].value;
                    inputObj[0].dispatchEvent(new Event('change'));
                    /* close the list of autocompleted values, (or any other open lists of autocompleted values: */
                    closeAllLists();
                });
                div.appendChild(row);
            }
        }
    }

    /* when someone clicks in the document */
    document.addEventListener('click', function (e) {
        closeAllLists(e.target);
    });
}

export function removeAutocomplete(inp) {
    inp.off('input');
    inp.off('keydown');
}

export function removeAllLists() {
    const autocompleteLists = document.getElementsByClassName('autocomplete-items');
    for (let i = 0; i < autocompleteLists.length; i++) {
        autocompleteLists[i].parentNode.removeChild(autocompleteLists[i]);
    }
}
