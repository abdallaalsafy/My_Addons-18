/** @odoo-module **/
import { user } from "@web/core/user";
// import { DateTime } from "luxon";
const { DateTime } = luxon;

function locale() {
    // Odoo langs look like "ar_001" / "en_US"; Intl wants BCP-47.
    return (user.lang || "en-US").replace("_", "-");
}

export function formatNumber(value, digits = 0) {
    if (value === null || value === undefined) {
        return "—";
    }
    try {
        return new Intl.NumberFormat(locale(), {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
        }).format(value);
    } catch {
        return String(value);
    }
}

export function formatMonetary(value, currency) {
    if (value === null || value === undefined) {
        return "—";
    }
    try {
        return new Intl.NumberFormat(locale(), {
            style: "currency",
            currency: currency || "USD",
        }).format(value);
    } catch {
        return `${formatNumber(value, 2)} ${currency || ""}`.trim();
    }
}

export function formatDate(iso) {
    if (!iso) {
        return "";
    }
    const dt = DateTime.fromISO(iso);
    return dt.isValid ? dt.toLocaleString(DateTime.DATE_MED, { locale: locale() }) : iso;
}

/**
 * format: "integer" | "decimal" | "percent" | "monetary" | "date" | "text"
 * A null/undefined value is shown as an em dash: "no data" is never shown as 0.
 */
export function formatValue(value, format = "integer", currency = null) {
    if (value === null || value === undefined || value === "") {
        return "—";
    }
    switch (format) {
        case "percent":
            return `${formatNumber(value, 1)}%`;
        case "decimal":
            return formatNumber(value, 2);
        case "monetary":
            return formatMonetary(value, currency);
        case "date":
            return formatDate(value);
        case "text":
            return String(value);
        default:
            return formatNumber(value, 0);
    }
}
