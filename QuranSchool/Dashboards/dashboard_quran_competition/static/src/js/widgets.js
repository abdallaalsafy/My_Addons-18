/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import {
    registerDashboardSection,
    registerDashboardWidget,
} from "@unified_dashboard_core/js/widget_registry";
import {
    UdBarsWidget,
    UdKpiWidget,
    UdTableWidget,
} from "@unified_dashboard_core/js/generic_widgets";

const ADDON = "dashboard_quran_competition";
const MODEL = "dashboard.quran.competition";

registerDashboardSection({ key: "competitions", title: _t("Competitions"), sequence: 50 });

registerDashboardWidget({
    key: "quran_competition.competition_overview",
    addon: ADDON,
    section: "competitions",
    title: _t("Competitions overview"),
    description: _t("Competitions dated within the period, their participants and prizes."),
    component: UdKpiWidget,
    model: MODEL,
    sequence: 10,
    size: "lg",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_competition.competition_upcoming",
    addon: ADDON,
    section: "competitions",
    title: _t("Upcoming competitions"),
    description: _t("Next open competitions from today."),
    component: UdTableWidget,
    model: MODEL,
    sequence: 20,
    size: "md",
});

registerDashboardWidget({
    key: "quran_competition.competition_results",
    addon: ADDON,
    section: "competitions",
    title: _t("Results distribution"),
    description: _t("Evaluated participants by result (disqualified and withdrawn excluded)."),
    component: UdBarsWidget,
    model: MODEL,
    sequence: 30,
    size: "md",
    filters: ["date"],
});
