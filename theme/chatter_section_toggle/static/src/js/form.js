/** @odoo-module **/
import { patch } from "@web/core/utils/patch"
import { FormController } from "@web/views/form/form_controller"
import { useService } from "@web/core/utils/hooks"
import { onMounted } from "@odoo/owl"

patch(FormController.prototype, {
    setup() {
        super.setup()
        this.actionService = useService("action")
        onMounted(() => {
            setTimeout(() => this.injectOvnButton(), 100)
        })
    },

    injectOvnButton() {
        const formSheet = document.querySelector(".o_form_sheet_bg")
        if (!formSheet) {
            console.warn("❌ .o_form_sheet_bg not found")
            return
        }

        formSheet.parentNode.style.position = "relative"

        this.wrapper = document.createElement("div")
        this.wrapper.className = "custom-ovn-wrapper"

        // Default floating behavior (chatter hidden)
        Object.assign(this.wrapper.style, {
            position: "absolute",
            top: "10px",
            right: "10px",
            zIndex: "9999",
            display: "flex",
            gap: "5px",
        })

        this.ShowBtn = document.createElement("button")
        this.ShowBtn.className = "btn btn-show-ovn"
        this.ShowBtn.innerText = "<<<"
        this.ShowBtn.onclick = () => this.onShowButtonClick()

        this.HideBtn = document.createElement("button")
        this.HideBtn.className = "btn btn-hide-ovn"
        this.HideBtn.innerText = ">>>"
        this.HideBtn.onclick = () => this.onHideButtonClick()

        const ChatterContainer = document.querySelector(
            ".o-mail-ChatterContainer"
        )
        if (ChatterContainer) {
            // Hide chatter by default
            ChatterContainer.style.display = "none"
            formSheet.style.maxWidth = "none"

            this.ShowBtn.style.display = "block"
            this.HideBtn.style.display = "none"

            this.wrapper.appendChild(this.ShowBtn)
            this.wrapper.appendChild(this.HideBtn)

            formSheet.parentNode.appendChild(this.wrapper)
        }
    },

    // ⭐ When showing chatter
    onShowButtonClick() {
        const ChatterContainer = document.querySelector(
            ".o-mail-ChatterContainer"
        )
        const formSheet = document.querySelector(".o_form_sheet_bg")

        ChatterContainer.style.display = "block"
        formSheet.style.maxWidth = "1534px"

        this.ShowBtn.style.display = "none"
        this.HideBtn.style.display = "block"

        // ⭐ Move button to inside the chatter container
        Object.assign(this.wrapper.style, {
            position: "relative",
            top: "0px",
            right: "0px",
            marginBottom: "8px",
        })

        ChatterContainer.prepend(this.wrapper)
    },

    // ⭐ When hiding chatter
    onHideButtonClick() {
        const ChatterContainer = document.querySelector(
            ".o-mail-ChatterContainer"
        )
        const formSheet = document.querySelector(".o_form_sheet_bg")

        ChatterContainer.style.display = "none"
        formSheet.style.maxWidth = "none"

        this.HideBtn.style.display = "none"
        this.ShowBtn.style.display = "block"

        // ⭐ Move button back to the top-right of form
        Object.assign(this.wrapper.style, {
            position: "absolute",
            top: "10px",
            right: "10px",
            marginBottom: "0px",
        })

        formSheet.parentNode.appendChild(this.wrapper)
    },
})
