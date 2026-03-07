from odoo import models, fields, _
from datetime import date

class FleetVehicleLogContract(models.Model):
    _inherit = "fleet.vehicle.log.contract"

    def _cron_contract_reminders(self):
        """Send reminders at 30, 7, and 1 day before expiration"""
        today = date.today()
        reminders = [30, 7, 1]
        activity_type = self.env.ref("fleet.mail_act_fleet_contract_to_renew", raise_if_not_found=False)

        if not activity_type:
            return  # make sure the activity type exists

        contracts = self.search([
            ("state", "=", "open"),
            ("expiration_date", "!=", False),
        ])

        for contract in contracts:
            days_left = (contract.expiration_date - today).days
            if days_left in reminders:
                # build a list of users to notify
                users_to_notify = []

                # Manager (responsible user)
                if contract.user_id:
                    users_to_notify.append(contract.user_id)

                # Driver (linked partner -> check if he has a user)
                if contract.vehicle_id.driver_id and contract.vehicle_id.driver_id.user_ids:
                    users_to_notify.append(contract.vehicle_id.driver_id.user_ids[0])

                for user in users_to_notify:
                    already_exists = self.env["mail.activity"].search_count([
                        ("res_id", "=", contract.id),
                        ("res_model", "=", "fleet.vehicle.log.contract"),
                        ("activity_type_id", "=", activity_type.id),
                        ("user_id", "=", user.id),
                        ("summary", "=", f"Contract expires in {days_left} days"),
                    ])
                    if not already_exists:
                        self.env["mail.activity"].create({
                            "res_id": contract.id,
                            "res_model_id": self.env.ref("fleet.model_fleet_vehicle_log_contract").id,
                            "activity_type_id": activity_type.id,
                            "user_id": user.id,
                            "summary": _(f"Contract expires in {days_left} days"),
                            "note": _(f"The contract {contract.name} for vehicle {contract.vehicle_id.name} will expire in {days_left} days (on {contract.expiration_date})."),
                            "date_deadline": today,
                        })
