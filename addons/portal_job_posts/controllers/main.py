from collections import defaultdict
from odoo import http
from odoo.http import request
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment

class CustomWebsiteHrRecruitment(WebsiteHrRecruitment):

    @http.route('''/jobs/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=True)
    def job(self, job, **kwargs):

        skills_by_type = defaultdict(list)
        if job.skill_ids:
            for skill in job.skill_ids:
                if skill.skill_type_id:
                    skills_by_type[skill.skill_type_id].append(skill)

        values = {
            'job': job,
            'main_object': job,
        }
        values['skills_by_type'] = skills_by_type

        return http.request.render("website_hr_recruitment.detail", values)



class WebsiteHrRecruitmentExtended(WebsiteHrRecruitment):


    @http.route('/jobs/apply/<model("hr.job"):job>', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, job, **kwargs):
        response = super(WebsiteHrRecruitmentExtended, self).jobs_apply(job, **kwargs)
        sources = request.env['utm.source'].search([])
        degree = request.env['hr.recruitment.degree'].search([])
        response.qcontext['sources'] = sources
        response.qcontext['degree'] = degree
        return response