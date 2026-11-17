/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import {
    registerDashboardSection,
    registerDashboardWidget,
} from "@unified_dashboard_core/js/widget_registry";
import {
    UdBarsWidget,
    UdKpiWidget,
    UdTrendWidget,
} from "@unified_dashboard_core/js/generic_widgets";

const ADDON = "dashboard_quran_memorization";
const MODEL = "dashboard.quran.memorization";

registerDashboardSection({ key: "memorization", title: _t("Memorization"), sequence: 30 });

registerDashboardWidget({
    key: "quran_memorization.memorization_kpis",
    addon: ADDON,
    section: "memorization",
    title: _t("Follow-up summary"),
    description: _t("Monthly memorization records, grades and students not yet followed."),
    component: UdKpiWidget,
    model: MODEL,
    sequence: 10,
    size: "lg",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_memorization.memorization_trend",
    addon: ADDON,
    section: "memorization",
    title: _t("Grades trend"),
    component: UdTrendWidget,
    model: MODEL,
    sequence: 20,
    size: "md",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_memorization.memorization_by_teacher",
    addon: ADDON,
    section: "memorization",
    title: _t("Records by teacher"),
    description: _t("Top 10 teachers by number of records, with their average grade."),
    component: UdBarsWidget,
    model: MODEL,
    sequence: 30,
    size: "md",
    filters: ["date"],
});
