# -*- coding: utf-8 -*-
from odoo import fields, models


class IrExports(models.Model):
    _inherit = "ir.exports"

    report_title = fields.Char(string='عنوان التقرير', help='Title for the exported report')
    is_landscape = fields.Boolean(default=False)
    enable_indexing = fields.Boolean(string='الفهرسة', default=False)


class IrExportsLine(models.Model):
    _inherit = 'ir.exports.line'

    aggregate = fields.Char(string='Aggregate')
