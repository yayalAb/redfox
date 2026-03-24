# Withholding Tax Threshold

Apply withholding tax only when the document total (before tax) exceeds a configurable threshold.

## Features

- **Threshold-based**: Withholding tax is applied **only** when `amount_untaxed` (subtotal before tax) **> 20,000**
- **No withholding below threshold**: When total ≤ 20,000, withholding taxes are automatically removed from all lines
- **Document-level check**: Uses the **total** amount of the document, not per-line amounts
- **Before tax**: The check uses `amount_untaxed` (amount before any taxes)
- **Applies to**: Customer Invoices, Vendor Bills, **Purchase Orders**, and **Purchase Quotations (RFQs)**

## Configuration

1. Go to **Settings → Invoicing → Withholding Tax**
2. Set **Withholding Tax Threshold** (default: 20,000)
3. Set to 0 to always apply withholding (except on empty invoices)

## How It Works

- **Invoices & Bills**: When creating or editing a draft invoice/bill:
  - If total (before tax) ≤ threshold → withholding taxes are removed from all product lines
  - If total (before tax) > threshold → withholding taxes from product defaults are applied

- **Purchase Orders & Quotations (RFQs)**: Same logic when creating or editing a PO/RFQ

- **Withholding identification**: A tax is treated as withholding if:
  - It has a negative amount (e.g. -3%), or
  - Its name contains "withhold", "withholding", or "retention", or
  - Its tax group's `preceding_subtotal` contains "withhold" or "withholding"

## Installation

1. Add the module path to your Odoo addons
2. Update the apps list and install **Withholding Tax Threshold**
