# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.export import Export


class ExportPDF(Export):
    @http.route('/web/export/formats', type='json', auth='user', readonly=True)
    def formats(self):
        values = super().formats()
        values.append({
            'tag': 'pdf',
            'label': 'PDF'
        })
        return values

