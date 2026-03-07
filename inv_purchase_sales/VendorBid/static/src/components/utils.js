/** @odoo-module */

export function formatAmount(number) {
    const abbreviations = ['', 'K', 'M', 'B'];
    
    let index = Math.floor(Math.log10(Math.abs(number)) / 3);
    index = Math.min(abbreviations.length - 1, index);
    let formattedNumber = (number / Math.pow(10, index * 3)).toFixed(2);
    return formattedNumber + abbreviations[index];
}

export function getDateInterval(interval) {
    const now = new Date();
    let start, end;

    switch (interval.toLowerCase()) {
        case 'last_week':
            start = new Date(now);
            start.setDate(now.getDate() - now.getDay() - 7);
            start.setHours(0, 0, 0, 0);

            end = new Date(start);
            end.setDate(start.getDate() + 6);
            end.setHours(23, 59, 59, 999);
            break;

        case 'this_week':
            start = new Date(now);
            start.setDate(now.getDate() - now.getDay());
            start.setHours(0, 0, 0, 0);

            end = new Date(now);
            end.setHours(23, 59, 59, 999);
            break;

        case 'last_month':
            start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            end = new Date(now.getFullYear(), now.getMonth(), 0);
            end.setHours(23, 59, 59, 999);
            break;

        case 'last_year':
            start = new Date(now.getFullYear() - 1, 0, 1);
            end = new Date(now.getFullYear() - 1, 11, 31);
            end.setHours(23, 59, 59, 999);
            break;

        default:
            throw new Error('Invalid interval specified');
    }

    function formatDateLocal(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    return {
        start: formatDateLocal(start),
        end: formatDateLocal(end)
    };
}

export function groupProducts(products) {
    const grouped = products.reduce((acc, product) => {
        const key = product.product_id[0];
        
        if (!acc[key]) {
            acc[key] = {
                product_name: product.product_name,
                product_image: product.product_image,
                product_id: product.product_id,
                total_qty: 0,
                sum_unit_price: 0,
                subtotal_purchase: 0,
                count: 0
            };
        }
        
        acc[key].total_qty += product.product_qty;
        acc[key].sum_unit_price += product.price_unit;
        acc[key].subtotal_purchase += product.price_subtotal;
        acc[key].count += 1;
        
        return acc;
    }, {});
    
    return Object.values(grouped).map((group, index) => ({
        id: index + 1,
        product_name: group.product_name,
        product_image: group.product_image,
        total_qty: group.total_qty,
        avg_qty_price: group.sum_unit_price / group.count,
        subtotal_purchase: group.subtotal_purchase
    }));
}

export function getCurrency(products) {
    return products?.[0]?.currency_id?.[1] || '';
}



export function getImageDataURI(base64) {
    const get_img_type = () => {
        if (base64.startsWith('iVBORw0KGgo')) return 'image/png';
        if (base64.startsWith('/9j/')) return 'image/jpeg';
        if (base64.startsWith('R0lGODlh')) return 'image/gif';
        return 'image/jpeg';
    }
    return `data:${get_img_type()};base64,${base64}`;
}