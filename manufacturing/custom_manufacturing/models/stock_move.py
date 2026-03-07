from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _create_quality_checks_for_mo(self):
        finished_product_moves = self.filtered(
            lambda m: m.production_id and m.product_id == m.production_id.product_id
        )
        super(StockMove, self)._create_quality_checks_for_mo()

        for production in finished_product_moves.mapped('production_id'):
            move = finished_product_moves.filtered(lambda m: m.production_id == production)
            if len(move) > 1:
                move = move[0]

            if production.is_main:
                self.env['quality.check'].search([
                    ('production_id', '=', production.id)
                ]).unlink()

                quality_points = self.env['quality.point'].search(
                    self.env['quality.point']._get_domain(
                        move.product_id, move.picking_type_id or self.picking_type_id
                    )
                )

                for point in quality_points.filtered(lambda p: p.test_type == 'test_plan'):
                    check_values = point._get_checks_values_from_plan(
                        move.product_id, move.company_id)
                    for values in check_values:
                        values['production_id'] = production.id
                        self.env['quality.check'].create(values)

            # elif production.is_nested:
            #     existing_checks = self.env['quality.check'].search([
            #         ('production_id', '=', production.id)
            #     ])

            #     checks_to_remove = existing_checks.filtered(
            #         lambda c: production.workorder_type_id not in c.point_id.workorder_type_ids
            #     )
                
            #     if checks_to_remove:
            #         checks_to_remove.unlink()