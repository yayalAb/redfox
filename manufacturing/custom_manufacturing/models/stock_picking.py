from odoo import models, _, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            if picking.location_id.usage == 'production':
                production = self.env['mrp.production'].search([
                    ('name', '=', picking.origin)
                ], limit=1)

                if production:
                    if not production.elpa_approved:
                        raise UserError(_(
                            "Validation Failed!\n\n"
                            "The Manufacturing Order '%s' has not received ELPA Approval.\n"
                        ) % production.name)

        return super(StockPicking, self).button_validate()