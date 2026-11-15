# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'


    memorization_ids = fields.One2many(
        'student.memorization',
        'student_id',
        string='Memorizations',
        help="Memorization records for this student (only shown for students)"
    )

    # Memorization count for students
    memorization_count = fields.Integer(
        'Memorization Count',
        compute='_compute_memorization_count',
        help="Number of memorization records for this student (only shown for students)"
    )

# =============================== Compute Functions =====================================
    def _compute_memorization_count(self):
        """Compute the number of memorization records for this student (only for students)"""
        for record in self:
            if record.is_student:
                record.memorization_count = len(record.memorization_ids)
            else:
                record.memorization_count = 0

# =============================== Action Functions =====================================   
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

#============================== Helper Functions =====================================
    def validate_student_for_memorization(self, month=None, office=None):
        """Check student status before allowing memorization"""
        self.ensure_one()

        self.validate_status_of_student()
        
        office = office or self.office_id

        # There also _sql_constraints in student.memorization to ensure uniqueness, but we check here for a more user-friendly error message
        month = month or fields.Date.today()
        existing_memorization = self.memorization_ids.filtered(
                    lambda m: m.memorization_month.replace(day=1) == month.replace(day=1) and m.office_id == office
                )
        if existing_memorization:
            raise ValidationError(_('This student already has memorization for month (%s) and office (%s).') % (month, office.name))
        if not office:
            raise ValidationError(
                _('Cannot create memorization for student (%s) without office.') % self.name)

