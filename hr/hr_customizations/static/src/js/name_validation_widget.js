/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

/**
 * A custom CharField widget that validates name format on blur
 * and shows an inline error message if invalid.
 */
export class NameField extends CharField {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    }

    onBlur() {
        super.onBlur(...arguments);
        this._validateNameField();
    }

    _validateNameField() {
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
        const regex = /^[A-Za-z][A-Za-z0-9@/ ]*$/;
        const isValid = regex.test(value);

        const wrapper = this.input.el.closest('.o_field_widget');
        wrapper.classList.toggle('o_field_invalid', !isValid);

        let msg = wrapper.querySelector('.o_name_error');
        if (!isValid) {
            if (!msg) {
                msg = document.createElement('div');
                msg.className = 'o_name_error text-danger small mt-1';
                msg.innerText = _t('⚠️ Invalid name format');
                wrapper.appendChild(msg);
            }

            this.notification.add(_t(
                'Name must start with a letter and contain only letters, numbers, spaces, "@" or "/".'
            ), {
                title: _t("Invalid Name"),
                type: "warning",
            });
        } else if (msg) {
            msg.remove();
        }
    }
}

// Register the widget
export const nameField = {
    component: NameField,
    displayName: _t('Name'),
    supportedTypes: ['char'],
};

registry.category('fields').add('name_field', nameField);
