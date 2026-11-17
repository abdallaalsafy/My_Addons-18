/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

/**
 * Registry contract of the unified dashboard (owned by this addon).
 *
 * Widget definition (registered by integration addons):
 *   key          unique key, e.g. "my_addon.kpis"           (required)
 *   addon        technical name of the registering addon              (required)
 *   section      section key; unknown keys fall back to "other"       (required)
 *   title        display name (translated with _t by the integration) (required)
 *   description  optional sub-title / tooltip
 *   component    OWL component rendering the payload (props: {data})  (required)
 *   model        server abstract model exposing get_widget_data()     (required)
 *   widget       server widget key (defaults to the part after "." in key)
 *   sequence     ordering inside the section (default 100)
 *   size         "sm" (1/3), "md" (1/2) or "lg" (full width)          (default "md")
 *   filters      array of shared filters the widget honours, e.g. ["date"]
 *
 * Authorization is enforced on the SERVER (see unified.dashboard.base); required groups
 * are declared in the integration's Python model, not trusted from the browser.
 */
export const widgetRegistry = registry.category("unified_dashboard.widgets");
export const sectionRegistry = registry.category("unified_dashboard.sections");

export const FALLBACK_SECTION = "other";
const SIZES = new Set(["sm", "md", "lg"]);

/**
 * Idempotent: registering the same key from the same addon again (asset reload, HMR)
 * replaces the previous definition. A key already owned by ANOTHER addon is rejected.
 */
export function registerDashboardWidget(def) {
    const required = ["key", "addon", "section", "title", "component", "model"];
    const missing = required.filter((name) => !def || !def[name]);
    if (missing.length) {
        console.error(`[unified_dashboard] widget not registered, missing: ${missing.join(", ")}`, def);
        return false;
    }
    const existing = widgetRegistry.contains(def.key) ? widgetRegistry.get(def.key) : null;
    if (existing && existing.addon !== def.addon) {
        console.warn(
            `[unified_dashboard] duplicate widget key "${def.key}" from "${def.addon}" ignored ` +
                `(already owned by "${existing.addon}")`
        );
        return false;
    }
    const entry = {
        description: "",
        sequence: 100,
        size: "md",
        filters: [],
        ...def,
        widget: def.widget || def.key.split(".").pop(),
    };
    if (!SIZES.has(entry.size)) {
        entry.size = "md";
    }
    widgetRegistry.add(entry.key, entry, { force: true, sequence: entry.sequence });
    return true;
}

export function registerDashboardSection(def) {
    if (!def || !def.key || !def.title) {
        console.error("[unified_dashboard] section not registered, key/title required", def);
        return false;
    }
    sectionRegistry.add(
        def.key,
        { sequence: 100, ...def },
        { force: true, sequence: def.sequence ?? 100 }
    );
    return true;
}

// The fallback section always exists so integrations never lose their widgets.
registerDashboardSection({ key: FALLBACK_SECTION, title: _t("Other"), sequence: 1000 });
