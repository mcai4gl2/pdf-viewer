document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const messageDiv = document.getElementById('message');

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(uploadForm);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                messageDiv.textContent = 'File uploaded successfully!';
                messageDiv.className = 'success';
                uploadForm.reset();
            } else {
                messageDiv.textContent = `Error: ${result.error}`;
                messageDiv.className = 'error';
            }
        } catch (error) {
            messageDiv.textContent = 'An unexpected error occurred.';
            messageDiv.className = 'error';
        }
    });
});
