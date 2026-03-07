{
    "name": "Vendor Bid Per Product",
    "version": "1.0",
    "category": "Purchases",
    "summary": "Vendor Bid Per Product",
    "description": "Module to manage vendor bids on a per-product basis.",
    "author": "Niyat ERP",
    "depends": ["base", "VendorBid", "purchase", "vendor_bid_custom"],
    "data": [
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "application": False
}