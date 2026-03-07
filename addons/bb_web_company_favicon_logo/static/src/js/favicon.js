/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient"
import {patch} from "@web/core/utils/patch";
import { useComponent } from "@odoo/owl";

patch(WebClient.prototype,  {
    setup() {
        super.setup();
        const component = useComponent();
        const env = component.env;
        const favicon = `/web/image/res.company/${env.services.company.currentCompany.id}/favicon`;
        const icons = document.querySelectorAll("link[rel*='icon']");
        const msIcon = document.querySelector("meta[name='msapplication-TileImage']");
        for (const icon of icons) {
            icon.href = favicon;
        }
        if (msIcon) {
            msIcon.content = favicon;
        }
    },
});