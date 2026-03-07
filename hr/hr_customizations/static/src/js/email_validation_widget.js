/** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { CharField } from "@web/views/fields/char/char_field";
// import { _t } from "@web/core/l10n/translation";
// import { useService } from "@web/core/utils/hooks";

// /**
//  * A custom CharField widget that validates email format on blur
//  * and shows an inline error message if invalid.
//  */
// export class EmailField extends CharField {
//     /**
//      * Extend onBlur to run CharField's logic, then validate
//      */

//     setup() {
//         super.setup(...arguments)
//         this.notification = useService("notification");
//     }

//     onBlur() {
//         super.onBlur(...arguments);
//         this._validateEmailField();
//     }

//     /**
//      * Validate only this field, using an email regex.
//      */
//     _validateEmailField() {
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
//         // Simple email regex (can be refined as needed)
//         const regex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
//         const isValid = regex.test(value);

//         // find the nearest widget wrapper div
//         const wrapper = this.input.el.closest('.o_field_widget');
//         // toggle Odoo's built-in invalid class
//         wrapper.classList.toggle('o_field_invalid', !isValid);

//         // inline error message
//         let msg = wrapper.querySelector('.o_email_error');
//         if (!isValid) {
//             if (!msg) {
//                 msg = document.createElement('div');
//                 msg.className = 'o_email_error text-danger small mt-1';
//                 msg.innerText = _t('⚠️ Invalid email address');
//                 wrapper.appendChild(msg);
//             }
//             this.notification.add(_t("An email should look like user@example.com"), {
//                 title: _t("Invalid Email"),
//                 type: "warning",
//                 sticky: false,            // auto-close (default)
//             });
//         } else if (msg) {
//             msg.remove();
//         }
//     }
// }

// // Register under a new widget name
// export const emailField = {
//     component: EmailField,
//     displayName: _t('Email'),
//     supportedTypes: ['char'],
// };

// registry.category('fields').add('email_field', emailField);

import { registry } from "@web/core/registry";
import { EmailField as BaseEmailField } from "@web/views/fields/email/email_field";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { useRef, onMounted } from "@odoo/owl";

export class EmailField extends BaseEmailField {
    static template = "web.FormEmailField";

    setup() {
        super.setup(...arguments)
        this.input = useRef("input")
        this.notification = useService("notification");
        onMounted(() => {
            if(this.input.el){
                this.input.el.addEventListener("blur", this.onBlur.bind(this));
            } else {
                console.log("Input element not found for the Email Field")
            }
        });
    }

    onBlur() {
        this._validateEmailField();
    }

    /**
     * Validate only this field, using an email regex.
     */
    _validateEmailField() {
        const value = this.input.el.value || '';
        // Simple email regex (can be refined as needed)
        const regex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
        const isValid = regex.test(value);

        // find the nearest widget wrapper div
        const wrapper = this.input.el.closest('.o_field_widget');
        // toggle Odoo's built-in invalid class
        wrapper.classList.toggle('o_field_invalid', !isValid);

        // inline error message
        let msg = wrapper.querySelector('.o_email_error');
        if (!isValid) {
            if (!msg) {
                msg = document.createElement('div');
                msg.className = 'o_email_error text-danger small mt-1';
                msg.innerText = _t('⚠️ Invalid email address');
                wrapper.appendChild(msg);
            }
            this.notification.add(_t("An email should look like user@example.com"), {
                title: _t("Invalid Email"),
                type: "warning",
                sticky: false,            // auto-close (default)
            });
        } else if (msg) {
            msg.remove();
        }
    }
}

// Register under a new widget name
export const emailField = {
    component: EmailField,
    displayName: _t('Email'),
    supportedTypes: ['char'],
};

registry.category('fields').add('email_field', emailField);
