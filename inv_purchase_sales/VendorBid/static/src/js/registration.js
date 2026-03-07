// ELEMENT IDs
const OTP_FORM_CONTAINER_ID = '#otp_container';
const REG_FORM_CONTAINER_ID = '#registration_form_container';
const CSRF_INPUT_ID = '#csrf_token';
const SEND_OTP_BTN_ID = '#send_otp_btn';
const EMAIL_INPUT_ID = '#email';
const OTP_INPUT_CONTAINER_ID = '#otp_input_container';
const VERIFY_OTP_BTN_ID = '#verify_otp_btn';
const OTP_RESEND_BTN_ID = '#resend_otp_button';
const ALERT_CONTAINER_ID = '#alert_container';
const STEPS_CONTAINER_ID = '#steps_container';
const CLIENT_REF_CONTAINER_ID = '#step_3';
const ADD_MORE_CLIENT_BTN_ID = '#add_client_reference';
const NEXT_BTN_ID = '#next_btn';
const PREV_BTN_ID = '#prev_btn';
const SUBMIT_BTN_ID = '#submit_btn';
const DECLARATION_CHECKBOX_ID = '#declarationCheckbox';
const MODAL_1 = 'modal_1';
const WINDOW_1_ID = '#window_1';
const WINDOW_2_ID = '#window_2';
const PROGRESS_BAR_ID = '#progress_bar';
// API Endpoints
const SEND_OTP_API = '/supplies/register/send-otp';
const VERIFY_OTP_API = '/supplies/register/verify-otp';
const SUBMIT_FORM_API = '/supplies/register/submit';
// Constants
const NUM_OTP_DIGITS = 6;


function get_csrf_token() {
    return $(CSRF_INPUT_ID).val();
}

const pageManager = {
    totalSteps: 5,
    page: 1,
    email: '',
    otp: '',
    data: {},
    goNext: function () {
        const supplierType = $("select[name='supplier_type']").val();

        if (this.page < this.totalSteps) {
            // If current step = 1 and supplier is local → jump to step 3
            if (this.page === 1 && supplierType === "local") {
                this.page = 3;
            } else {
                this.page += 1;
            }
            this.showStep();
        }
        this.setProgressBar();
        return this.page;
    },
    goBack: function () {
        const supplierType = $("select[name='supplier_type']").val();

        if (this.page > 1) {
            // If currently at step 3 and supplier is local → jump back to step 1
            if (this.page === 3 && supplierType === "local") {
                this.page = 1;
            } else {
                this.page -= 1;
            }
            this.showStep();
        }
        this.setProgressBar();
        return this.page;
    },
    setProgressBar: function () {
        $(PROGRESS_BAR_ID).css('width', `${(this.page / this.totalSteps) * 100}%`);
    },
    showStep: function () {
        $(`${STEPS_CONTAINER_ID} .step`).each((index, element) => {
            if (index + 1 === this.page) {
                $(element).show();
            } else {
                $(element).hide();
            }
        });
        if (this.page === 1) {
            $(PREV_BTN_ID).hide();
        } else {
            $(PREV_BTN_ID).show();
        }
        if (this.page === this.totalSteps) {
            $(NEXT_BTN_ID).hide();
            $(SUBMIT_BTN_ID).show();
        } else {
            $(NEXT_BTN_ID).show();
            $(SUBMIT_BTN_ID).hide();
        }

    },
    getRegData: function () {
        const data = {};
        $(REG_FORM_CONTAINER_ID).find('input, select').each((index, element) => {
            let name = $(element).attr('name');
            let type = $(element).attr('type');
            if (!name) {
                return;
            }
            if (type === 'file') {
                const files = element.files;
                if (files && files.length) {
                    // If the input allows multiple files
                    if ($(element).prop('multiple')) {
                        // Convert FileList to an array.
                        data[name] = Array.from(files);
                    } else {
                        // Otherwise, store the first file.
                        data[name] = files[0];
                    }
                }
            } else {
                let value = $(element).val();
                if (value) {
                    data[name] = value;
                }
            }
        });
        return data;
    },
    getFormData: function () {
        const formData = new FormData();
        const regData = this.getRegData();

        for (const key in regData) {
            if (Array.isArray(regData[key])) {
                regData[key].forEach((file, index) => {
                    formData.append(`${key}_${index}`, file);
                });
            } else {
                formData.append(key, regData[key]);
            }
        }
        const csrf_token = get_csrf_token();
        formData.append('csrf_token', csrf_token);
        formData.append('email', this.email);
        formData.append('otp', this.otp);
        return formData;
    },
    handleSubmitForm: function (handler) {
        if (typeof handler !== 'function') {
            return;
        }
        if (this.page !== this.totalSteps) {
            return;
        }
        const formData = this.getFormData();
        handler(formData);
    }
}

