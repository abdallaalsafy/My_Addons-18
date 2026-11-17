/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { formatValue, formatNumber } from "./formatters";

/**
 * Generic, data-driven widget components. Integration addons register these as the
 * `component` of their widgets and only supply server data; this keeps every widget
 * visually consistent.
 *
 * Optional `drill` objects (on tiles / bar items / table rows) open the matching
 * records: { name, res_model, domain } for a list or { name, res_model, res_id } for a form.
 * They run through the normal action service, so the user's ACLs apply.
 */
function useDrill() {
    const action = useService("action");
    return (drill) => {
        if (!drill || !drill.res_model) {
            return;
        }
        if (drill.res_id) {
            return action.doAction({
                type: "ir.actions.act_window",
                name: drill.name || drill.res_model,
                res_model: drill.res_model,
                res_id: drill.res_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
        return action.doAction({
            type: "ir.actions.act_window",
            name: drill.name || drill.res_model,
            res_model: drill.res_model,
            domain: drill.domain || [],
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
        });
    };
}

/** data: { tiles: [{label, value, format, currency, hint, tone, drill}] } */
export class UdKpiWidget extends Component {
    static template = "unified_dashboard_core.KpiWidget";
    static props = { data: Object };
    setup() {
        this.drill = useDrill();
    }
    display(tile) {
        return formatValue(tile.value, tile.format || "integer", tile.currency);
    }
    toneClass(tile) {
        return `ud-tone-${tile.tone || "neutral"}`;
    }
}

/**
 * data: { format, items: [{label, value, secondary_text, drill}] }
 * Bars are scaled to the largest value (or 100 for percentages).
 */
export class UdBarsWidget extends Component {
    static template = "unified_dashboard_core.BarsWidget";
    static props = { data: Object };
    setup() {
        this.drill = useDrill();
    }
    get maxValue() {
        if (this.props.data.format === "percent") {
            return 100;
        }
        return Math.max(1, ...this.props.data.items.map((item) => item.value || 0));
    }
    width(item) {
        return Math.max(0, Math.min(100, ((item.value || 0) * 100) / this.maxValue));
    }
    display(item) {
        return formatValue(item.value, this.props.data.format || "integer");
    }
}

/** data: { columns: [{key, label, format, align}], rows: [{...cells, drill}], footer } */
export class UdTableWidget extends Component {
    static template = "unified_dashboard_core.TableWidget";
    static props = { data: Object };
    setup() {
        this.drill = useDrill();
    }
    cell(row, column) {
        const value = row[column.key];
        const currency = column.currency_key ? row[column.currency_key] : null;
        return formatValue(value, column.format || "text", currency);
    }
}

const COLUMN_W = 600;
const COLUMN_H = 220;
const PAD = { top: 18, right: 12, bottom: 28, left: 44 };

/**
 * data: { format, series: [{name, points: [{label, value}]}] }   (value may be null)
 * Grouped columns; at most 3 series are drawn.
 */
export class UdTrendWidget extends Component {
    static template = "unified_dashboard_core.TrendWidget";
    static props = { data: Object };
    get series() {
        return this.props.data.series.slice(0, 3);
    }
    get labels() {
        return this.series[0] ? this.series[0].points.map((p) => p.label) : [];
    }
    get maxValue() {
        if (this.props.data.format === "percent") {
            return 100;
        }
        const values = this.series.flatMap((s) => s.points.map((p) => p.value || 0));
        const max = Math.max(...values, 0);
        return max > 0 ? max * 1.1 : 1;
    }
    get viewBox() {
        return `0 0 ${COLUMN_W} ${COLUMN_H}`;
    }
    get plotHeight() {
        return COLUMN_H - PAD.top - PAD.bottom;
    }
    get gridLines() {
        return [0, 0.5, 1].map((ratio) => ({
            y: PAD.top + this.plotHeight * (1 - ratio),
            label: formatNumber(this.maxValue * ratio, 0),
        }));
    }
    get bars() {
        const n = this.labels.length || 1;
        const groupW = (COLUMN_W - PAD.left - PAD.right) / n;
        const seriesCount = this.series.length || 1;
        const barW = Math.min(36, (groupW * 0.7) / seriesCount);
        const bars = [];
        this.series.forEach((serie, si) => {
            serie.points.forEach((point, i) => {
                if (point.value === null || point.value === undefined) {
                    return;
                }
                const h = Math.max(1, (point.value / this.maxValue) * this.plotHeight);
                const groupStart = PAD.left + groupW * i + (groupW - barW * seriesCount) / 2;
                bars.push({
                    key: `${si}-${i}`,
                    cls: `ud-s${si}`,
                    x: groupStart + barW * si,
                    y: PAD.top + this.plotHeight - h,
                    w: barW,
                    h,
                    text: formatValue(point.value, this.props.data.format || "integer"),
                    tip: `${serie.name} — ${point.label}: ${formatValue(
                        point.value,
                        this.props.data.format || "integer"
                    )}`,
                    showLabel: n <= 8 && seriesCount === 1,
                });
            });
        });
        return bars;
    }
    get xLabels() {
        const n = this.labels.length || 1;
        const groupW = (COLUMN_W - PAD.left - PAD.right) / n;
        return this.labels.map((label, i) => ({
            key: i,
            label,
            x: PAD.left + groupW * i + groupW / 2,
            y: COLUMN_H - 8,
        }));
    }
    get pad() {
        return PAD;
    }
    get width() {
        return COLUMN_W;
    }
}
