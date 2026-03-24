# -*- coding: utf-8 -*-

def post_init_hook(env):
    """Assign default stage to existing LC letters and migrate payment line states."""
    LcLetter = env['lc.letter']
    Stage = env['lc.letter.stage']
    default_stage = Stage.search([], order='sequence asc', limit=1)
    if default_stage:
        LcLetter.search([('stage_id', '=', False)]).write({'stage_id': default_stage.id})

    # Migrate payment line states: draft->submitted, pending->verified, paid->approved, cancelled->submitted
    PaymentLine = env['lc.letter.payment.line']
    state_map = {
        'draft': 'submitted',
        'pending': 'verified',
        'paid': 'approved',
        'cancelled': 'submitted',
    }
    for old_state, new_state in state_map.items():
        PaymentLine.search([('state', '=', old_state)]).write({'state': new_state})
