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
    UdTrendWidget,
} from "@unified_dashboard_core/js/generic_widgets";

const ADDON = "dashboard_quran_attendance";
const MODEL = "dashboard.quran.attendance";

registerDashboardSection({ key: "attendance", title: _t("Attendance"), sequence: 40 });

registerDashboardWidget({
    key: "quran_attendance.attendance_kpis",
    addon: ADDON,
    section: "attendance",
    title: _t("Attendance summary"),
    description: _t("Rates are based on the study days actually filled in."),
    component: UdKpiWidget,
    model: MODEL,
    sequence: 10,
    size: "lg",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_attendance.attendance_trend",
    addon: ADDON,
    section: "attendance",
    title: _t("Attendance trend"),
    component: UdTrendWidget,
    model: MODEL,
    sequence: 20,
    size: "md",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_attendance.attendance_classes",
    addon: ADDON,
    section: "attendance",
    title: _t("Classes with the highest absence"),
    description: _t("Top 10 classes by absence rate."),
    component: UdBarsWidget,
    model: MODEL,
    sequence: 30,
    size: "md",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_attendance.attendance_students",
    addon: ADDON,
    section: "attendance",
    title: _t("Students with the most absences"),
    component: UdTableWidget,
    model: MODEL,
    sequence: 40,
    size: "md",
    filters: ["date"],
});
