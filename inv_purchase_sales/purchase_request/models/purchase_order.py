from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rfp_id = fields.Many2one(
        'supplies.rfp', string='RFP', index=True, copy=False)
    purchase_origin = fields.Selection([
        ('local', 'Local'), ('foreign', 'Foreign')],
        string='Purchase Type')
    committee_member_ids = fields.One2many('committee.member', 'rfp_id', string='Committee Members')
    final_po = fields.Boolean(string="Final PO", default=False)

    # Foriegn purchases related fields
    payment_term = fields.Selection(
        [('lc', 'L/C'), ('tt', 'TT'), ('cad', 'CAD')])
    country_origin = fields.Char(string='Country of Origin')
    good_description = fields.Char(string='Description of Goods')
    supplier_pi_number = fields.Char(string='Suppliers PI number')
    port_loading = fields.Char(string='Port Loading')
    port_discharge = fields.Char(string='Port Discharge')
    final_destination = fields.Char(string='Final Destination')
    bank_name = fields.Char(string='Vendor Bank Name')
    bank_address = fields.Char(string='Vendor Bank Address')
    swift_code = fields.Char(string='Vendor Swift Code')
    account_number = fields.Char(string='Vendor Account Number')

    # Local purchases related fields
    warranty_period = fields.Integer(string='Warrenty Period (in months)')
    validity_period = fields.Date(string='Validity Period')

    @api.onchange('purchase_origin')
    def _onchange_purchase_origin(self):
  
        if not self.purchase_origin:
            return
        group_map = {
            'local': 'my_module.group_local_committee_users', 
            'foreign': 'my_module.group_foreign_committee_users',
        }
        xml_id = group_map.get(self.purchase_origin)
        group = self.env.ref(xml_id, raise_if_not_found=False)

        if not group:
            self.committee_member_ids = [Command.clear()]
            return

        employees = self.env['hr.employee'].search([
            ('user_id', 'in', group.users.ids)
        ])
        new_members_list = [Command.clear()]

        for employee in employees:
            new_members_list.append(
                Command.create({
                    'member_id': employee.id,
                    'role': 'member',
                    'approval_status': 'pending',
                })
            )
        self.committee_member_ids = new_members_list
