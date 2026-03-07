{
    "name": "HR 360 Performance Evaluation",
    "summary": "Extend jobs with peer relationships and evaluator rate tabs",
    "description": "Adds 360-degree evaluation support by letting HR jobs"
    " track related peer positions and evaluator rate references.",
    "category": "Human Resources",
    "version": "1.0",
    "author": "Niyat ERP",
    "depends": ["hr", "update_menus"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_performance_confi.xml",
        "views/job_views.xml",
        "views/hr_performance_evaluation_views.xml",
        "views/hr_employee_performance_views.xml",
        "views/hr_evaluation_direct_views.xml",
        "views/hr_performance_evaluation_summary_detail_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_performance_360/static/src/js/evaluation_wizard_widget.js",
            "hr_performance_360/static/src/xml/evaluation_wizard_widget.xml",
            "hr_performance_360/static/src/css/evaluation_wizard.css",
        ],
    },
    "installable": True,
    "auto_install": False,
}


