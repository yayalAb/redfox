/** @odoo-module **/

/**
 * The SPA router listens on window for clicks (see web/static/src/core/browser/router.js).
 * Links whose resolved URL look like /odoo/web/content/... are mis-parsed as action path
 * "content". Stopping propagation at document (bubble phase) runs before the event
 * reaches window, so the router never intercepts legitimate binary/image downloads.
 *
 * This complements many2many_binary_patch (field-specific) and fixes chatter / any
 * other /web/content or /web/image link under /odoo.
 */
function registerDocumentClickStopper() {
    document.addEventListener(
        "click",
        (ev) => {
            if (!window.location.pathname.startsWith("/odoo")) {
                return;
            }
            const a = ev.target?.closest?.("a[href]");
            if (!a) {
                return;
            }
            const href = (a.getAttribute("href") || "").toLowerCase();
            if (!href.includes("/web/content") && !href.includes("/web/image")) {
                return;
            }
            ev.stopPropagation();
        },
        false
    );
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", registerDocumentClickStopper);
} else {
    registerDocumentClickStopper();
}
