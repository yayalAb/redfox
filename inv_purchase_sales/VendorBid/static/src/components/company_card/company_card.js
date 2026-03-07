/** @odoo-module */

const { Component, onWillUpdateProps, onWillStart, useState } = owl;
import { getImageDataURI } from "../utils"

export class CompanyCard extends Component {
    static template = 'supplies.company_card';

    setup() {
        this.state = useState({
            supplier: null,
        });

        onWillStart(() => {
            const supplierId = parseInt(this.props.supplierId);
            const supplier = this.props.all_suppliers.find(s => s.id === supplierId);
            this.setSupplier(supplier);
        })

        onWillUpdateProps((nextProps) => {
            const supplierId = parseInt(nextProps.supplierId);
            const supplier = nextProps.all_suppliers.find(s => s.id === supplierId);
            this.setSupplier(supplier);       
        });
    }

    setSupplier(supplier) {
        if (supplier) {
            this.state.supplier = {
                ...supplier,
                image: getImageDataURI(supplier.image_1920),
            };
        } else {
            this.state.supplier = null;
        }
    }
}