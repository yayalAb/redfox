import { registry } from "@web/core/registry";
import { IntegerField, integerField } from "@web/views/fields/integer/integer_field";
import { parseInt } from "@web/views/fields/parsers";
import { _t } from "@web/core/l10n/translation";
import { onPatched } from "@odoo/owl";

/**
 * NonNegativeIntegerValidation is a widget for integer fields that ensures the
 * entered value is a non-negative number (>= 0).
 * It provides immediate visual feedback to the user by adding a validation
 * class and an error message if the input is invalid.
 */
export class NonNegativeIntegerValidation extends IntegerField {
    static props = {
        ...IntegerField.props,
    };

    setup() {
        super.setup();
        // Reusable error message
        this.errorMessage = _t("⚠️ must be a non-negative number.");

        // Update validation on each patch/re-render
        onPatched(() => {
            this._updateVisualValidation();
        });
    }

    /**
     * Parses the string value from the input.
     * @param {string} value The value from the input element.
     * @returns {number} The parsed integer value.
     */
    parse(value) {
        // An empty field is considered valid and parsed as 0
        if (value === "") {
            this.props.record.setInvalidField(this.props.name, false);
            return 0;
        }
        
        try {
            // Use Odoo's parseInt to handle user's language format
            const numValue = parseInt(value);
            if (numValue >= 0) {
                // Mark the field as valid in the record model
                this.props.record.setInvalidField(this.props.name, false);
                return numValue;
            } else {
                // Value is negative, which is invalid
                throw new Error("Negative number is invalid");
            }
        } catch (e) {
            // Any parsing error or validation failure marks the field as invalid
            this.props.record.setInvalidField(this.props.name, this.errorMessage);
            throw new Error("Integer validation failed");
        }
    }

    /**
     * When the user leaves the field, trigger a visual update.
     */
    onFocusOut() {
        super.onFocusOut(...arguments);
        this._updateVisualValidation();
    }

    /**
     * Clean up visual validation elements when the component is destroyed.
     */
    onWillUnmount() {
        super.onWillUnmount();
        this._removeErrorMessage();
    }

    /**
     * Manages the visual feedback (red border and error message) on the DOM.
     * This method directly inspects the input's current value for immediate feedback.
     */
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
                const numValue = parseInt(value);
                isValid = numValue >= 0 && Number.isInteger(numValue);
            } catch (e) {
                isValid = false;
            }
        }

        const wrapper = this.inputRef.el.closest('.o_field_widget');
        if (!wrapper) {
            return;
        }

        // Toggle invalid class for CSS styling (e.g., red border)
        wrapper.classList.toggle('o_field_invalid', !isValid);
        const existingError = wrapper.querySelector('.o_non_negative_error_message');

        if (!isValid) {
            if (!existingError) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'o_non_negative_error_message text-danger small mt-1';
                errorDiv.innerText = this.errorMessage;
                wrapper.appendChild(errorDiv);
            }
        } else if (existingError) {
            existingError.remove();
        }
    }

    /**
     * Helper to safely remove the error message and invalid class.
     */
    _removeErrorMessage() {
        const wrapper = this.inputRef.el?.closest('.o_field_widget');
        if (wrapper) {
            const existingError = wrapper.querySelector('.o_non_negative_error_message');
            if (existingError) {
                existingError.remove();
            }
            wrapper.classList.remove('o_field_invalid');
        }
    }
}

export const nonNegativeIntegerField = {
    ...integerField,
    component: NonNegativeIntegerValidation,
    displayName: "Validated Integer",
    supportedTypes: ["integer"],
};

registry.category("fields").add("non_negative_integer", nonNegativeIntegerField);