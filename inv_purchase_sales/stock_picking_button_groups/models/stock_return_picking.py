from odoo import _, models
from odoo.exceptions import AccessError


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def action_create_returns(self):
        if not self.env.user.has_group(
            "stock_picking_button_groups.group_stock_picking_return"
        ):
            raise AccessError(
                _("You do not have the access right to perform this operation.")
            )
        return super().action_create_returns()
