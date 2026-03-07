/** @odoo-module */

import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";


patch(SearchBar.prototype, {
	setup() {
		super.setup();
        // this.rpc = useService("rpc");
	},
	async _onClickCustom() {
		var self = this;
		var input_value = document.getElementById('search_custom_input').value
        if(input_value != ''){
            await rpc('/search_document',
                {searching_for: input_value}).then( (found_records) =>{
                    return self.env.model.action.doAction({
                            type: 'ir.actions.act_window',
                            name: _t('Documents'),
                            res_model: 'documents.document',
                            view_type: 'kanban,list',
                            views: [[false, 'kanban'], [false, 'list']],
                            view_mode: 'kanban',
                            domain: [['id', 'in', found_records]],
                            target: 'main',
                            tag: 'reload',
                    });
                }
            )
        }
    },
});