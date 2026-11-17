/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import {
    registerDashboardSection,
    registerDashboardWidget,
} from "@unified_dashboard_core/js/widget_registry";
import {
    UdKpiWidget,
    UdTableWidget,
    UdTrendWidget,
} from "@unified_dashboard_core/js/generic_widgets";

const ADDON = "dashboard_quran_subscription";
const MODEL = "dashboard.quran.subscription";

registerDashboardSection({ key: "finance", title: _t("Subscriptions"), sequence: 20 });

registerDashboardWidget({
    key: "quran_subscription.subscription_kpis",
    addon: ADDON,
    section: "finance",
    title: _t("Collection summary"),
    description: _t("Expected vs collected amounts per currency, plus students not yet billed."),
    component: UdKpiWidget,
    model: MODEL,
    sequence: 10,
    size: "lg",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_subscription.subscription_trend",
    addon: ADDON,
    section: "finance",
    title: _t("Collections trend"),
    component: UdTrendWidget,
    model: MODEL,
    sequence: 20,
    size: "md",
    filters: ["date"],
});

registerDashboardWidget({
    key: "quran_subscription.subscription_outstanding",
    addon: ADDON,
    section: "finance",
    title: _t("Largest outstanding balances"),
    component: UdTableWidget,
    model: MODEL,
    sequence: 30,
    size: "md",
    filters: ["date"],
});
