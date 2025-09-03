document.addEventListener('DOMContentLoaded', () => {
    const searchBar = document.getElementById('search-bar');
    const documentsTable = document.getElementById('documents-table');
    const documentsTableHead = documentsTable.querySelector('thead');
    const documentsTableBody = documentsTable.querySelector('tbody');

    const fetchAndRenderDocuments = async (query = '') => {
        try {
            const url = query ? `/search?q=${query}` : '/documents';
            const response = await fetch(url);
            const documents = await response.json();
            renderDocuments(documents);
        } catch (error) {
            console.error('Error fetching documents:', error);
        }
    };

    const renderDocuments = (documents) => {
        // Clear existing table
        documentsTableHead.innerHTML = '';
        documentsTableBody.innerHTML = '';

        if (documents.length === 0) {
            return;
        }

        // Get all unique metadata keys
        const allKeys = new Set();
        documents.forEach(doc => {
            Object.keys(doc.metadata).forEach(key => allKeys.add(key));
        });
        const headers = ['doc_id', ...Array.from(allKeys), 'latest_version', 'Actions'];

        // Create table header
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        documentsTableHead.appendChild(headerRow);

        // Create table rows
        documents.forEach(doc => {
            const row = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                if (header === 'doc_id') {
                    td.textContent = doc.doc_id;
                } else if (header === 'latest_version') {
                    td.textContent = doc.latest_version;
                } else if (header === 'Actions') {
                    const button = document.createElement('button');
                    button.textContent = 'Show/Hide Versions';
                    button.classList.add('toggle-versions');
                    td.appendChild(button);
                } else {
                    td.textContent = doc.metadata[header] || '';
                }
                row.appendChild(td);
            });
            documentsTableBody.appendChild(row);

            const versionsRow = document.createElement('tr');
            versionsRow.style.display = 'none';
            const versionsCell = document.createElement('td');
            versionsCell.colSpan = headers.length;
            const versionsTable = document.createElement('table');
            versionsTable.innerHTML = `
                <thead>
                    <tr>
                        <th>Version</th>
                        <th>Change Description</th>
                        <th>File</th>
                        <th>HTML Files</th>
                        <th>File Consistency</th>
                        <th>HTML Consistency</th>
                        <th>Created At</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${doc.versions.map(v => `
                        <tr>
                            <td>${v.version}</td>
                            <td>${v.change_description}</td>
                            <td><a href="/uploads/${v.file_path.split('/').pop()}" target="_blank">PDF</a></td>
                            <td>${v.html_paths.map(hp => `<a href="/uploads/${hp.path.split('/').pop()}" target="_blank">HTML</a>`).join(', ')}</td>
                            <td>${v.file_consistent ? '✅' : '❌'}</td>
                            <td>${v.html_paths.map(hp => hp.consistent ? '✅' : '❌').join(', ')}</td>
                            <td>${v.created_at}</td>
                            <td>
                                <button class="delete-version-btn" data-doc-id="${doc.doc_id}" data-version="${v.version}">Delete</button>
                                <button class="vote-btn good" data-doc-id="${doc.doc_id}" data-version="${v.version}">Good</button>
                                <button class="vote-btn bad" data-doc-id="${doc.doc_id}" data-version="${v.version}">Bad</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
            versionsCell.appendChild(versionsTable);
            versionsRow.appendChild(versionsCell);
            documentsTableBody.appendChild(versionsRow);

            row.querySelector('.toggle-versions').addEventListener('click', () => {
                versionsRow.style.display = versionsRow.style.display === 'none' ? 'table-row' : 'none';
            });
        });
    };

    searchBar.addEventListener('input', (event) => {
        fetchAndRenderDocuments(event.target.value);
    });

    fetchAndRenderDocuments();

    // Function to handle version deletion
    const deleteVersion = async (docId, version) => {
        if (confirm(`Are you sure you want to delete version ${version} of document ${docId}?`)) {
            try {
                const response = await fetch(`/documents/${docId}/versions/${version}`, {
                    method: 'DELETE',
                });
                const result = await response.json();
                if (result.success) {
                    alert(result.message);
                    // Re-fetch and render documents to update the UI
                    fetchAndRenderDocuments(searchBar.value);
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                console.error('Error deleting version:', error);
                alert('An error occurred while deleting the version.');
            }
        }
    };

    // Function to handle vote submission
    const sendVote = async (docId, version, voteType) => {
        try {
            const response = await fetch('/vote', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    doc_id: docId,
                    version: parseInt(version),
                    vote_type: voteType,
                }),
            });
            const result = await response.json();

            if (result.success) {
                alert(result.message);
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error('Error sending vote:', error);
            alert('An error occurred while sending your vote.');
        }
    };

    // Event delegation for delete buttons (since they are dynamically created)
    documentsTableBody.addEventListener('click', async (event) => {
        if (event.target.classList.contains('delete-version-btn')) {
            const docId = event.target.dataset.docId;
            const version = event.target.dataset.version;
            await deleteVersion(docId, version);
        } else if (event.target.classList.contains('vote-btn')) {
            const docId = event.target.dataset.docId;
            const version = event.target.dataset.version;
            const voteType = event.target.classList.contains('good') ? 'good' : 'bad';
            await sendVote(docId, version, voteType);
        }
    });
});