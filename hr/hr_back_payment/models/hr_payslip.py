from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    back_payment_id = fields.Many2one(
        'hr.back.payment', 
        string="Back Payment Record", 
        readonly=True, 
        copy=False,
        help="The back payment record that generated the inputs for this payslip."
    )

    def action_payslip_done(self):
        """
        Override of the 'Mark as Paid' button action.
        When a payslip is marked as paid, update the related back payment record.
        """
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            if slip.back_payment_id and slip.back_payment_id.state == 'in_payroll':
                slip.back_payment_id.write({'state': 'done'})
        return res

    def action_payslip_cancel(self):
        """
        Override of the 'Cancel Payslip' action.
        If a payslip is cancelled, reset the back payment record to draft.
        """
        for slip in self:
            if slip.back_payment_id and slip.back_payment_id.state == 'in_payroll':
                slip.back_payment_id.write({'state': 'draft'})
        return super(HrPayslip, self).action_payslip_cancel()

    def unlink(self):
        """
        Override of the delete action.
        If a draft payslip is deleted, reset the back payment record to draft.
        """
        for slip in self:
            if slip.back_payment_id and slip.back_payment_id.state == 'in_payroll':
                slip.back_payment_id.write({'state': 'draft'})
        return super(HrPayslip, self).unlink()