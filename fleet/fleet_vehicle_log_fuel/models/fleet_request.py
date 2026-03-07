# Copyright 2022 ForgeFlow S.L.  <https://www.forgeflow.com>
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FleetVehicleRequest(models.Model):
    _name = "fleet.vehicle.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fuel log for vehicles"

    active = fields.Boolean(default=True)
    user_id = fields.Many2one(
        "res.users",
        "Requester",
        required=True,
        default=lambda self: self.env.user,

    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        "Vehicle",
        help="Vehicle concerned by this log",
    )
    driver_id = fields.Many2one(
        "res.partner",
        "Driver",
        help="Driver of the vehicle",
    )
    amount = fields.Monetary("Cost")
    description = fields.Char()
    odometer_id = fields.Many2one(
        "fleet.vehicle.odometer",
        "Odometer",
        help="Odometer measure of the vehicle at the moment of this log",
    )
    odometer = fields.Float(
        compute="_compute_odometer",
        store=True,
        inverse="_inverse_odometer",
        string="Odometer Value",
        help="Odometer measure of the vehicle at the moment of this log",
    )
    odometer_unit = fields.Selection(
        related="vehicle_id.odometer_unit", string="Unit")
    date = fields.Date(
        help="Date when the cost has been executed",
        default=fields.Date.context_today,
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id")
    purchaser_id = fields.Many2one(
        "res.partner",
        string="Driver",
        compute="_compute_purchaser_id",
        store=True,
    )
    inv_ref = fields.Char("Vendor Reference")
    vendor_id = fields.Many2one("res.partner", "Vendor")
    notes = fields.Text()
    source_location = fields.Char("Pick up location", required=True)
    destruction_location = fields.Char("Destruction Location", required=True)
    date_from = fields.Datetime(string="From", required=True)
    date_to = fields.Datetime(string="To")
    service_type_id = fields.Many2one(
        "fleet.service.type",
        "Service Type",
        default=lambda self: self.env.ref(
            "fleet.type_service_refueling", raise_if_not_found=False
        ),
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_review", "Submitted"),
            ("verify", "Verified"),
            ("approved", "Approved"),
            ("authorize", "Authorize"),
            ("cancel", "Cancel"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        string="Stage",
    )
    liter = fields.Float()
    price_per_liter = fields.Float()
    service_id = fields.Many2one(
        comodel_name="fleet.vehicle.log.services", readonly=True, copy=False
    )

    def button_draft(self):
        self.write({"state": "draft"})
        # Send message to requester
        for record in self:
            if record.user_id:
                record.message_post(
                    body=_("Fleet request has been set back to draft."),
                    partner_ids=[record.user_id.partner_id.id] if record.user_id.partner_id else [],
                    subject=_("Fleet Request - Set to Draft"),
                )
        return True

    def button_in_review(self):
        self.write({"state": "in_review"})
        # Send message to requester
        for record in self:
            if record.user_id:
                record.message_post(
                    body=_("Your fleet request has been submitted for review."),
                    partner_ids=[record.user_id.partner_id.id] if record.user_id.partner_id else [],
                    subject=_("Fleet Request - In Review"),
                )
        return True

    def button_verify(self):
        self.write({"state": "verify"})
        # Send message to requester
        for record in self:
            if record.user_id:
                record.message_post(
                    body=_("Your fleet request has been verified and is pending approval."),
                    partner_ids=[record.user_id.partner_id.id] if record.user_id.partner_id else [],
                    subject=_("Fleet Request - Verified"),
                )
        return True

    def button_approved(self):
        self.write({"state": "approved"})
        # Send message to requester
        for record in self:
            if record.user_id:
                record.message_post(
                    body=_("Your fleet request has been approved and is pending authorization."),
                    partner_ids=[record.user_id.partner_id.id] if record.user_id.partner_id else [],
                    subject=_("Fleet Request - Approved"),
                )
        return True

    def button_authorize(self):
        # Validate all records before changing state
        for record in self:
            if not record.vehicle_id:
                raise UserError(_("Vehicle is required for authorization. Please select a vehicle before authorizing."))
            if not record.driver_id:
                raise UserError(_("Driver is required for authorization. Please select a driver before authorizing."))
        # If all validations pass, update state for all records
        self.write({"state": "authorize"})
        # Send message to both driver and requester (final stage)
        for record in self:
            partner_ids = []
            if record.user_id and record.user_id.partner_id:
                partner_ids.append(record.user_id.partner_id.id)
            if record.driver_id:
                partner_ids.append(record.driver_id.id)
            
            if partner_ids:
                message_body = _(
                    "Fleet request has been authorized.\n\n"
                    "Vehicle: %s\n"
                    "Driver: %s\n"
                    "Planned Date: %s\n"
                    "Pick up Location: %s\n"
                    "Destination: %s"
                ) % (
                    record.vehicle_id.name if record.vehicle_id else _("N/A"),
                    record.driver_id.name if record.driver_id else _("N/A"),
                    record.date_from.strftime("%Y-%m-%d %H:%M") if record.date_from else _("N/A"),
                    record.source_location or _("N/A"),
                    record.destruction_location or _("N/A"),
                )
                record.message_post(
                    body=message_body,
                    partner_ids=partner_ids,
                    subject=_("Fleet Request - Authorized"),
                )
        return True

    def button_cancel(self):
        self.write({"state": "cancel"})
        # Send message to requester
        for record in self:
            if record.user_id:
                record.message_post(
                    body=_("Your fleet request has been cancelled."),
                    partner_ids=[record.user_id.partner_id.id] if record.user_id.partner_id else [],
                    subject=_("Fleet Request - Cancelled"),
                )
        return True

    def button_rejected(self):
        self.write({"state": "rejected"})
        # Send message to requester
        for record in self:
            if record.user_id:
                record.message_post(
                    body=_("Your fleet request has been rejected."),
                    partner_ids=[record.user_id.partner_id.id] if record.user_id.partner_id else [],
                    subject=_("Fleet Request - Rejected"),
                )
        return True

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        if self.vehicle_id and self.vehicle_id.driver_id:
            self.driver_id = self.vehicle_id.driver_id
