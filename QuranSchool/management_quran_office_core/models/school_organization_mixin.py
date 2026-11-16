# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolOrganizationMixin(models.AbstractModel):
    _name = 'school.organization.mixin'
    _description = 'School Organization Mixin'

    office_id = fields.Many2one(
        'quran.office.office',
        'Office',
        help="Office this record belongs to"
    )
    class_id = fields.Many2one(
        'quran.office.class',
        'Class',
        domain="[('office_id', '=?', office_id)]",
        help="Class this record belongs to"
    )
    teacher_id = fields.Many2one(
        'res.partner',
        'Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Teacher or memorizer for this record"
    )


    @api.onchange('office_id')
    def _onchange_office_id(self):
        """Clear class_id and teacher_id when office changes to ensure proper filtering."""
        if (self.office_id and self.office_id != self.class_id.office_id) or not self.office_id:
            self.class_id = False

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """Auto-fill teacher_id when class is selected."""
        if self.class_id:
            self.office_id = self.class_id.office_id
        if self.class_id and self.class_id.teacher_id:
            self.teacher_id = self.class_id.teacher_id

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        if self.teacher_id and not self.class_id:
            self.class_id = self.teacher_id.class_ids[:1]


    @api.constrains('office_id', 'class_id')
    def _check_class_belongs_to_office(self):
        for rec in self:
            if rec.class_id and rec.office_id and rec.class_id.office_id != rec.office_id:
                raise ValidationError(_('The selected class does not belong to the selected office.'))