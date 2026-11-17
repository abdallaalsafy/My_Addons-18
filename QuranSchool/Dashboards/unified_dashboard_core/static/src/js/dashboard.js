/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { DashboardWidgetCard } from "./widget_card";
import { FALLBACK_SECTION, sectionRegistry, widgetRegistry } from "./widget_registry";


const PRESETS = [
    { key: "this_month", label: _t("This month") },
    { key: "last_month", label: _t("Last month") },
    { key: "last_3_months", label: _t("Last 3 months") },
    { key: "this_year", label: _t("This year") },
    { key: "custom", label: _t("Custom range") },
];

/** The single central dashboard (one client action, one menu). */
export class UnifiedDashboard extends Component {
    static template = "unified_dashboard_core.Dashboard";
    static components = { DashboardWidgetCard };
    static props = { "*": true };

    setup() {
        this.presets = PRESETS;
        this.state = useState({
            preset: "this_month",
            dateFrom: "",
            dateTo: "",
            customError: "",
            refreshKey: 0,
            denied: {},
        });
        // Applied filters: only changes when the selection is valid (avoids half-typed ranges).
        this.filters = useState({ preset: "this_month", date_from: "", date_to: "" });
    }

    // ---- registry -> sections --------------------------------------------------------
    get sections() {
        const knownSections = new Map(
            sectionRegistry
                .getAll()
                .map((section) => [section.key, { ...section, widgets: [] }])
        );
        const fallback = knownSections.get(FALLBACK_SECTION);
        for (const widget of widgetRegistry.getAll()) {
            const target = knownSections.get(widget.section) || fallback;
            target.widgets.push(widget);
        }
        return [...knownSections.values()]
            .map((section) => ({
                ...section,
                widgets: section.widgets
                    .filter((widget) => !this.state.denied[widget.key])
                    .sort((a, b) => a.sequence - b.sequence),
            }))
            .filter((section) => section.widgets.length)
            .sort((a, b) => a.sequence - b.sequence);
    }

    get totalWidgets() {
        return widgetRegistry.getAll().length;
    }

    get deniedCount() {
        return Object.keys(this.state.denied).length;
    }

    get allDenied() {
        return this.totalWidgets > 0 && this.deniedCount === this.totalWidgets;
    }

    // ---- filters -----------------------------------------------------------------------
    onPresetChange(ev) {
        this.state.preset = ev.target.value;
        this.state.customError = "";
        if (this.state.preset !== "custom") {
            this.filters.preset = this.state.preset;
            this.filters.date_from = "";
            this.filters.date_to = "";
        } else {
            this.applyCustom();
        }
    }

    onDateChange(field, ev) {
        this.state[field] = ev.target.value;
        this.applyCustom();
    }

    applyCustom() {
        const { dateFrom, dateTo } = this.state;
        if (!dateFrom || !dateTo) {
            this.state.customError = "";
            return;
        }
        if (dateFrom > dateTo) {
            this.state.customError = _t("The start date must not be after the end date.");
            return;
        }
        this.state.customError = "";
        this.filters.preset = "custom";
        this.filters.date_from = dateFrom;
        this.filters.date_to = dateTo;
    }

    refresh() {
        this.state.refreshKey++;
    }

    onWidgetDenied(key) {
        // Reassign (not mutate in place) so OWL re-renders the sections.
        this.state.denied = { ...this.state.denied, [key]: true };
    }
}

registry.category("actions").add("unified_dashboard.main", UnifiedDashboard, { force: true });
