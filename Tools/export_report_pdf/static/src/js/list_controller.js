/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";


patch(ListController.prototype, {
    async onPrintPDF(fields,report_info) {
        const model = this.model.root.resModel;
        const domain = this.model.root.domain;
        const groupby = this.model.root.groupBy;
        const context = this.props.context;
        const resIds = this.model.root.selection.map((r) => r.resId);

        const action = {
            type: "ir.actions.report",
            report_name: "export_report_pdf.report_list_view",
            report_type: "qweb-pdf",
            context: {
                    ...context,
                    landscape: report_info['is_landscape'],
                },
            data: {
                model: model,
                domain: domain,
                fields: fields,
                groupby: groupby,
                res_ids: resIds,
                report_info:report_info,
            },
        };

        return this.actionService.doAction(action);
    },
    async downloadExport(fields, import_compat, format,report_info) {
        if (format === 'pdf'){
            const exportedFields = fields.map((field) => ({
                name: field.name || field.id,
                label: field.label || field.string,
                store: field.store,
                type: field.field_type || field.type,
                aggregate: field.aggregate || '',
            }));
            await this.onPrintPDF(exportedFields,report_info);
        } else {
            await super.downloadExport(fields, import_compat, format);
        }

    },
});
