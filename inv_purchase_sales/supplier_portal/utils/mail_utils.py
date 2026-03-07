from odoo.api import Environment
from .common import get_descendant_category_ids

def get_smtp_server_email(env: Environment):
    mail_server = env['ir.mail_server'].sudo().search([], order='sequence', limit=1)
    return mail_server.from_filter

def get_approver_emails(env: Environment) -> str:
    group = env.ref('VendorBid.group_supplies_approver')
    approvers = env['res.users'].sudo().search([('groups_id', 'in', group.id)])
    email_list = approvers.mapped('login')
    return ','.join(email_list)

def get_reviewers(env: Environment) -> str:
    group = env.ref('VendorBid.group_supplies_reviewer')
    reviewers = env['res.users'].sudo().search([('groups_id', 'in', group.id)])
    return reviewers

def get_supplier_emails(env: Environment, rfp_product_category_id) -> list:
    def partner_is_in_category(partner):
        category_tree = get_descendant_category_ids(partner.product_category_id) if partner.product_category_id else []
        return rfp_product_category_id.id in category_tree
    
    suppliers = env['res.users'].search([]).filtered(
        lambda u: u.partner_id and u.partner_id.supplier_rank >= 1 and partner_is_in_category(u.partner_id)
    )
    email_list = suppliers.mapped('login')
    return email_list

def get_reviewer_emails(env: Environment) -> str:
    group = env.ref('VendorBid.group_supplies_reviewer')
    reviewers = env['res.users'].sudo().search([('groups_id', 'in', group.id)])
    email_list = reviewers.mapped('login')
    return ','.join(email_list)
