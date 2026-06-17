# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name = 'overall_customer_report'
        )
        """
    )
    if not cr.fetchone()[0]:
        return
    cr.execute(
        """
        DELETE FROM overall_customer_report a
        USING overall_customer_report b
        WHERE a.sale_order_id = b.sale_order_id
          AND a.id < b.id
        """
    )
    _logger.info('overall_customer_report: removed duplicate rows per sales order')