function goNextWindow() {
    $(WINDOW_1_ID).fadeOut(100, () => {
        $(WINDOW_2_ID).fadeIn(200, () => {
            setTimeout(() => {
                $('.otp-input').first().focus();
            }, 300)
            setTimeout(() => {
                $(OTP_RESEND_BTN_ID).removeAttr('disabled');
            }, 3000)
        });
    });
}

function showModal(id, body_content = null, static_backdrop = false, hide_close_btn = false) {
    if (body_content) {
        $(`#${id} .modal-body`).html(body_content);
    }
    if (static_backdrop) {
        $(`#${id}`).attr('data-bs-backdrop', 'static');
        $(`#${id}`).attr('data-bs-keyboard', false);
    } else {
        $(`#${id}`).removeAttr('data-bs-backdrop');
    }
    if (hide_close_btn) {
        $(`#${id} .modal-header .btn-close`).hide();
    } else {
        $(`#${id} .modal-header .btn-close`).show();
    }
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}


function showToast(message, title = "Error", scope = "danger") {
    const toastLiveExample = document.getElementById('liveToast')
    const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastLiveExample)
    toastLiveExample.querySelector('.toast-body').innerText = message
    toastLiveExample.querySelector('.title').innerText = title
    toastLiveExample.classList.remove('bg-danger', 'bg-warning', 'bg-success', 'bg-info')
    toastLiveExample.classList.add(`bg-${scope}`)
    toastBootstrap.show()
}

function validateStepInputs(step) {
    let isValid = true;
    const toggleIsInvalid = (element, isInvalid) => {
        if (isInvalid) {
            $(element).addClass('is-invalid');
            isValid = false;
        } else {
            $(element).removeClass('is-invalid');
        }
        return isInvalid;
    }
    // Check all input fields of the step
    $(`#step_${step} input`).each((index, element) => {
        // skip file input
        if ($(element).attr('type') === 'file') {
            if ($(element).attr('required') && !$(element).val()) {
                toggleIsInvalid(element, true);
            }
        }
        // first check if the input is required
        if ($(element).attr('required')) {
            let notValid = toggleIsInvalid(element, !$(element).val());
            if (notValid) {
                if (!$(element).next().hasClass('invalid-feedback')) {
                    $('<div class="invalid-feedback">This field is required</div>').insertAfter($(element));
                }
            } else {
                if ($(element).next().hasClass('invalid-feedback')) {
                    $(element).next().remove();
                }
            }
        }
        // check for pattern
        if ($(element).attr('pattern')) {
            const pattern = new RegExp($(element).attr('pattern'));
            toggleIsInvalid(element, !pattern.test($(element).val()));
        }
        // validate date input min and max set
        if ($(element).attr('type') === 'date' && $(element).val()) {
            const min = $(element).attr('min');
            const max = $(element).attr('max');
            if (min) {
                toggleIsInvalid(element, $(element).val() < min);
            }
            if (max) {
                toggleIsInvalid(element, $(element).val() > max);
            }
        }
    });
    // Check dependent fields
    // First it catches all the fields which is required if some other field is filled. Their classes are set on the data attribute "data-requires-if"
    // Then it checks from the `data-container-class` of the dependent field for the required fields.
    $(`#step_${step} input[data-requires-if]`).each((index, element) => {
        const dependentField = $(element);
        if (dependentField.val()) {
            toggleIsInvalid(element, false);
            return;
        }
        const requiredFieldClasses = dependentField.data('requires-if').split(',');
        const parent = dependentField.closest(`.${dependentField.data('container-class')}`);
        let requiredFields = parent.find(
            requiredFieldClasses.map((className) => `.${className}`).join(',')
        )
        const any_field_filled = requiredFields.map((index, field) => $(field).val().length > 0).get().some((val) => val);
        toggleIsInvalid(element, any_field_filled);
    });
    return isValid;
}

