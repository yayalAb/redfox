# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from ..utils import controller_utils as utils
from ..utils import schemas
from pydantic import ValidationError
from odoo import fields
from ..utils.mail_utils import get_smtp_server_email, get_reviewers
import json


class SupplierRegistration(http.Controller):
    @http.route(['/supplies/register'], type='http', auth='public', website=True)
    def show_supplier_registration(self):
        """
        Renders the supplier registration page  '
        """
        if not request.env.user.is_public:
            return request.redirect('/my')
        ctx = {}
        ctx['categories'] = request.env['product.category'].sudo().search([])
        return request.render('supplier_registration.portal_supplier_registration', ctx)

    @http.route(['/supplies/register/send-otp'], type='json', auth='none', methods=['POST'])
    def send_otp(self):
        """
        Sends an OTP to the given mobile number
        """
        email = request.params.get('email')
        is_valid, message = utils.validate_email_address(request, email)
        if not is_valid:
            return utils.format_response('error', message)
        # limit 5 OTPs sent to an email address which is not expired
        otps = request.env['supplies.registration.otp'].sudo().search(
            [('email', '=', email), ('expiry_time', '>=', fields.Datetime.now())]
        )
        if len(otps) >= 5:
            return utils.format_response('error', 'Maximum number of OTPs sent. Please try again later')
        otp_obj = request.env['supplies.registration.otp'].sudo().create(
            {'email': email}
        )
        try:
            otp_obj.send_otp_email()
        except Exception as e:
            return utils.format_response('error', 'Failed to send OTP')
        return utils.format_response('success', 'OTP sent successfully to your email address')

    @http.route(['/supplies/register/verify-otp'], type='json', auth='none', methods=['POST'])
    def verify_otp(self):
        """
        Verifies the OTP
        """
        email = request.params.get('email')
        otp = request.params.get('otp')
        otp_obj = request.env['supplies.registration.otp'].sudo().search(
            [('email', '=', email), ('otp', '=', otp), ('expiry_time', '>=', fields.Datetime.now())]
        )
        if not otp_obj or not otp_obj.verify_otp():
            return utils.format_response('error', 'Invalid OTP')
        return utils.format_response('success', 'OTP verified successfully')

    @http.route(['/supplies/register/submit'], type='http', auth='public', methods=['POST'], csrf=False)
    def submit_registration(self, **post):
        """
        Handles the submission of the supplier registration form
        """
        form_data = request.httprequest.form
        files = request.httprequest.files
        otp = form_data.get('otp')
        email = form_data.get('email')
        otp_obj = request.env['supplies.registration.otp'].sudo().search(
            [('email', '=', email), ('otp', '=', otp)]
        )
        if not otp_obj:
            return request.make_response(
                json.dumps(
                    utils.format_response('error', 'Invalid OTP')
                ),
                headers={'Content-Type': 'application/json'}
            )
        if not utils.check_unique_tin_trade_lic(request.env, form_data):
            return request.make_response(
                json.dumps(
                    utils.format_response('error', '<h3>TIN or Trade License already exists</h3>')
                ),
                headers={'Content-Type': 'application/json'}
            )
        try:
            reg_data_schema = schemas.SupplierRegistrationSchema(**form_data, **files)
            registration = utils.create_supplier_registration(request.env, reg_data_schema.model_dump())
        except ValidationError as e:
            errors = e.errors(include_input=False, include_context=False, include_url=False)
            data = json.dumps(
                utils.format_response(
                    'error',
                    'Data validation failed',
                    {
                        'html': utils.render_registration_error_html(request.env, errors)
                    }
                )
            )
        else:
            reviewers = get_reviewers(request.env)
            reg_url = utils.generate_registration_url(request.env, registration.id)
            email_values = {
                'email_from': get_smtp_server_email(request.env),
            }
            contexts = {
                'reg_url': reg_url,
                'company_name': request.env.company.name,
            }
            for reviewer in reviewers:
                template = request.env.ref('VendorBid.email_template_model_supplies_vendor_registration_reviewer').sudo()
                template.with_context(**contexts).send_mail(reviewer.id, email_values=email_values)

            data = json.dumps(
                utils.format_response(
                    'success',
                    'Registration successful',
                    {
                        'html': utils.render_qweb_template(
                            request.env,
                            'VendorBid.supplier_registration_success'
                        )
                    }
                )
            )
        return request.make_response(data, headers={'Content-Type': 'application/json'})