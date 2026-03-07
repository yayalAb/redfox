async function getProducts(categoryId) {
    try {
        const response = await fetch('/my/supplies/category-products-html/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                params: {
                    category_id: categoryId
                }
            })
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        if (data && data?.result?.data) {
            const productSelects = document.querySelectorAll('.product-select');
            productSelects.forEach(select => {
                select.innerHTML = data.result.data;
                select.value = ''; // Reset value to trigger change event
                select.dispatchEvent(new Event('change')); // Trigger change event
            });
        } else {
            console.error('Invalid data format received:', data);
        }
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}


document.addEventListener("DOMContentLoaded", function () {
    const categorySelect = document.getElementById('category');
    categorySelect.addEventListener('change', function () {
        const categoryId = this.value;
        if (categoryId) {
            getProducts(categoryId);
        }
    });

    function updateProductDropdowns() {
        const allSelects = document.querySelectorAll('.product-select');
        const selectedValues = Array.from(allSelects).map(s => s.value).filter(v => v);

        allSelects.forEach(select => {
            const currentVal = select.value;
            const allOptions = Array.from(select.querySelectorAll('option'));
            const preservedOption = allOptions.find(opt => opt.value === currentVal);
            select.innerHTML = '<option value="">Select a product</option>';
            allOptions.forEach(opt => {
                if (!opt.value) return;
                if (opt.value === currentVal || !selectedValues.includes(opt.value)) {
                    select.appendChild(opt.cloneNode(true));
                }
            });
            if (currentVal) select.value = currentVal;
        });
    }

    function addProductLineEventListeners(row) {
        const productSelect = row.querySelector('.product-select');
        productSelect.addEventListener('change', function () {
            const selectedOption = this.options[this.selectedIndex];
            const imageData = selectedOption.getAttribute('data-image');
            const description = selectedOption.getAttribute('data-desc') || '';
            const imageContainer = row.querySelector('.product-image-container');
            const descContainer = row.querySelector('.product-description');

            imageContainer.innerHTML = imageData && imageData !== 'False'
                ? `<img src="${imageData}" class="img-thumbnail" alt="Product image" style="max-width: 100px;"/>`
                : '<div class="text-muted">No image</div>';


            descContainer.textContent = description || 'No description';
            updateProductDropdowns();
        });

        row.querySelector('.remove-line').addEventListener('click', function () {
            if (document.querySelectorAll('.product-line').length > 1) {
                row.remove();
                setTimeout(updateProductDropdowns, 0);
            }
        });
    }

    document.getElementById('add_product_line').addEventListener('click', function () {
        const newRow = document.querySelector('.product-line').cloneNode(true);
        const tbody = document.getElementById('product_lines');
        newRow.querySelector('.product-select').value = '';
        newRow.querySelector('.quantity').value = 1;
        newRow.querySelector('.product-image-container').innerHTML = '<div class="text-muted">No image</div>';
        newRow.querySelector('.product-description').innerHTML = '<em class="text-muted">Select a product</em>';

        document.querySelectorAll('.remove-line').forEach(btn => btn.disabled = false);
        tbody.appendChild(newRow);
        addProductLineEventListeners(newRow);
        updateProductDropdowns();
    });

    document.querySelectorAll('.product-line').forEach(row => {
        addProductLineEventListeners(row);
        const select = row.querySelector('.product-select');
        if (select.value) select.dispatchEvent(new Event('change'));
    });

});

window.addEventListener('DOMContentLoaded', function () {
    const url = new URL(window.location.href);
    if (url.searchParams.has('submitted')) {
        url.searchParams.delete('submitted');
        window.history.replaceState({}, document.title, url.pathname);
    }
});
