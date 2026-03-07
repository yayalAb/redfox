import { registry } from "@web/core/registry";
import { FloatField, floatField } from "@web/views/fields/float/float_field";
import { parseFloat } from "@web/views/fields/parsers";
import { _t } from "@web/core/l10n/translation";
import { onPatched } from "@odoo/owl";

export class SalaryValidation extends FloatField {
    static props = {
        ...FloatField.props,
    };

    setup() {
        super.setup();
        this.errorMessage = _t("⚠️ must be a non-negative number.");

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
            const numValue = parseFloat(value);
            if (numValue >= 0) {
                this.props.record.setInvalidField(this.props.name, false);
                return numValue;
            } else {
                throw new Error("Negative number is invalid");
            }
        } catch (e) {
            this.props.record.setInvalidField(this.props.name, this.errorMessage);
            throw new Error("Salary validation failed");
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
                const numValue = parseFloat(value);
                isValid = numValue >= 0;
            } catch (e) {
                isValid = false;
            }
        }

        const wrapper = this.inputRef.el.closest('.o_field_widget');
        if (!wrapper) {
            return;
        }

        wrapper.classList.toggle('o_field_invalid', !isValid);
        const existingError = wrapper.querySelector('.o_salary_error_message');

        if (!isValid) {
            if (!existingError) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'o_salary_error_message text-danger small mt-1';
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
            const existingError = wrapper.querySelector('.o_salary_error_message');
            if (existingError) {
                existingError.remove();
            }
            wrapper.classList.remove('o_field_invalid');
        }
    }
}

export const salaryValidationField = {
    ...floatField,
    component: SalaryValidation,
    displayName: "Validated Salary",
    supportedTypes: ["float"],
};

registry.category("fields").add("salary_validation", salaryValidationField);