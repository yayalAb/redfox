from . import models


def update_menu_icons(env):
    """Update menu icons only if the module is installed."""
    menu_items = [
        {"xml_id": "account.menu_finance", "module": "account"},
        {"xml_id": "stock.menu_stock_root", "module": "stock"},
        {"xml_id": "mrp.menu_mrp_root", "module": "mrp"},
        {"xml_id": "purchase.menu_purchase_root", "module": "purchase"},
        {"xml_id": "sale.sale_menu_root", "module": "sale"},
        {"xml_id": "contacts.menu_contacts", "module": "contacts"},
        {"xml_id": "project.menu_main_pm", "module": "project"},
        {"xml_id": "crm.crm_menu_root", "module": "crm"},
        {"xml_id": "hr.menu_hr_root", "module": "hr"},
        {"xml_id": "survey.menu_surveys", "module": "survey"},
        {"xml_id": "om_hr_payroll.menu_hr_payroll_root", "module": "om_hr_payroll"},
        {"xml_id": "hr_attendance.menu_hr_attendance_root", "module": "hr_attendance"},
        {"xml_id": "hr_reward_warning.hr_announcement",
            "module": "hr_reward_warning"},
        {"xml_id": "hr_resignation.employee_resignation", "module": "hr_resignation"},
        {"xml_id": "hr_holidays.menu_hr_holidays_root", "module": "hr_holidays"},
        {"xml_id": "spreadsheet_dashboard.spreadsheet_dashboard_menu_root",
            "module": "spreadsheet_dashboard"},
        {"xml_id": "hr_recruitment.menu_hr_recruitment_root",
            "module": "hr_recruitment"},
        {"xml_id": "hr_expense.menu_hr_expense_root", "module": "hr_expense"},
        {"xml_id": "utm.menu_link_tracker_root", "module": "utm"},
        {"xml_id": "mail.menu_root_discuss", "module": "mail"},
        {"xml_id": "calendar.mail_menu_calendar", "module": "calendar"},
        {"xml_id": "provident_fund.provident_fund_root_menu",
            "module": "provident_fund"},
        {"xml_id": "point_of_sale.menu_point_root", "module": "point_of_sale"},
        {"xml_id": "project.menu_main_pm", "module": "project"},
        {"xml_id": "website.menu_website_configuration", "module": "website"},
        {"xml_id": "event.event_main_menu", "module": "event"},
        {"xml_id": "fleet.menu_root", "module": "fleet"},
        {"xml_id": "lunch.menu_lunch", "module": "lunch"},
        {"xml_id": "project_todo.menu_todo_todos", "module": "project_todo"},
        {"xml_id": "maintenance.menu_maintenance_title", "module": "maintenance"},
        {"xml_id": "hotel_management_odoo.hotel_management_menu_root",
            "module": "hotel_management_odoo"},
        {"xml_id": "operation.menu_edomias_main", "module": "operation"},
        {"xml_id": "hr_timesheet.timesheet_menu_root", "module": "hr_timesheet"},
        {"xml_id": "recruitment_requests.menu_recruitment_requests",
            "module": "recruitment_requests"},
        {"xml_id": "performance_evaluation.menu_employee_appraisal",
            "module": "performance_evaluation"},


        {"xml_id": "project_todo.menu_todo_todos",
            "module": "project_todo"},

        {"xml_id": "ohrms_overtime.hr_overtime_menu_root",
            "module": "ohrms_overtime"},
        {"xml_id": " hr_resignation.hr_resignation_menu_root",
         "module": "hr_resignation"},
        {"xml_id": "hr_payroll_community.menu_hr_payroll_community_root",
         "module": "hr_payroll_community"},
        {"xml_id": "accountant.menu_accounting",
         "module": "accountant"},
        {"xml_id": "mass_mailing.mass_mailing_menu_root",
         "module": "mass_mailing"},
        {"xml_id": "utm.menu_link_tracker_root",
            "module": "utm"},
        {"xml_id": "website_slides.website_slides_menu_root",
            "module": "website_slides"},
        {"xml_id": "fleet.menu_root",
            "module": "fleet"},


    ]

    for item in menu_items:
        name = item["module"]
        menu_id = item["xml_id"]
        module_installed = env["ir.module.module"].search([
            ("name", "=", name),
            ("state", "=", "installed")
        ])
        if module_installed:
            menu = env.ref(menu_id, raise_if_not_found=False)
            if menu:
                menu.write(
                    {"web_icon": f"update_icons,static/src/img/icons/{name}.png"})
