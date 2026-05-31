from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    mo_attachment_reason = fields.Text(string='MO Attachment Reason')

    def get_moa_raw_material_moves(self):
        self.ensure_one()
        return self.move_raw_ids.filtered(lambda move: move.state != 'cancel')

    def get_moa_byproduct_moves(self):
        self.ensure_one()
        return self.move_byproduct_ids.filtered(lambda move: move.state != 'cancel')

    def get_moa_machine_name(self):
        self.ensure_one()
        if self.workorder_ids:
            workcenters = self.workorder_ids.mapped('workcenter_id.name')
            return ', '.join(filter(None, workcenters))
        return ''

    def get_moa_company_phone(self):
        self.ensure_one()
        company = self.company_id
        return company.phone or company.partner_id.phone or company.partner_id.mobile or ''

    def get_moa_company_address(self):
        self.ensure_one()
        return self.company_id.partner_id.contact_address or ''

    def get_moa_consumed_qty(self, move):
        self.ensure_one()
        if self.state in ('progress', 'to_close', 'done'):
            return move.quantity or 0.0
        return 0.0

    def get_moa_byproduct_qty(self, move):
        self.ensure_one()
        if self.state == 'done':
            return move.quantity or 0.0
        return move.product_uom_qty or 0.0

    def get_moa_prepared_by(self):
        self.ensure_one()
        return self.create_uid

    def get_moa_approved_by(self):
        self.ensure_one()
        return self.user_id or False
