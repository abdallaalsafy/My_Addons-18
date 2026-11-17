/** @odoo-module **/
import { Component, useEffect, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { formatDate } from "./formatters";

/**
 * One card per registered widget. Each card loads its own data, so a failing widget only
 * affects itself. Separate states: loading, error, denied (no access), empty, ready.
 */
export class DashboardWidgetCard extends Component {
    static template = "unified_dashboard_core.WidgetCard";
    static props = {
        widget: Object,
        preset: String,
        dateFrom: String,
        dateTo: String,
        refreshKey: Number,
        onDenied: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({ status: "loading", data: null, reloading: false });
        this.requestId = 0;
        useEffect(
            () => {
                this.load();
            },
            () => [
                this.props.preset,
                this.props.dateFrom,
                this.props.dateTo,
                this.props.refreshKey,
            ]
        );
    }

    get supportsDate() {
        return (this.props.widget.filters || []).includes("date");
    }

    get periodText() {
        const period = this.state.data && this.state.data.period;
        if (!this.supportsDate || !period) {
            return "";
        }
        return `${formatDate(period.from)} – ${formatDate(period.to)}`;
    }

    async load() {
        const requestId = ++this.requestId;
        const widget = this.props.widget;
        if (this.state.data) {
            this.state.reloading = true;
        } else {
            this.state.status = "loading";
        }
        // Only send the shared filters this widget declares it honours.
        const filters = this.supportsDate
            ? {
                  preset: this.props.preset,
                  date_from: this.props.dateFrom || false,
                  date_to: this.props.dateTo || false,
              }
            : {};
        try {
            const data = await this.orm.call(widget.model, "get_widget_data", [], {
                widget_key: widget.widget,
                filters,
            });
            if (requestId !== this.requestId) {
                return; // a newer request superseded this one
            }
            this.state.data = data;
            this.state.status = data.empty ? "empty" : "ready";
        } catch (error) {
            if (requestId !== this.requestId) {
                return;
            }
            const name = (error && ((error.data && error.data.name) || error.exceptionName)) || "";
            if (String(name).includes("AccessError")) {
                this.state.status = "denied";
                this.props.onDenied(widget.key);
            } else {
                this.state.status = "error";
            }
        } finally {
            if (requestId === this.requestId) {
                this.state.reloading = false;
            }
        }
    }
}
