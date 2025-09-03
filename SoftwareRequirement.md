# Project Overview

pdf browser is a python web project which:
- Has rest endpoints for admin to upload pdf files, alone with summary and metadata in json. It can have also other docs in html associated with it
- The website shall serve the metdata for all entires in a table
- When a row is clicked, it can show all docs including pdf with some clickable clicks. When clicked, the content shall be served
- There shall be some global search capabilities across metadata and contents in text format. No need to handle search in pdf
- Upload shall have some id to allow updates. All versions shall be stored and viewable. The upload shall have some other names to store details on what the change is

Some techinical requirement:
- The code shall be in python, the evironment management shall be in pip and venv
- The backend shall be in flask
- The front end shall be very simple templates
- The data shall be stored in some database to allow search. Database to use shall be sqlite
- All code shall have as much unit test as possible

## Clarifications

- **PDF Content Search**: No need to search in pdf, only the text content.
- **Associated HTML Docs**: Yes, they are separate files.
- **"Clickable Clicks"**: Hyperlinks so user can click and nagivate to see the content.
- **Versioning UI**: They shall be ideally sub tables and can fold/expand on the main page.
- **Authentication**: No need for auth.
- **Frontend Framework**: css is fine but I don't want stuff like react.
- **Table Display**: The main table will dynamically display columns based on metadata JSON keys. If a document lacks a specific key, its cell will be empty.
- **Multiple HTML Documents**: Each version of a document can now be associated with multiple HTML files.
- **Consistency Check**: A new column will indicate if the files (PDF and HTML) stored in the database are consistent with the files present in the `uploads` folder.
- **File Naming**: File names are generated using UUIDs, ensuring uniqueness and preventing clashes between different uploads.

## User Voting Feature

-   **Purpose**: Allow users to vote on the quality of document versions (good/bad).
-   **Vote Storage**:
    -   Votes will be stored in the database.
    -   Each vote will record:
        -   The `doc_id` and `version` of the document being voted on.
        -   The type of vote (e.g., 'good' or 'bad').
        -   The timestamp of the vote.
        -   Information about the voter (e.g., remote IP address or a simple identifier from cookie, prioritizing what's easily available without complex authentication).
-   **Vote Visibility**: Vote results (e.g., counts of good/bad votes) will **not** be displayed on the main document listing page.
-   **Voting Interface**: Users can cast votes directly from the main document listing page using 'Good' and 'Bad' buttons. A separate dedicated page (`/vote_results_page`) is available to view the aggregated voting results, including individual voter details (who and when).