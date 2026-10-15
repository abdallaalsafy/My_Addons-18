# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

class ReportListView(models.AbstractModel):
    _name = 'report.export_report_pdf.report_list_view'
    _description = 'List View PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data or not data.get('model'):
            raise UserError(_("No data provided to generate the report."))

        res_model = data.get('model')
        domain = data.get('domain', [])
        fields = data.get('fields', [])
        groupby = data.get('groupby', [])
        title = data.get('report_info', {}).get('reportTitle', '')
        enable_indexing = data.get('report_info', {}).get('enable_indexing', False),
        res_ids = data.get('res_ids', [])

        Model = self.env[res_model]

        # Use Model Name (e.g. Sales Order) instead of technical name (sale.order)
        if not title:
            title = Model._description

        field_label = [f['label'] for f in fields]
        field_names = [f['name'] for f in fields]
        fields_type = [f['type'] for f in fields]

        # Prepare aggregate fields for read_group
        # aggregates =  ['fld_name:sum', 'fld_name:max', ......]
        aggregates = [f"{f['name']}:{f['aggregate']}" for f in fields if f['aggregate']]
        aggregates_stored, aggregates_non_stored = self._sperate_aggregates(fields, Model)

        rows = []
        if groupby:
            # Grouped Export Logic
            domain_to_use = [('id', 'in', res_ids)] if res_ids else domain
            rows = self._get_grouped_rows(Model, domain_to_use, field_names, fields_type, groupby, aggregates,aggregates_stored, aggregates_non_stored, fields)
        else:
            # Flat Export Logic
            records = Model.browse(res_ids).exists() if res_ids else Model.search(domain)
            # export_result = {'datas': [ [value1, value2, ...],[],...] }
            export_result = records.with_context(import_compat=False).export_data(field_names)
            raw_rows = export_result.get('datas', [])
            for raw_row in raw_rows:
                rows.append({'type': 'data', 'values': self._format_row(raw_row, fields_type)})

        # Calculate Grand Totals
        grand_totals = []#['Aggregates', 'sum:value', 'max:value','',......]
        total_data = []
        total_data_non_stored = {}
        has_totals = False
        if aggregates:
            total_domain = [('id', 'in', res_ids)] if res_ids else domain
            # total_data:
            # [
            # {
            #     '__count': 2,
            #     'fld_name1': 150.0,
            #     'fld_name2': 0.0,
            #     ..........,
            #     '__domain': [('id', 'in', [2, 1])]
            # },
            # ]
            if aggregates_stored:
                total_data = Model.read_group(total_domain, aggregates_stored, [])
            if aggregates_non_stored:
                total_data_non_stored = self._aggregates_non_store_values(aggregates_non_stored,Model,total_domain)

            if total_data:
                total_data[0].update(total_data_non_stored)
            else:
                total_data = [total_data_non_stored]

            if total_data:
                res = total_data[0]
                
                for i in range(0, len(field_names)):
                    f_name = field_names[i]
                    val = res.get(f_name)
                    if f_name in res:
                        aggregate_type = next((a.split(':')[1] for a in aggregates if a.startswith(f"{f_name}:")), '')
                        grand_totals.append(f"{aggregate_type}: {self._format_value(val, fields_type[i])}")
                        has_totals = True
                    else:
                        if i == 0 :
                            grand_totals.append(_("Aggregates"))  # Label for first column
                        else:
                            grand_totals.append('')
        return {
            'doc_ids': docids,
            'doc_model': res_model,
            'headers': field_label,
            'rows': rows,
            'title': title,
            'grand_totals': grand_totals if has_totals else None,
            'enable_indexing': enable_indexing,
        }

    def _sperate_aggregates(self,fields,Model):
        # Prepare aggregate fields for read_group
        # Separate stored and non-stored fields
        aggregates_stored = []
        aggregates_non_stored = []
        for f in fields:
            f_name = f['name']
            f_aggregate = f['aggregate']
            if f_aggregate:
                field = Model._fields.get(f_name)
                if field and field.store:
                    aggregates_stored.append(f"{f_name}:{f_aggregate}")
                else:
                    aggregates_non_stored.append(f"{f_name}:{f_aggregate}")
        return aggregates_stored,aggregates_non_stored

    def _aggregates_non_store_values(self,aggregates_non_stored,Model,total_domain):
        # Calculate non-stored field aggregates manually
        non_stored_totals = {}
        if aggregates_non_stored:
            records = Model.search(total_domain)
            for agg in aggregates_non_stored:
                f_name = agg.split(':')[0]
                agg_type = agg.split(':')[1]
                values = records.mapped(f_name)

                if agg_type == 'sum':
                    non_stored_totals[f_name] = sum(values)
                elif agg_type == 'avg':
                    non_stored_totals[f_name] = sum(values) / len(values)
                elif agg_type == 'max':
                    non_stored_totals[f_name] = max(values)
                elif agg_type == 'min':
                    non_stored_totals[f_name] = min(values)
                elif agg_type == 'count':
                    non_stored_totals[f_name] = len(values)
        return non_stored_totals

    def _get_grouped_rows(self, Model, domain, field_names, fields_type, groupby, aggregates,aggregates_stored, aggregates_non_stored, fields, depth=0):
        rows = []
        if not groupby:
            # Reach the leaf, fetch records
            records = Model.search(domain)
            export_result = records.with_context(import_compat=False).export_data(field_names)
            for raw_row in export_result.get('datas', []):
                rows.append({'type': 'data', 'values': self._format_row(raw_row, fields_type)})
            return rows

        current_groupby = groupby[0]
        # read_group to get sub-groups
        fields_to_read = ['__count'] + aggregates_stored
        groups_data = Model.read_group(domain, fields_to_read, [current_groupby], lazy=True)
        
        count_key = f"{current_groupby.split(':')[0]}_count"

        for group in groups_data:
            # Calculate non-stored aggregates for this group manually
            child_domain = group.get('__domain', [])
            non_stored_aggregates = self._aggregates_non_store_values(aggregates_non_stored, Model, child_domain)
            group.update(non_stored_aggregates)

            # Build group header
            group_name = self._format_group_name(Model, current_groupby, group)
            count = group.get(count_key) or group.get('__count') or 0
            header_label = f"{'    ' * depth}{group_name} ({count})"

            # Group headers show aggregates in their respective columns
            header_values = [header_label]
            for i in range(1, len(field_names)):
                f_name = field_names[i]
                val = group.get(f_name)
                is_aggregated = any(a.startswith(f"{f_name}:") for a in aggregates)
                if val is not None and is_aggregated:
                    aggregate_type = next((a.split(':')[1] for a in aggregates if a.startswith(f"{f_name}:")), '')
                    header_values.append(f"{aggregate_type}: {self._format_value(val, fields_type[i])}")
                else:
                    header_values.append('')
            
            rows.append({'type': 'header', 'values': header_values, 'depth': depth})

            rows.extend(self._get_grouped_rows(Model, child_domain, field_names, fields_type, groupby[1:], aggregates,aggregates_stored, aggregates_non_stored, fields, depth + 1))
            
        return rows

    def _format_group_name(self, Model, groupby_field, group_data):
        field_name = groupby_field.split(':')[0]
        field = Model._fields.get(field_name)
        value = group_data.get(groupby_field)
        
        if value is False or value is None:
            return _("Undefined")
            
        if field.type == 'many2one':
            return value[1] if isinstance(value, (list, tuple)) else value
        elif field.type == 'selection':
            return dict(field.selection).get(value, value)
        elif field.type == 'boolean':
            return _('Yes') if value else _('No')
            
        return str(value)

    def _format_row(self, raw_row, fields_type):
        formatted_row = []
        for i, value in enumerate(raw_row):
            formatted_row.append(self._format_value(value, fields_type[i]))
        return formatted_row

    def _format_value(self, value, field_type):
        if field_type in ['float', 'monetary'] and isinstance(value, (int, float)):
            return formatLang(self.env, value)
        elif field_type == 'integer' and isinstance(value, int):
            return formatLang(self.env, value, digits=0)
        elif value is False or value is None:
            return ''
        return str(value)
