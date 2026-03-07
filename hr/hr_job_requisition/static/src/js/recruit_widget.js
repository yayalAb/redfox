import { registry } from "@web/core/registry";
import { IntegerField, integerField } from "@web/views/fields/integer/integer_field";
import { parseInteger } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useNumpadDecimal } from "@web/views/fields/numpad_decimal_hook";
import { _t } from "@web/core/l10n/translation";
import { onPatched, useState } from "@odoo/owl";

export class RecruitValidation extends IntegerField {
    static props = {
        ...IntegerField.props,
    };

    setup() {

        this.state = useState({ hasFocus: false });
        this.errorMessage = _t("⚠️ must be a positive number.");

        useNumpadDecimal();

        this.inputRef = useInputField({
            getValue: () => this.formattedValue,
            refName: "numpadDecimal",
            parse: (v) => this.parse(v),
        });
        
        onPatched(() => {
            this._updateVisualValidation();
        });
    }

    parse(value) {
        if (value === "") {
            this.props.record.setInvalidField(this.props.name, false);
            return 0;
        }
        
        try {
            const numValue = parseInteger(value);
            if (numValue > 0) {
                this.props.record.setInvalidField(this.props.name, false);
                return numValue;
            } else {
                throw new Error("Negative number is invalid");
            }
        } catch (e) {
            this.props.record.setInvalidField(this.props.name, this.errorMessage);
            throw new Error("Recruit validation failed");
        }
    }

    onFocusOut() {
        super.onFocusOut(...arguments);
        this._updateVisualValidation();
    }

    onWillUnmount() {
        super.onWillUnmount();
        this._removeErrorMessage();
    }

    _updateVisualValidation() {
        if (!this.inputRef.el) {
            return;
        }

        const value = this.inputRef.el.value;
        let isValid;

        if (value === "") {
            isValid = true;
        } else {
            try {
                const numValue = parseInteger(value);
                isValid = numValue > 0;
            } catch (e) {
                isValid = false;
            }
        }

        const wrapper = this.inputRef.el.closest('.o_field_widget');
        if (!wrapper) {
            return;
        }

        wrapper.classList.toggle('o_field_invalid', !isValid);
        const existingError = wrapper.querySelector('.o_recruit_error_message');

        if (!isValid) {
            if (!existingError) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'o_recruit_error_message text-danger small mt-1';
                errorDiv.innerText = this.errorMessage;
                wrapper.appendChild(errorDiv);
            }
        } else if (existingError) {
            existingError.remove();
        }
    }

    _removeErrorMessage() {
        const wrapper = this.inputRef.el?.closest('.o_field_widget');
        if (wrapper) {
            const existingError = wrapper.querySelector('.o_recruit_error_message');
            if (existingError) {
                existingError.remove();
            }
            wrapper.classList.remove('o_field_invalid');
        }
    }
}

export const recruitValidationField = {
    ...integerField,
    component: RecruitValidation,
    displayName: "Validated Recruit",
    supportedTypes: ["integer"],
};

registry.category("fields").add("recruit_validation", recruitValidationField);