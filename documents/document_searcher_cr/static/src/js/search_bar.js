/** @odoo-module **/

import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from "@web/core/utils/patch";

patch(SearchBar.prototype,{
    setup() {
		super.setup();
    },
    getModelName(){
        return this.env.searchModel.resModel;
    }
});



