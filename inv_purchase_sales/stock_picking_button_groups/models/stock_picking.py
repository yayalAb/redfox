from odoo import _, models
from odoo.exceptions import AccessError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_picking_button_group(self, group_xmlid):
        if not self.env.user.has_group(group_xmlid):
            raise AccessError(
                _("You do not have the access right to perform this operation.")
            )

    def action_confirm(self):
        self._check_picking_button_group(
            "stock_picking_button_groups.group_stock_picking_mark_todo"
        )
        return super().action_confirm()

    def action_assign(self):
        self._check_picking_button_group(
            "stock_picking_button_groups.group_stock_picking_check_availability"
        )
        return super().action_assign()

    def button_validate(self):
        self._check_picking_button_group(
            "stock_picking_button_groups.group_stock_picking_validate"
        )
        return super().button_validate()

    def action_cancel(self):
        self._check_picking_button_group(
            "stock_picking_button_groups.group_stock_picking_cancel"
        )
        return super().action_cancel()