function isValidEmail(email) {
    const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return emailPattern.test(email);
}

function addMoreClientReference() {
    const total_clients = $(`${CLIENT_REF_CONTAINER_ID} .client`).length;
    const visible_clients = $(`${CLIENT_REF_CONTAINER_ID} .client`).filter(function () {
        return $(this).css("display") !== "none";
    }).length;
    // show the next client with display=none if visible clients are less than total clients
    if (visible_clients < total_clients) {
        $(`${CLIENT_REF_CONTAINER_ID} .client`).each(function () {
            if ($(this).css("display") === "none") {
                $(this).show();
                return false;
            }
        });
        if (visible_clients + 1 === total_clients) {
            $(ADD_MORE_CLIENT_BTN_ID).hide();
        }
    }
}

function format_rpc_data(data) {
    return {
        jsonrpc: '2.0',
        method: 'call',
        params: data,
    };
}

function send_otp() {
    const email = $(EMAIL_INPUT_ID).val();
    if (!isValidEmail(email)) {
        showToast('Invalid email address');
        return;
    }
    $.ajax({
        type: 'POST',
        url: SEND_OTP_API,
        contentType: 'application/json',
        dataType: 'json',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
            $(SEND_OTP_BTN_ID).prop('disabled', true);
        },
        data: JSON.stringify(format_rpc_data({ email: email })),
        success: function (data) {
            if (data?.result?.status === 'success') {
                goNextWindow();
            } else {
                showToast(data?.result?.message || 'Failed to send OTP');
            }
        },
        error: function (xhr, status, error) {
            showToast('Failed to send OTP');
        },
        complete: function () {
            $(SEND_OTP_BTN_ID).prop('disabled', false);
        },
    });
}

function resend_otp() {
    const email = $(EMAIL_INPUT_ID).val();
    $.ajax({
        type: 'POST',
        url: SEND_OTP_API,
        contentType: 'application/json',
        dataType: 'json',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
            $(OTP_RESEND_BTN_ID).prop('disabled', true);
            let countdown = 15;
            const interval = setInterval(() => {
                $(OTP_RESEND_BTN_ID).text(`Resend OTP in ${countdown} seconds`);
                countdown -= 1;
            }, 1000);
            setTimeout(() => {
                clearInterval(interval);
                $(OTP_RESEND_BTN_ID).text('Resend OTP');
                $(OTP_RESEND_BTN_ID).prop('disabled', false);
            }, 15 * 1000);
        },
        data: JSON.stringify(format_rpc_data({ email: email })),
        success: function (data) {
            if (data?.result?.status === 'success') {
                showToast('OTP resent successfully, please check your inbox/spam', 'Success', 'success');
            } else {
                showToast(data?.result?.message || 'Failed to send OTP');
            }
        },
        error: function (xhr, status, error) {
            showToast('Failed to send OTP');
        },
    });
}

function getOtpInput() {
    const otp = [];
    $('.otp-input').each((index, element) => {
        const value = $(element).val();
        if (value) {
            otp.push(value);
        }
    });
    if (otp.length !== NUM_OTP_DIGITS) {
        return null;
    }
    return otp.join('');
}

function verify_otp() {
    const email = $(EMAIL_INPUT_ID).val();
    const otp = getOtpInput();
    if (!otp) {
        showToast('Please enter valid OTP');
        return;
    }
    $.ajax({
        type: 'POST',
        url: VERIFY_OTP_API,
        contentType: 'application/json',
        dataType: 'json',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
            $(VERIFY_OTP_BTN_ID).prop('disabled', true);
        },
        data: JSON.stringify(format_rpc_data({ email: email, otp: otp })),
        success: function (data) {
            if (data?.result?.status === 'success') {
                showToast('OTP verified successfully, proceeding to next step', 'Success', 'success');
                setTimeout(() => {
                    $(WINDOW_2_ID).fadeOut(200, () => {
                        $(REG_FORM_CONTAINER_ID).show(200);
                        pageManager.email = email;
                        pageManager.otp = otp;
                    });
                }, 1500);
            } else {
                const error_msg = data?.result?.message || 'Invalid OTP. Please try again.';
                showToast(error_msg);
            }
        },
        error: function (xhr, status, error) {
            showToast('Invalid OTP. Please try again.')
        },
        complete: function () {
            $(VERIFY_OTP_BTN_ID).prop('disabled', false);
        },
    });
}

