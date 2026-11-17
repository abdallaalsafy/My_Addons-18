/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import {
    registerDashboardSection,
    registerDashboardWidget,
} from "@unified_dashboard_core/js/widget_registry";
import { UdBarsWidget, UdKpiWidget } from "@unified_dashboard_core/js/generic_widgets";

const ADDON = "dashboard_quran_office_core";
const MODEL = "dashboard.quran.office";

registerDashboardSection({ key: "students", title: _t("Students & Classes"), sequence: 10 });

registerDashboardWidget({
    key: "quran_office.students_overview",
    addon: ADDON,
    section: "students",
    title: _t("Overview"),
    description: _t("Current number of active students, teachers, offices and classes."),
    component: UdKpiWidget,
    model: MODEL,
    sequence: 10,
    size: "lg",
});

registerDashboardWidget({
    key: "quran_office.students_by_office",
    addon: ADDON,
    section: "students",
    title: _t("Students by office"),
    description: _t("Top 10 offices by number of active students."),
    component: UdBarsWidget,
    model: MODEL,
    sequence: 20,
    size: "md",
});

registerDashboardWidget({
    key: "quran_office.students_levels",
    addon: ADDON,
    section: "students",
    title: _t("Memorization levels"),
    description: _t("Active students grouped by memorized amount (Juz')."),
    component: UdBarsWidget,
    model: MODEL,
    sequence: 30,
    size: "md",
});

registerDashboardWidget({
    key: "quran_office.data_gaps",
    addon: ADDON,
    section: "students",
    title: _t("Data to complete"),
    description: _t("Records missing an office, class, teacher or status. Click to open them."),
    component: UdKpiWidget,
    model: MODEL,
    sequence: 40,
    size: "lg",
});
