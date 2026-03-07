(function() {
    console.log("Portal script loaded");

    function updateCalculations(lineId) {
        // 1. Select elements using the data-line-id to be specific
        const qtyInput = document.querySelector(`input[name='line-${lineId}-product_qty']`);
        const priceInput = document.querySelector(`input[name='line-${lineId}-price_unit']`);
        const taxInput = document.querySelector(`input[name='line-${lineId}-tax']`);
        const subtotalSpan = document.querySelector(`.line_subtotal[data-line-id='${lineId}']`);

        if (qtyInput && priceInput && subtotalSpan) {
            const qty = parseFloat(qtyInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const tax = taxInput ? (parseFloat(taxInput.value) || 0) : 0;

            const subtotal = (qty * price) * (1 + (tax / 100));
            
            // Format the number to 2 decimal places
            subtotalSpan.textContent = subtotal.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
            
            console.log(`Line ${lineId} updated: ${subtotal}`);
        }
    }

    // Use Event Delegation
    document.addEventListener('input', function (event) {
        // TRIGGER for BOTH price and quantity changes
        if (event.target.classList.contains('input_price_unit') || event.target.classList.contains('line_qty')) {
            const lineId = event.target.dataset.lineId;
            if (lineId) {
                updateCalculations(lineId);
            }
        }
    });
})();