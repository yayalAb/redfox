import { url } from "@web/core/utils/urls"
import { useService } from "@web/core/utils/hooks"
import { Component, onWillUnmount, useState } from "@odoo/owl"

export class AppsBar extends Component {
    static template = "muk_web_appsbar.AppsBar"
    static props = {}

    setup() {
        this.companyService = useService("company")
        this.appMenuService = useService("app_menu")
        this.state = useState({
            openSubmenu: null, // Track which submenu is currently open
        })

        if (this.companyService.currentCompany.has_appsbar_image) {
            this.sidebarImageUrl = url("/web/image", {
                model: "res.company",
                field: "appbar_image",
                id: this.companyService.currentCompany.id,
            })
        }

        const renderAfterMenuChange = () => {
            this.render()
        }

        this.env.bus.addEventListener(
            "MENUS:APP-CHANGED",
            renderAfterMenuChange
        )

        onWillUnmount(() => {
            this.env.bus.removeEventListener(
                "MENUS:APP-CHANGED",
                renderAfterMenuChange
            )
        })
    }

    _onAppClick(app, ev) {
        // If the app has children, toggle its submenu
        if (this._hasChildren(app)) {
            // Close if clicking the same menu, otherwise open the clicked one
            this.state.openSubmenu =
                this.state.openSubmenu === app.id ? null : app.id
            ev.stopPropagation() // Prevent event bubbling
        } else {
            // If no children, select the app and close any open submenu
            this.state.openSubmenu = null
            return this.appMenuService.selectApp(app)
        }
    }

    _hasChildren(app) {
        return app.children && app.children.length > 0
    }

    _isSubmenuOpen(app) {
        return this.state.openSubmenu === app.id
    }
}
