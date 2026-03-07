/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient"
import { useService } from "@web/core/utils/hooks"
import { useRef, onMounted } from "@odoo/owl"
import { patch } from "@web/core/utils/patch"
import { SidebarBottom } from "./SidebarBottom"
import { rpc } from "@web/core/network/rpc"
// import { Transition } from "@web/core/transition";

patch(WebClient.prototype, {
    setup() {
        super.setup()
        this.root = useRef("root")
        this.rpc = rpc
        this.companyService = useService("company")
        this.menuService = useService("menu")
        this.currentCompany = this.companyService.currentCompany

        onMounted(() => {
            this.fetchMenuData()
        })
    },
    collapsExpandedElements(ev) {
        ev.stopPropagation()
        const currentMenu = ev.currentTarget.closest(
            ".sub-menu-dropdown.show, .header-sub-menus .collapse.show"
        )
        const currentButton = ev.currentTarget.closest(
            '[data-bs-toggle="collapse"]'
        )
        const currentTargetId = currentButton
            ? currentButton.getAttribute("data-bs-target")
            : null
        const expandedMenus = document.querySelectorAll(
            ".sub-menu-dropdown.show, .header-sub-menus .collapse.show"
        )
        expandedMenus.forEach(menu => {
            if (currentMenu && menu === currentMenu) {
                return
            }

            menu.classList.remove("show")
            const toggleButtons = document.querySelectorAll(
                `[data-bs-target="#${menu.id}"]`
            )
            toggleButtons.forEach(button => {
                button.setAttribute("aria-expanded", "false")
            })
        })

        // If there was a current menu, toggle its state
        if (currentMenu) {
            const shouldShow = !currentMenu.classList.contains("show")
            currentMenu.classList.toggle("show", shouldShow)

            if (currentButton) {
                currentButton.setAttribute(
                    "aria-expanded",
                    shouldShow.toString()
                )
            }
        }
    },
    toggleSidebar(ev) {
        this.state.isSidebarOpen = !this.state.isSidebarOpen
        const toggleEl = ev.currentTarget
        toggleEl.classList.toggle("visible")
        toggleEl.classList.toggle("sidebar-open")
        const navWrapper = document.querySelector(".nav-wrapper-bits")
        if (navWrapper) {
            navWrapper.classList.toggle("toggle-show")
        }
    },

    collapsExpandedChildElements(ev) {
        ev.preventDefault()
        ev.stopPropagation()
        ev.stopImmediatePropagation()

        const currentButton = ev.currentTarget.closest("[data-menu]")
        const currentTargetId = currentButton
            ? currentButton.getAttribute("href")
            : null

        const currentMenu = currentTargetId
            ? document.querySelector(currentTargetId)
            : null

        const isAlreadyOpen =
            currentMenu && currentMenu.classList.contains("showing")

        const expandedMenus = document.querySelectorAll(
            ".sub-menu-dropdown.showing, .header-sub-menus .smooth-collapse.showing"
        )

        const ancestorMenus = new Set()
        if (currentMenu) {
            ancestorMenus.add(currentMenu)
            let parent = currentMenu.parentElement
            while (parent && parent !== document.body) {
                const parentMenu = parent.closest(
                    ".sub-menu-dropdown, .header-sub-menus .smooth-collapse"
                )
                if (parentMenu) {
                    ancestorMenus.add(parentMenu)
                    parent = parentMenu.parentElement
                } else {
                    parent = parent.parentElement
                }
            }
        }

        // Collapse all other menus
        expandedMenus.forEach(menu => {
            if (!ancestorMenus.has(menu)) {
                menu.classList.remove("showing")
                const toggleButtons = document.querySelectorAll(
                    `[href="#${menu.id}"]`
                )
                toggleButtons.forEach(button => {
                    button.setAttribute("aria-expanded", "false")
                })
            }
        })

        // Toggle current menu with animation
        if (currentMenu) {
            currentMenu.classList.add("smooth-collapse")

            if (isAlreadyOpen) {
                currentMenu.classList.remove("showing")
                currentButton.setAttribute("aria-expanded", "false")
            } else {
                currentMenu.classList.add("showing")
                currentButton.setAttribute("aria-expanded", "true")
            }
        }
    },
    async fetchMenuData() {
        try {
            const menuData = this.menuService.getApps()
            const menuIds = menuData.map(app => app.id)
            const result = await this.rpc("/get/menu_data", {
                menu_ids: menuIds,
            })
            for (const menu of menuData) {
                const targetElem = this.root.el?.querySelector(
                    `.primary-nav a.main_link[data-menu="${menu.id}"] .app_icon`
                )
                if (!targetElem) continue

                targetElem.innerHTML = ""
                const prRecord = result[menu.id]?.[0]
                if (!prRecord) continue

                menu.id = prRecord.id
                menu.use_icon = prRecord.use_icon
                menu.icon_class_name = prRecord.icon_class_name
                menu.icon_img = prRecord.icon_img

                let iconImage
                if (prRecord.use_icon) {
                    if (prRecord.icon_class_name) {
                        iconImage = `<span class="ri ${prRecord.icon_class_name}"/>`
                    } else if (prRecord.icon_img) {
                        iconImage = `<img class="img img-fluid" src="/web/image/ir.ui.menu/${prRecord.id}/icon_img" />`
                    } else if (prRecord.web_icon) {
                        const [iconPath, iconExt] =
                            prRecord.web_icon.split("/icon.")
                        if (iconExt === "svg") {
                            const webSvgIcon = prRecord.web_icon.replace(
                                ",",
                                "/"
                            )
                            iconImage = `<img class="img img-fluid" src="${webSvgIcon}" />`
                        } else {
                            iconImage = `<img class="img img-fluid" src="data:image/${iconExt};base64,${prRecord.web_icon_data}" />`
                        }
                    } else {
                        iconImage = `<img class="img img-fluid" src="/clarity_backend_theme_bits/static/img/logo.png" />`
                    }
                } else {
                    if (prRecord.icon_img) {
                        iconImage = `<img class="img img-fluid" src="/web/image/ir.ui.menu/${prRecord.id}/icon_img" />`
                    } else if (prRecord.web_icon) {
                        const [iconPath, iconExt] =
                            prRecord.web_icon.split("/icon.")
                        if (iconExt === "svg") {
                            const webSvgIcon = prRecord.web_icon.replace(
                                ",",
                                "/"
                            )
                            iconImage = `<img class="img img-fluid" src="${webSvgIcon}" />`
                        } else {
                            iconImage = `<img class="img img-fluid" src="data:image/${iconExt};base64,${prRecord.web_icon_data}" />`
                        }
                    } else {
                        iconImage = `<img class="img img-fluid" src="/clarity_backend_theme_bits/static/img/logo.png" />`
                    }
                }
                targetElem.innerHTML = iconImage
            }
        } catch (error) {
            console.error("Failed to fetch menu data:", error)
        }
    },

    BackMenuToggle(ev) {
        const parent = ev.currentTarget.parentElement
        if (parent) {
            parent.classList.remove("show")
        }
    },

    get currentMenuId() {
        const actionParams = window.location.hash
        const params = new URLSearchParams(actionParams.substring(1))
        return params.get("menu_id")
    },
})

patch(WebClient, {
    components: { ...WebClient.components, SidebarBottom },
    // components: { ...WebClient.components, SidebarBottom, Transition },
})
