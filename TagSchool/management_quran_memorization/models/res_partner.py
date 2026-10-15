# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    # Memorization count for students
    memorization_count = fields.Integer(
        'Memorization Count',
        compute='_compute_memorization_count',
        help="Number of memorization records for this student (only shown for students)"
    )

    def _compute_memorization_count(self):
        """
        Compute the number of memorization records for this student (only for students)
        """
        for record in self:
            if record.is_student:
                # Count memorization records where this partner is the student
                memorizations = self.env['student.memorization'].search([('student_id', '=', record.id)])
                record.memorization_count = len(memorizations)
            else:
                record.memorization_count = 0

    def action_view_memorizations(self):
        """View memorizations of this student"""
        self.ensure_one()
        name = _('Memorizations of %s') % self.name
        domain = [('student_id', '=', self.id)]
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'student.memorization',
            'view_mode': 'list,form',
            'domain': domain,
            'context': { 'default_student_id': self.id, }
        }

    def action_create_memorization(self):
        """
        Open memorization registration form for the current student
        """
        self.ensure_one()
        
        # Check if the partner is a student
        if not self.is_student:
            raise ValidationError(_('This partner is not a student. Only students can have memorization records.'))
        
        # Check if student already has memorization for current month
        current_month = fields.Date.today().replace(day=1)
        existing_memorization = self.env['student.memorization'].search([
            ('student_id', '=', self.id),
            ('memorization_month', '>=', current_month)
        ], limit=1)
        if not existing_memorization:
            # Open new record
            return {
                'type': 'ir.actions.act_window',
                'name': _('Register Memorization'),
                'res_model': 'student.memorization',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_student_id': self.id,
                    'default_memorization_month': fields.Date.today(),
                }
            }
        else:
            raise UserError(_('This student already has memorization for current month.'))

