
function reviewerList(button, arr, reviewerTextObj) {
    let currentFocus;
    let menuOpen = true;

    function showMenu() {
        /* close any already open lists of autocompleted values */
        closeAllLists();
        currentFocus = -1;
        /* create a DIV element that will contain the items (values) */
        const div = document.createElement('DIV');
        div.setAttribute('id', button[0].id + 'autocomplete-list');
        div.setAttribute('class', 'autocomplete-items reviewer-autocomplete-items');
        /* append the DIV element as a child of the autocomplete container */
        button[0].parentNode.appendChild(div);
        for (let i = 0; i < arr.length; i++) {
            let row = document.createElement('DIV');
            row.innerHTML = `
                <strong>${arr[i].name}</strong><br>                
                <span class="small">${arr[i].focus}</span><br>
                <i class="small text-muted">${arr[i].organization}</i><br>
            `;
            /* insert a input field that will hold the current array item's value */
            row.innerHTML += "<input type='hidden' value='" + arr[i].name + "'>";
            /* execute a function when someone clicks on the item value (DIV element) */
            row.addEventListener("click", function(e) {
                /* insert the value for the autocomplete text field */
                reviewerTextObj.html(row.getElementsByTagName('input')[0].value);
                $('#externalModalSubmitButton').prop('disabled', false);
                button[0].dispatchEvent(new Event('change'));
                /* close the list of autocompleted values,
                (or any other open lists of autocompleted values */
                closeAllLists();
            });
            div.appendChild(row);
        }
        menuOpen = true;
    }
    /* execute a function presses a key on the keyboard */
    button[0].addEventListener('keydown', function(e) {
      let list = document.getElementById(this.id + 'autocomplete-list');
      if (list) {
          list = list.getElementsByTagName("div");
      }
      if (e.keyCode === 40) {
        /* If the arrow DOWN key is pressed, increase the currentFocus variable */
        currentFocus++;
        addActive(list);
      } else if (e.keyCode === 38) { //up
        /* If the arrow UP key is pressed, decrease the currentFocus variable */
        currentFocus--;
        addActive(list);
      } else if (e.keyCode === 13) {
        /* If the ENTER key is pressed, prevent the form from being submitted */
        e.preventDefault();
        if (currentFocus > -1 && list) {
          list[currentFocus].click();
        }
      }
    });
    function addActive(x) {
        /* classifies an item as "active" */
        if (!x) return false;
        removeActive(x);
        if (currentFocus >= x.length) {
            currentFocus = 0;
        }
        if (currentFocus < 0) {
            currentFocus = (x.length - 1);
        }
        x[currentFocus].classList.add('autocomplete-active');
    }
    function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
        for (let i = 0; i < x.length; i++) {
            x[i].classList.remove('autocomplete-active');
        }
    }
    function closeAllLists() {
        /* close all autocomplete lists in the document */
        const list = document.getElementsByClassName('autocomplete-items');
        for (let i = 0; i < list.length; i++) {
            list[i].parentNode.removeChild(list[i]);
        }
        menuOpen = false;
    }
    button[0].addEventListener('click', function (e) {
        e.stopPropagation();  // can't believe this works
        if (menuOpen) {
            closeAllLists();
        } else {
            showMenu();
        }
    });
    document.addEventListener('click', function (e) {
        if (menuOpen) {
            closeAllLists();
        }
    });
}