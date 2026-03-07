from pydantic import (
    BaseModel, Field, field_validator,
    model_validator, EmailStr, conbytes, ConfigDict, Base64Str,
    Base64Bytes, StringConstraints
)
from typing import List, Optional, Annotated
from collections import defaultdict
from datetime import date, datetime
import re
import base64

DOC_MAX_SIZE = 1 * 1024 * 1024 # 1 MB
DOC_MIMETYPES = ['application/pdf', 'image/jpeg', 'image/png']

class PurchaseOrderLineSchema(BaseModel):
    product_id: int
    product_qty: float  # can be float for partial quantities
    product_uom: Optional[int] = None
    price_unit: float = Field(gt=0)
    date_planned: date
    name: str = ''  # description
    hs_code: str = ''
    item_model: str = ''


class PurchaseOrderSchema(BaseModel):
    rfp_id: int
    partner_id: int
    warrenty_period: Optional[int] = 0
    validity_period: Optional[date] = None
    date_planned: Optional[date] = None
    purchase_origin: str
    currency_id: int
    notes: str = ''
    state: str = 'draft'
    user_id: int
    order_line: List[PurchaseOrderLineSchema]

    incoterm_id: Optional[int] = None
    good_description: str = ''
    supplier_pi_number: str = ''
    payment_term: str = ''
    country_origin: str = ''
    port_loading: str = ''
    port_discharge: str = ''
    final_destination: str = ''
    bank_name: str = ''
    bank_address: str = ''
    account_number: str = ''
    swift_code: str = ''

    @model_validator(mode='before')
    @classmethod
    def preprocess_data(cls, values):
        groups_types = {'line'}
        group_collections = defaultdict(dict)

        # Collect all line fields from form keys
        for key, value in values.items():
            match = re.match(r"([a-zA-Z]+)-(\d+)-(.+)", key)
            if match:
                group, index, field = match.groups()
                if group in groups_types:
                    group_collections[f"{group}_{index}"][field] = value

        # Convert strings to proper types
        order_line = []
        date_planned = values.get('date_planned')
        for vals in group_collections.values():
            line = {
                'date_planned': date_planned,
                'product_id': int(vals.get('product_id')),
                'product_qty': float(vals.get('product_qty', 0)),
                'price_unit': float(vals.get('price_unit', 0)),
                'product_uom': int(vals['product_uom']) if vals.get('product_uom') else None,
                'hs_code': vals.get('hs_code', ''),
                'name': vals.get('name', ''),  # optional
            }
            order_line.append(line)

        values['order_line'] = order_line
        return values

    def get_new_purchase_order_data(self):
        data = self.model_dump()
        order_line = data.pop('order_line')
        data['order_line'] = [(0, 0, line) for line in order_line]
        return data
