# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Set report binding dynamically after module installation"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Try to find the training.requisition model
    try:
        training_model = env['ir.model'].search([
            ('model', '=', 'training.requisition')
        ], limit=1)
        
        if training_model:
            # Find the report action
            report_action = env.ref('hr_contract_letters.action_report_training_invitation', raise_if_not_found=False)
            if report_action:
                # Set binding model
                report_action.binding_model_id = training_model.id
    except Exception as e:
        # If model doesn't exist or other error, just continue
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning('Error in post_init_hook for training requisition: %s', str(e))
