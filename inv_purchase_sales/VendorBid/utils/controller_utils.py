from typing import List, Tuple
from odoo.api import Environment
from urllib.parse import urlencode
from .common import get_descendant_category_ids


def format_response(status: str, message: str, data: dict = None) -> dict:
    """
    Formats the response
    """
    return {
        'status': status,
        'message': message,
        'data': data
    }

def validate_email_address(request, email: str) -> Tuple[bool, str]:
    """
    Validates the given email address
    """
    # First check if its blacklisted
    blacklist = request.env['mail.blacklist'].sudo().search(
        [('email', '=', email), ('active', '=', True)]
    )
    if blacklist:
        return False, 'Email address is blacklisted'
    # check if user is already registered
    user = request.env['res.users'].sudo().search(
        [('login', '=', email)]
    )
    if user:
        return False, 'Email address is already registered'
    # check if already applied
    registration = request.env['supplies.registration'].sudo().search(
        [('email', '=', email)]
    )
    if registration:
        return False, 'You have already applied'
    return True, ''

def create_supplier_registration(env: Environment, data: dict):

    

    # create the contacts first
    contact_names = ['primary_contact_id', 'finance_contact_id', 'authorized_contact_id']
    for name in contact_names:
        contact_data = data.pop(name, {})
        if contact_data:
            existing_contact = env['supplies.contact'].sudo().search(
                [('email', '=', contact_data.get('email'))]
            )
            if existing_contact:
                data[name] = existing_contact.id
            else:
                new_contact = env['supplies.contact'].sudo().create(contact_data)
                data[name] = new_contact.id
    # create the client references
    client_refs = data.pop('client_ref_ids', [])
    client_ref_ids = []
    for client_ref in client_refs:
        existing_client_ref = env['supplies.contact'].sudo().search(
            [('email', '=', client_ref.get('email'))]
        )
        if existing_client_ref:
            client_ref_ids.append((4, existing_client_ref.id))
        else:
            client_ref_ids.append((0, 0, client_ref))
    data['client_ref_ids'] = client_ref_ids
    # create the registration
    return env['supplies.registration'].sudo().create(data)

def render_qweb_template(env: Environment, template_name: str, data: dict = {}):
    """
    Renders a QWeb template
    """
    return env['ir.qweb']._render(template_name, data)

def format_labels(*labels):
    formatted_labels = []
    human_readable_labels = {
        'image_1920': "Logo",
        'street': 'Address Line 1',
        'vat': "Tax Identification Number",
        'primary_contact_id': 'Primary Contact',
        'finance_contact_id': 'Finance Contact',
        'authorized_contact_id': 'Authorized Contact',
        'acc_number': 'Account Number',
        'client_ref_ids': 'Client Reference'
    }

    for label in labels:
        # Replace underscores with spaces and capitalize each word
        if isinstance(label, str):
            formatted_label = human_readable_labels.get(
                label,
                label.replace('_', ' ').title()
            )
        else:
            if isinstance(label, int):
                label = label + 1
            formatted_label = str(label)
        formatted_labels.append(formatted_label)

    return ", ".join(formatted_labels)

def get_nice_error_message(*fields, err_type: str, default: str) -> str:
    message_mappings = {
        "trade_license_number": {
            "string_pattern_mismatch": "Trade License number should be a 8-20 characters long alphanumeric string",
        },
        "vat": {
            "string_pattern_mismatch": "TIN should be 10 digits long"
        }
    }
    for field in fields:
        msg = message_mappings.get(field, {}).get(err_type, default)
        return msg
    return default

def format_errors(errors: List[dict]):
    out = []
    for error_dict in errors:
        # value: {'loc': ('field_name',), 'msg': 'Field required', 'type': 'missing'}
        # we want to change the field_name (loc) and message to a more readable format
        error_copy = error_dict.copy()
        error_copy['loc'] = format_labels(*error_copy['loc'])
        if not error_copy['loc']:
            error_copy['loc'] = "Error"
        error_copy['msg'] = get_nice_error_message(
            *error_dict['loc'], err_type=error_dict['type'], default=error_copy['msg']
        )
        out.append(error_copy)
    return out

def render_registration_error_html(env: Environment, errors: List[dict]):
    """
    Renders the error HTML for the registration form modal
    """
    formatted_erros = format_errors(errors)
    template_name = 'VendorBid.supplier_registration_error'
    html = render_qweb_template(env, template_name, {'errors': formatted_erros})
    return str(html)

def check_unique_tin_trade_lic(env: Environment, formdata):
    """
    Checks if the tin and trade license are unique
    """
    tin = formdata.get('vat')
    trade_lic = formdata.get('trade_license_number')
    if tin and env['res.partner'].sudo().search([('vat', '=', tin)]):
        return False
    if trade_lic and env['res.partner'].sudo().search([('trade_license_number', '=', trade_lic)]):
        return False
    return True

def generate_registration_url(env: Environment, registration_id: int) -> str:
    """
    Generates the registration URL
    """
    model_name = 'supplies.registration'
    
    action = env.ref('supplies_registration_reviewer_action', raise_if_not_found=False)
    action_id = action.id if action else 340
    
    cids = env.company.id
    
    base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
    
    params = {
        'id': registration_id,
        'model': model_name,
        'action': action_id,
        'view_type': 'form',
        'cids': cids,
    }
    fragment = urlencode(params)
    url = f"{base_url}/web#{fragment}"
    return url

def get_res_partner_field_changes(res_partner, form_data: dict) -> dict:
    """
    returns the changed fields from the submitted form for the res partner
    """
    data = {}
    for field, val in form_data.items():
        existing_val = getattr(res_partner, field, None)
        if type(val) == int and type(existing_val) != int:
            existing_val = getattr(existing_val, 'id', None)
        if val and existing_val != val:
            data[field] = val
    return data

def get_rfp_general_search_domain(env: Environment) -> List[Tuple[str, str, str]]:
    """
    Returns the general search domain for RFP based on user
    """
    domain = []
    if hasattr(env.user, 'partner_id') and env.user.partner_id.supplier_rank > 0:
        # Supplier: can see all approved RFPs
        domain.append(('state', '=', 'approved'))
        # 🚫 removed product_category restriction
    elif env.user.has_group('VendorBid.group_supplies_requester'):
        # If the user is a requester, filter by the rfp requested by them
        domain.append(('create_uid', '=', env.user.id))
    return domain


# def get_rfp_general_search_domain(env: Environment) -> List[Tuple[str, str, str]]:
#     """
#     Returns the general search domain for RFP based on user
#     """
#     domain = []
#     if hasattr(env.user, 'partner_id') and env.user.partner_id.supplier_rank > 0:
#         partner_id = env.user.partner_id
#         domain.append(('state', '=', 'approved'))
#         # filter by the product category of the partner
#         if hasattr(partner_id, 'product_category_id'):
#             domain.append(
#                 (
#                     'product_category_id',
#                     'in',
#                     get_descendant_category_ids(partner_id.product_category_id)
#                 )
#             )
#     elif env.user.has_group('VendorBid.group_supplies_requester'):
#         # If the user is a requester, filter by the rfp requested by them
#         domain.append(
#             ('create_uid', '=', env.user.id)
#         )
#     return domain