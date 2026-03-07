from odoo.api import Environment
from .schemas import ContactOutSchema, ClientContactOutSchema


def get_or_create_bank(env: Environment, bank_data: dict):
    bank_name = bank_data.get('bank_name')
    bank = env['res.bank'].search([('name', '=', bank_name)], limit=1)
    if not bank:
        bank = env['res.bank'].create(bank_data)
    return bank

def get_child_contacts(self):
    child_ids = []
    contact_function_mapping = {
        'primary_contact_id': 'Primary Contact',
        'finance_contact_id': 'Finance Contact',
        'authorized_contact_id': 'Authorized Contact'
    }
    for field_name, field_label in contact_function_mapping.items():
        contact = getattr(self, field_name)
        if contact:
            contact_data = ContactOutSchema.model_validate(contact).model_dump(
                function=field_label
            )
            email = contact_data.get('email')
            existing_contact = self.env['res.partner'].search(
                [('email', '=', email)]
            )
            if existing_contact:
                child_ids.extend(
                    [(4, c.id) for c in existing_contact]
                )
                child_ids.extend(
                    [(1, c.id, contact_data) for c in existing_contact]
                )
            else:
                child_ids.append((0, 0, contact_data))
    # client references
    for client_ref in self.client_ref_ids:
        client_ref_schema = ClientContactOutSchema.model_validate(client_ref)
        existing_client_ref = self.env['res.partner'].search(
            [('email', '=', client_ref_schema.email)]
        )
        client_ref_data = client_ref_schema.model_dump()
        if existing_client_ref:
            child_ids.extend(
                [(4, c.id) for c in existing_client_ref]
            )
            child_ids.extend(
                [(1, c.id, client_ref_data) for c in existing_client_ref]
            )
        else:
            child_ids.append((0, 0, client_ref_data))
    return child_ids