function submit_form(formData) {
    $.ajax({
        type: 'POST',
        url: SUBMIT_FORM_API,
        contentType: false,
        processData: false,
        beforeSend: function () {
            $(SUBMIT_BTN_ID).prop('disabled', true);
        },
        data: formData,
        success: function (data) {
            if (data?.status === 'success') {
                showModal(
                    MODAL_1,
                    data?.data?.html || 'Form submitted successfully',
                    true,
                    true
                );
            } else {
                showModal(MODAL_1, data?.data?.html || data?.message || 'Failed to submit form', true);
            }
        },
        error: function (xhr, status, error) {
            showModal(
                MODAL_1,
                "<div class='alert alert-danger my-4'>Failed to submit form</div>",
            )
        },
        complete: function () {
            $(SUBMIT_BTN_ID).prop('disabled', false);
        },
    });
}

function enableOtpInput() {
    $(".otp-input").on('keyup', function (e) {
        if (e.keyCode === 8) {
            return;
        }
        const current_position = $(this).data('position');
        if (e.keyCode === 13) {
            verify_otp();
        }
        if (isNaN(parseInt($(this).val()))) {
            $(this).val('');
            return;
        }
        const next_position = current_position + 1;
        if (next_position <= NUM_OTP_DIGITS) {
            $(`input[data-position=${next_position}]`).removeAttr('disabled').focus();
        } else {
            $(VERIFY_OTP_BTN_ID).removeAttr('disabled');
        }
    });
    $('input[data-position="1"]').on('paste', function (e) {
        e.preventDefault();
        var pastedData = e.originalEvent.clipboardData.getData('text');
        var digits = pastedData.match(/\d/g);
        if (digits && digits.length > 0) {
            var numDigits = Math.min(digits.length, 6);
            for (var i = 1; i <= numDigits; i++) {
                var input = $('input[data-position="' + i + '"]');
                input.val(digits[i - 1]);
                input.removeAttr('disabled');
            }
            if (numDigits < 6) {
                var nextInput = $('input[data-position="' + (numDigits + 1) + '"]');
                if (nextInput.length > 0) {
                    nextInput.removeAttr('disabled').focus();
                }
            } else {
                $(VERIFY_OTP_BTN_ID).removeAttr('disabled');
                $('input[data-position="6"]').focus();
            }
        }
    });
}

$(document).ready(function () {

    $(document).on("change", "select[name='supplier_type']", function () {
        let supplierType = $(this).val();

        if (supplierType === "local") {
            $("#step_2").hide()
        } else {
            $("#step_2").show()
        }

        // 🔥 Force re-render so only the current page is visible
        pageManager.showStep();
        pageManager.setProgressBar();
    });

    $(SEND_OTP_BTN_ID).on('click', send_otp);
    $(OTP_RESEND_BTN_ID).on('click', resend_otp);
    $(VERIFY_OTP_BTN_ID).on('click', verify_otp);
    $(NEXT_BTN_ID).on('click', () => {
        validateStepInputs(pageManager.page);
        pageManager.goNext();
    });
    $(PREV_BTN_ID).on('click', () => {
        pageManager.goBack();
    });
    $(ADD_MORE_CLIENT_BTN_ID).on('click', addMoreClientReference);
    $(SUBMIT_BTN_ID).on('click', () => {
        validateStepInputs(pageManager.page);
        pageManager.handleSubmitForm(submit_form);
    });
    $(DECLARATION_CHECKBOX_ID).on('change', function () {
        const isChecked = $(this).is(':checked');
        $(SUBMIT_BTN_ID).prop('disabled', !isChecked);
    });
    $(EMAIL_INPUT_ID).on('keyup', function (e) {
        if (e.keyCode === 13) {
            send_otp();
        }
    });
    $(OTP_INPUT_CONTAINER_ID).on('keyup', 'input', function (e) {
        if (e.keyCode === 13) {
            verify_otp();
        }
    });
    enableOtpInput();
});