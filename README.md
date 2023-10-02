# DARC Internal Image Review
Method for easily viewing and editing image annotations on HURLSTOR. 

***

### Installation

_Requirements: Python ≥ 3.9_

1. Clone this repository.
2. `cd` into the root of the repository and run the command `pip3 install -r requirements.txt`.

### Usage

1. From the root directory of the repository, run the command `./start.sh` and the application will open in your web browser.
2. Enter a sequence number in the text field.
   1. To view images from multiple dives, select the `+` icon to the right of the sequence number text field.
   2. To filter by phylogeny or by comment, select `Filter By` and enter a filter.
   3. To view all annotations added for external review, select `External Review` in the top right corner.
3. After entering the appropriate dives/filters, select `Go`. A page will load displaying all image records that match the search criteria.
4. Select an annotation's `Edit annotation` button to edit the annotation. A popup window will appear where you can enter updated information. Edits here are saved to the VARS database when you click `Save Changes`.
5. Select `See video` to see the video where the image was captured. 
6. Select `Add for external review` to add an annotation to the external review database. A popup window will appear.
   1. More information on the external review process can be found below.

_Note: Environment variables must be configured in order to save annotation edits to the server. See section at the bottom of this doc for information on setting environment variables_.

### External Review

1. Add records for external review via the `Add to external review` popup menu. The dropdown menu lists external reviewers that match the current record's phylum.
   1. If the reviewer you want to add is not on the list, select `See all reviewers`. A new tab will open that allows you to view and edit external reviewer information. Changes here are saved to the external reviewer database.
2. After choosing a reviewer and clicking `Save`, the record will be saved to the external reviewer database and the comment in VARS will automatically be updated to `Added for review: [Reviewer name]`.
3. After adding a record to the external review database, more options will appear in the record's information section.
   1. The `Change reviewer` button allows you to assign a different reviewer to the record.
   2. The `Delete from external review` button will remove the record from the external review database (the record will remain in the VARS database). The `Added for review` comment will be automatically deleted.
   3. The `Reviewer comments` section will display comments that the external reviewer has saved along with a timestamp of when the comment was written.
4. Once all records have been added for an external reviewer, they can access their review page at http://hurlstor.soest.hawaii.edu:5000/review/REVIEWER-NAME (spaces or dashes between first/last names are both okay).
   1. Example: To share images for review with Jeff Drazen, share the link http://hurlstor.soest.hawaii.edu:5000/review/Jeff-Drazen

### Screenshots

![Images Page](https://i.imgur.com/m8YwDlK.png)
![Edit Annotation](https://i.imgur.com/xSCyjh6.png)


### Setting Environment Variables

The environment variables must be set before any changes can be made to the server. These can be set by editing the `.env` file in the root of the repository:

1. Open `.env` in a text editor of your choice.
2. Update the entries for `ANNOSAURUS_URL` and `ANNOSAURUS_CLIENT_SECRET`. The correct values can be found in `m3-quickstart/bin/docker-env.sh`. Make sure to trace back and find the correct variables for the `ANNOSAURUS_URL`: the entry should read `http://server:port/route`, not `http://${SERVER}:${PORT}${ROUTE}`.
3. Run the command `git update-index --skip-worktree .env` from the command line. This will ensure that there are no conflicts when updating the repository.
