{
    "name": "HR Generate Offer Button Controller",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "Controls visibility of 'Generate Offer' button based on recruitment stage setting",
    "description": """
This module adds a checkbox to the recruitment stage form to control whether
the 'Generate Offer' button should be visible on the applicant form.
""",
    "author": "Fikre Tesfay",
    "depends": ["hr_recruitment", "hr_contract_salary"],
    "data": [
        "views/hr_recruitment_stage_views.xml",
        "views/hr_applicant_form_view.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}