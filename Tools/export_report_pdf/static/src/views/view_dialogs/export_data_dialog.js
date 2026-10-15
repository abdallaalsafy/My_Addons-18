/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";

patch(ExportDataDialog.prototype, {
    setup() {
        super.setup();
        this.state.reportTitle = "";
        this.portrait = "portrait";
        this.landscape = 'landscape'
        this.state.reportOrientation = this.portrait;
        this.state.enableIndexing = false;
    },

    get isPdfFormat() {
        return this.availableFormats[this.state.selectedFormat]?.tag === 'pdf';
    },

    onToggleFieldSelection(fieldId, aggregateValue) {
        // Update the field object in exportList
        const field = this.state.exportList.find(f => f.id === fieldId);
        if (field) {
            field.aggregate = aggregateValue;
        }
    },

    async onSaveExportTemplate() {
        await super.onSaveExportTemplate();
        // Save the custom fields to the template
        await this.orm.write("ir.exports", [this.state.templateId], {
            report_title: this.state.reportTitle,
            is_landscape: this.state.reportOrientation === this.landscape,
            enable_indexing: this.state.enableIndexing,
        });

        // Update the field object in exportList
         const template = this.templates.find(t => t.id === this.state.templateId);
        if (template) {
            template.report_title = this.state.reportTitle;
            template.is_landscape = this.state.reportOrientation === this.landscape;
            template.enable_indexing = this.state.enableIndexing;
        }

        // Save the field selections
        const exportFields = await this.orm.searchRead(
            "ir.exports.line",
            [["export_id", "=", this.state.templateId]],
            ["id", "name"]
        );

        for (const field of this.state.exportList) {
            const exportField = exportFields.find(ef => ef.name === field.id);
            if (exportField) {
                await this.orm.write("ir.exports.line", [exportField.id], {
                    aggregate: field.aggregate || '',
                });
            }
        }
    },

    async loadExportList(value) {
        await super.loadExportList(value);
        if (value && value !== "new_template") {
            // Load the custom fields from the template
            const template = this.templates.find(t => t.id === Number(value));
            if (template) {
                this.state.reportTitle = template.report_title || "";
                this.state.reportOrientation = template.is_landscape?this.landscape:this.portrait;
                this.state.enableIndexing = template.enable_indexing || false;
            }

            //Load field selections
            const exportFields = await this.orm.searchRead(
                "ir.exports.line",
                [["export_id", "=", Number(value)]],
                ["name", "aggregate"]
            );

            for (const field of this.state.exportList) {
                const exportField = exportFields.find(ef => ef.name === field.id);
                if (exportField) {
                    field.aggregate = exportField.aggregate;
                }
            }
        } else {
                this.state.reportTitle = "";
                this.state.reportOrientation = this.portrait;
                this.state.enableIndexing = false;
                for (const field of this.state.exportList) {
                field.aggregate = '';
            }
            }
    },

    async onClickExportButton() {
        const format_tag = this.availableFormats[this.state.selectedFormat].tag
        if (format_tag === 'pdf'){
            if (!this.state.exportList.length) {
                return this.notification.add(_t("Please select fields to save export list..."), {
                    type: "danger",
                });
            }

            this.state.disabled = true;
            await this.props.download(
                this.state.exportList,
                this.state.isCompatible,
                format_tag,
                {'reportTitle':this.state.reportTitle,'is_landscape':this.state.reportOrientation === this.landscape,'enable_indexing':this.state.enableIndexing},
            );
            this.state.disabled = false;
        } else {
            await super.onClickExportButton();
        }

    }
});
