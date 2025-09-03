document.addEventListener('DOMContentLoaded', () => {
    const voteResultsTableBody = document.querySelector('#vote-results-table tbody');

    const fetchAndRenderVoteResults = async () => {
        try {
            const response = await fetch('/vote_results');
            const individualVotes = await response.json();

            voteResultsTableBody.innerHTML = ''; // Clear existing rows

            if (individualVotes.length === 0) {
                const row = document.createElement('tr');
                row.innerHTML = '<td colspan="5">No vote results available.</td>';
                voteResultsTableBody.appendChild(row);
                return;
            }

            // Aggregate votes
            const aggregatedVotes = {};
            individualVotes.forEach(vote => {
                const key = `${vote.doc_id}-${vote.version}`;
                if (!aggregatedVotes[key]) {
                    aggregatedVotes[key] = {
                        doc_id: vote.doc_id,
                        version: vote.version,
                        good_votes: 0,
                        bad_votes: 0,
                        individual_votes: []
                    };
                }
                if (vote.vote_type === 'good') {
                    aggregatedVotes[key].good_votes++;
                } else if (vote.vote_type === 'bad') {
                    aggregatedVotes[key].bad_votes++;
                }
                aggregatedVotes[key].individual_votes.push(vote);
            });

            // Render main table rows
            Object.values(aggregatedVotes).forEach(aggVote => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${aggVote.doc_id}</td>
                    <td>${aggVote.version}</td>
                    <td>${aggVote.good_votes}</td>
                    <td>${aggVote.bad_votes}</td>
                    <td><button class="toggle-details" data-doc-id="${aggVote.doc_id}" data-version="${aggVote.version}">Show Details</button></td>
                `;
                voteResultsTableBody.appendChild(row);

                // Create a hidden row for details sub-table
                const detailsRow = document.createElement('tr');
                detailsRow.classList.add('details-row');
                detailsRow.style.display = 'none'; // Initially hidden
                const detailsCell = document.createElement('td');
                detailsCell.colSpan = 5; // Span all columns

                const subTable = document.createElement('table');
                subTable.classList.add('sub-table');
                subTable.innerHTML = `
                    <thead>
                        <tr>
                            <th>Vote Type</th>
                            <th>Voter Info</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${aggVote.individual_votes.map(detail => `
                            <tr>
                                <td>${detail.vote_type}</td>
                                <td>${detail.voter_info}</td>
                                <td>${detail.created_at}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                `;
                detailsCell.appendChild(subTable);
                detailsRow.appendChild(detailsCell);
                voteResultsTableBody.appendChild(detailsRow);
            });

            // Add event listener for toggle buttons
            voteResultsTableBody.addEventListener('click', (event) => {
                if (event.target.classList.contains('toggle-details')) {
                    const button = event.target;
                    const detailsRow = button.closest('tr').nextElementSibling; // Get the next sibling (details row)
                    if (detailsRow && detailsRow.classList.contains('details-row')) {
                        detailsRow.style.display = detailsRow.style.display === 'none' ? 'table-row' : 'none';
                        button.textContent = detailsRow.style.display === 'none' ? 'Show Details' : 'Hide Details';
                    }
                }
            });

        } catch (error) {
            console.error('Error fetching vote results:', error);
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" style="color: red;">Error loading vote results.</td>';
            voteResultsTableBody.appendChild(row);
        }
    };

    fetchAndRenderVoteResults();
});