/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useSignViewButtons } from "@sign_custom/views/hooks";
import { Dropdown, DropdownItem } from "@web/core/dropdown/dropdown";
import { SignDocumentDropZone } from "../../mixin/document_upload";
import { SignActionHelper } from '@sign_custom/views/helper/sign_action_helper';

export class SignListController extends ListController {
    static template = "sign.SignListController";
    static components = {
        ...ListController.components,
        Dropdown,
        DropdownItem,
    };

    setup() {
        super.setup(...arguments);
        const functions = useSignViewButtons();
        Object.assign(this, functions);
    }
}

export class SignListRenderer extends SignDocumentDropZone(ListRenderer)  {
    static template = "sign.ListRenderer";
    static components = {
        ...ListRenderer.components,
        SignActionHelper,
    };
}
