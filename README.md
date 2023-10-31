# DARC Annotation Review
Streamlined QA/QC and image review for VARS annotations.

***

### Installation

_Requirements: Python ≥ 3.9_

1. Clone this repository.
2. Activate your Python virtual environment (optional).
3. `cd` into the root of the repository and run the command `pip3 install -r requirements.txt`.

### Usage

1. From the root directory of the repository, run the command `./start.sh`. The application will automatically open in your web browser.
   1. Alternatively, you can set up an alias in your command line for an easier startup. Suggested alias (for MacOS):
      ```alias ir="echo 'Checking for updates...' && [COMMAND TO START PYTHON VIRTUAL ENV] && git -C [PATH TO LOCAL REPOSITORY] pull && gunicorn --chdir [PATH TO LOCAL REPOSITORY] run:app --threads 3"```
2. Enter a sequence number in the text field.
   1. To select multiple dives, select the `+` icon to the right of the sequence number text field.
   2. To view annotations added for external review, select `External Image Review` in the top right corner.
3. After entering the appropriate dives, select either `QA/QC` or `Image Review`.
   1. `QA/QC`: A checklist of QA/QC items will be displayed. Each item has a link to the specific check and a checkbox to keep track of progress. Checkbox progress is saved locally and persists after the application is shut down.
   2. `Image Review`: Every annotation record in the selected dive(s) that has an image reference will be displayed. Filtering and sorting these records is possible through the options at the top left and right of the screen.

Both the `QA/QC` and `Image Review` sections have the ability to edit annotations: edits can be done directly in the browser without having to go through VARS.

_Note: Environment variables must be configured in order to save annotation edits to the server. See the section at the bottom of this doc for information about setting environment variables_.

### External Review

1. Add records for external review via the `Add to external review` popup menu on the `Image Review` page. The dropdown menu lists external reviewers that match the current record's phylum.
   1. If the reviewer you want to add is not on the list, select `See all reviewers`. A new tab will open that allows you to view and edit external reviewer information. Changes here are saved to the external reviewer database.
2. After choosing a reviewer and clicking `Save`, the record will be saved to the external reviewer database and the comment in VARS will automatically be updated to `Added for review: [Reviewer name]`.
3. After adding a record to the external review database, more options will appear in the record's information section.
   1. `Change reviewer` allows you to assign a different reviewer to the record.
   2. `Delete from external review` will remove the record from the external review database (the record will remain in the VARS database). The `Added for review` comment will be automatically deleted.
   3. `Reviewer comments` will display comments that the external reviewer has saved along with a timestamp of when the comment was written.
4. Once a record has been added for external review, the reviewer can see all the images added for them by accessing their review page at http://hurlstor.soest.hawaii.edu:5000/review/REVIEWER-NAME (spaces or dashes between first & last names are both okay).
   1. Example: To share images for review with Jeff Drazen, share the link http://hurlstor.soest.hawaii.edu:5000/review/Jeff-Drazen

### Screenshots

![Images Page](https://i.imgur.com/VUHPDIs.png)
![QA/QC Edit Annotation](https://i.imgur.com/N01V8dK.png)
![QA/QC Checklist](https://i.imgur.com/TYYFT5P.png)
![QA/QC Page](https://i.imgur.com/yMNIzyY.png)
![QA/QC Edit Annotation](https://i.imgur.com/GqxueOH.png)


### Setting Environment Variables

The environment variables must be set before any changes can be made to the server. These can be set by creating a file named `.env` in the root of the repository with the following content:

```python
ANNOSAURUS_URL = '...'
ANNOSAURUS_CLIENT_SECRET = '...'
_FLASK_ENV = '...'
```
