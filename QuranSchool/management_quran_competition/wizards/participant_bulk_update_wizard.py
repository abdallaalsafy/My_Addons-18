# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ParticipantBulkUpdateWizard(models.TransientModel):
    _name = 'participant.bulk.update.wizard'
    _description = 'Bulk Update Participant Wizard'

    field_name = fields.Selection([
        ('state', 'State'),
        ('status', 'Status'),
    ], string='Field to Update', required=True, default='state')

    state_value = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('disqualified', 'Disqualified'),
        ('withdrawn', 'Withdrawn'),
    ], string='State')

    status_value = fields.Selection([
        ('superior', 'Superior'),
        ('successful', 'Successful'),
        ('acceptable', 'Acceptable'),
        ('precipitate', 'Precipitate'),
    ], string='Status')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['field_name'] = self.env.context.get('default_field_name') or res.get('field_name') or 'state'
        return res

    @api.onchange('field_name')
    def _onchange_field_name(self):
        if self.field_name != 'state':
            self.state_value = False
        if self.field_name != 'status':
            self.status_value = False

    def action_apply(self):
        active_ids = self.env.context.get('active_ids') or []
        if not active_ids:
            raise ValidationError(_('Please select at least one participant.'))

        records = self.env['quran.competition.participant'].browse(active_ids)
        if not records:
            raise ValidationError(_('The selected participants could not be found.'))

        if self.field_name == 'state':
            if not self.state_value:
                raise ValidationError(_('Please choose a state value to apply.'))
            values = {'state': self.state_value}
        elif self.field_name == 'status':
            if not self.status_value:
                raise ValidationError(_('Please choose a status value to apply.'))
            values = {'status': self.status_value}
        else:
            raise ValidationError(_('Invalid field selected.'))

        records.write(values)
        return {'type': 'ir.actions.act_window_close'}
