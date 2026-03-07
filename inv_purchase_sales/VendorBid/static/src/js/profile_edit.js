function showModal(id) {
    const elem = document.getElementById(id)
    if (elem) {
        const mBootstrap = new bootstrap.Modal(elem);
        mBootstrap.show()
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Save form data to sessionStorage
    function saveFormData() {
        const formData = {};
        document.querySelectorAll('.persist-field').forEach(input => {
            if (input.value) formData[input.name] = input.value;
        });
        document.querySelectorAll('.file-field').forEach(input => {
            if (input.files.length > 0) formData[input.name] = 'uploaded';
        });
        sessionStorage.setItem('formData', JSON.stringify(formData));
    }

    // Load form data from sessionStorage
    function loadFormData() {
        const savedData = JSON.parse(sessionStorage.getItem('formData') || '{}');
        document.querySelectorAll('.persist-field').forEach(input => {
            if (savedData[input.name] && !input.value) {
                input.value = savedData[input.name];
            }
        });
        document.querySelectorAll('.file-field').forEach(input => {
            const label = input.closest('.mb-3')?.querySelector('label');
            if (savedData[input.name] === 'uploaded' && label) {
                label.textContent = label.textContent.replace('Not Uploaded', 'Uploaded');
            }
        });
    }

    // Show the specified page and hide others
    function showPage(page) {
        document.querySelectorAll('.page-section').forEach((section, index) => {
            section.classList.toggle('active', index + 1 === page);
        });
        document.querySelector("#submit_btn").style.display = (page === 4) ? '' : 'none';
        updateButtonVisibility(page);
    }

    // Update visibility of navigation buttons
    function updateButtonVisibility(currentPage) {
        const prevButton = document.querySelector('button[onclick*="navigateRelativePage(-1)"]');
        const nextButton = document.querySelector('button[onclick*="navigateRelativePage(1)"]');
        const submitButton = document.querySelector('button[type="submit"]');
        const discardButton = document.querySelector('#discard_btn');

        if (prevButton) prevButton.style.display = currentPage === 1 ? 'none' : 'inline-block';
        if (nextButton) nextButton.style.display = currentPage === 4 ? 'none' : 'inline-block';
        if (submitButton) submitButton.style.display = currentPage === 4 ? 'inline-block' : 'none';
        if (discardButton) discardButton.style.display = currentPage === 1 ? 'inline-block' : 'none';
    }

    // Navigate to a specific page
    function navigateToPage(page) {
        saveFormData();
        showPage(page);
        // Update URL without reloading
        history.pushState({ page }, '', `/my/account/edit?page=${page}`);
    }

    // Navigate relative to current page
    function navigateRelativePage(delta) {
        const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        const nextPage = currentPage + delta;
        if (nextPage >= 1 && nextPage <= 4) {
            navigateToPage(nextPage);
        }
    }

    // Expose navigateRelativePage to global scope for button onclick
    window.navigateRelativePage = navigateRelativePage;

    // Initialize form
    const form = document.getElementById('partner-profile-form');
    if (form) {
        // Handle form submission
        form.addEventListener('submit', function (event) {
            saveFormData();
            document.querySelectorAll('.persist-field').forEach(input => {
                const hiddenInput = document.querySelector(`input[type="hidden"][name="${input.name}"]`);
                if (hiddenInput) hiddenInput.value = input.value || '';
            });
            sessionStorage.removeItem('formData');
            // Form will submit normally to server
        });

        // Load initial form data
        loadFormData();

        // Show initial page based on URL parameter
        const initialPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        showPage(initialPage);

        // Handle input changes
        document.querySelectorAll('.persist-field, .file-field').forEach(input => {
            input.addEventListener('change', saveFormData);
        });
    }

    // Handle browser back/forward navigation
    window.addEventListener('popstate', function (event) {
        const page = event.state?.page || parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        showPage(page);
    });

    showModal("exampleModal");
});