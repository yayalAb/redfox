/** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { CharField } from "@web/views/fields/char/char_field";
// import { _t } from "@web/core/l10n/translation";
// import { useService } from "@web/core/utils/hooks";

// /**
//  * A custom CharField widget that validates phone numbers on blur
//  * and shows an inline error message if invalid.
//  */
// export class PhoneField extends CharField {
//     setup() {
//         super.setup(...arguments);
//         this.notification = useService("notification");
//     }

//     onBlur() {
//         super.onBlur(...arguments);
//         this._validatePhoneField();
//     }

//     _validatePhoneField() {
//         let value = this.input.el.value.trim();
//         // don't validate empty field
//         if (!value) {
//             // remove existing message if any
//             const wrapper = this.input.el.closest('.o_field_widget');
//             const existing = wrapper.querySelector('.o_phone_error');
//             if (existing) {
//                 existing.remove();
//                 wrapper.classList.remove('o_field_invalid');
//             }
//             return;
//         }

//         value = this.input.el.value || '';
//         const regex = /^(0\d{9}|\+251\d{9}|\(\+251\)\d{9}|\(\d{3}\)-\d{3}-\d{4})$/;
//         const isValid = regex.test(value);

//         const wrapper = this.input.el.closest('.o_field_widget');
//         wrapper.classList.toggle('o_field_invalid', !isValid);

//         let msg = wrapper.querySelector('.o_phone_error');
//         if (!isValid) {
//             if (!msg) {
//                 msg = document.createElement('div');
//                 msg.className = 'o_phone_error text-danger small mt-1';
//                 msg.innerText = _t(
//                     '⚠️ Invalid phone number.'
//                 );
//                 wrapper.appendChild(msg);
//             }

//             this.notification.add(_t(
//                 'Phone number is not valid.\nExamples:\n' +
//                 '• 0912345678\n' +
//                 '• +251912345678\n' +
//                 '• (+251)912345678\n' +
//                 '• (123)-456-7890'
//             ), {
//                 title: _t("Invalid Phone Number"),
//                 type: "warning",
//             });
//         } else if (msg) {
//             msg.remove();
//         }
//     }
// }

// // Register the widget
// export const phoneField = {
//     component: PhoneField,
//     displayName: _t('Phone'),
//     supportedTypes: ['char'],
// };

// registry.category('fields').add('phone_field', phoneField);

import { registry } from "@web/core/registry";
import { PhoneField as BasePhoneField } from "@web/views/fields/phone/phone_field";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { useRef, onMounted } from "@odoo/owl";

export class PhoneField extends BasePhoneField {
    static template = "web.FormPhoneField";

    setup() {
        super.setup(...arguments)
        this.notification = useService("notification");
        this.input = useRef("input");
        onMounted(() => {
            if (this.input.el) {
                this.input.el.addEventListener("blur", this.onBlur.bind(this));
            } else {
                console.warn("Input element not found in PhoneField");
            }
        });
    }

    onBlur() {
        console.log("Validating");
        this._validatePhoneField();
    }

    _validatePhoneField() {
        let value = this.input.el.value.trim();
        // don't validate empty field
        if (!value) {
            // remove existing message if any
            const wrapper = this.input.el.closest('.o_field_widget');
            const existing = wrapper.querySelector('.o_phone_error');
            if (existing) {
                existing.remove();
                wrapper.classList.remove('o_field_invalid');
            }
            return;
        }

        value = this.input.el.value || '';
        const regex = /^(0\d{9}|\+251\d{9}|\(\+251\)\d{9}|\(\d{3}\)-\d{3}-\d{4})$/;
        const isValid = regex.test(value);

        const wrapper = this.input.el.closest('.o_field_widget');
        wrapper.classList.toggle('o_field_invalid', !isValid);

        let msg = wrapper.querySelector('.o_phone_error');
        if (!isValid) {
            if (!msg) {
                msg = document.createElement('div');
                msg.className = 'o_phone_error text-danger small mt-1';
                msg.innerText = _t(
                    '⚠️ Invalid phone number.'
                );
                wrapper.appendChild(msg);
            }

            this.notification.add(_t(
                'Phone number is not valid.\nExamples:\n' +
                '• 0912345678\n' +
                '• +251912345678\n' +
                '• (+251)912345678\n' +
                '• (123)-456-7890'
            ), {
                title: _t("Invalid Phone Number"),
                type: "warning",
            });
        } else if (msg) {
            msg.remove();
        }
    }

}

// Register the widget
export const phoneField = {
    component: PhoneField,
    displayName: _t('Phone'),
    supportedTypes: ['char'],
};

registry.category('fields').add('phone_field', phoneField);
