# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError


class UpdatepersonDataWizard(models.TransientModel):
    _name = 'update.person.data.wizard'
    _inherit = ['school.organization.mixin']
    _description = 'Update person Data Wizard'

    _MODE_SELECTION = [
        ('update', 'Update'),
        ('clear', 'Clear'),
    ]

    mode_area = fields.Selection(_MODE_SELECTION, string='Mode Area',help="Update selected fields or clear existing data")
    mode_tags = fields.Selection(_MODE_SELECTION, string='Mode Tags',help="Update selected fields or clear existing data")
    mode_father = fields.Selection(_MODE_SELECTION, string='Mode Fathers',help="Update selected fields or clear existing data")
    mode_mother = fields.Selection(_MODE_SELECTION, string='Mode Mothers',help="Update selected fields or clear existing data")
    mode_qua = fields.Selection(_MODE_SELECTION, string='Mode Qualification',help="Update selected fields or clear existing data")
    mode_office_class = fields.Selection(_MODE_SELECTION, string='Mode Office Class',help="Update selected fields or clear existing data")
    mode_teacher = fields.Selection(_MODE_SELECTION, string='Mode Teacher',help="Update selected fields or clear existing data")
    mode_subscrip = fields.Selection(_MODE_SELECTION, string='Mode Subscription',help="Update selected fields or clear existing data")
    mode_discount = fields.Selection(_MODE_SELECTION, string='Mode Discount',help="Update selected fields or clear existing data")
    mode_salary = fields.Selection(_MODE_SELECTION, string='Mode salary',help="Update selected fields or clear existing data")
    
    # Area and Tags fields -----------------------------------------------------------
    area_id = fields.Many2one(
        'quran.office.area',
        'Area',
        help="Select area for persons"
    )
    tag_ids = fields.Many2many(
        'res.partner.category',
        'person_area_tags_wizard_category_rel',
        'wizard_id',
        'category_id',
        string='Tags',
        help="Tags to add to persons"
    )
    tags_mode = fields.Selection([
            ('add', 'Add Tags'),
            ('replace', 'Replace Tags'),
        ], string='Tags Mode', default='add', required=True,
           help="Add tags to existing ones or replace all tags")
        

    # Parent Data Fields ------------------------------------------------------------------------
    father_id = fields.Many2one(
        'res.persons',
        'Father Name',
        domain="[('parent_role', '=', 'father')]",
        help="Select the father from existing persons"
    )
    mother_id = fields.Many2one(
        'res.persons',
        'Mother Name',
        domain="[('parent_role', '=', 'mother')]",
        help="Select the mother from existing persons"
    )

    # Academic Qualification Fields ------------------------------------------------------------------------
    qualification = fields.Char(
            string='Qualification',
            help="Enter the academic qualification for persons"
        )

    # Subscription Fields -----------------------------------------------------------
    subscription_fee = fields.Monetary(
        'Subscription Fee', currency_field='currency_id',
        help="Student subscription fee"
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency for subscription fee"
    )
    discount_percentage_fee = fields.Float(
        'Discount %',
        help="Discount percentage for student subscription fee"
    )
    reason_discount_fee = fields.Char(
        'Reason for Discount',
        help="Reason for discount on student subscription fee"
    )

    # Salary Fields -----------------------------------------------------------
    teacher_salary = fields.Monetary(
            'Teacher Salary', currency_field='currency_id',
            help="Teacher monthly salary"
        )


    #========================= OnChange Methods =========================
    @api.onchange('mode_subscrip')
    def _onchange_mode_subscrip(self):
        """
        Clear checkboxes when switching to clear mode
        """
        if self.mode_subscrip == 'clear':
            self.mode_discount = 'clear'
        else:
            self.mode_discount = False

    @api.onchange('discount_percentage_fee')
    def _onchange_discount_percentage_fee(self):
        """
        Clear reason when discount is zero
        """
        if self.discount_percentage_fee == 0:
            self.reason_discount_fee = False

    @api.constrains('teacher_salary','subscription_fee','discount_percentage_fee')
    def _check_salary_subscription_discount(self):
        """
        Check if teacher salary, subscription fee, and discount percentage are not negative or zero in update mode.
        """
        for record in self:
            if record.teacher_salary <= 0 and record.mode_salary == 'update':
                raise ValidationError(_("Teacher salary cannot be negative or zero in update mode."))
            if record.subscription_fee <= 0 and record.mode_subscrip == 'update':
                raise ValidationError(_("Subscription fee cannot be negative or zero in update mode."))
            if record.discount_percentage_fee <= 0 and record.mode_discount == 'update':
                raise ValidationError(_("Discount percentage cannot be negative or zero in update mode."))

    def action_update_selected_fields_data(self):
        """
        Apply selected fields changes to selected persons based on mode and selected fields
        """
        # Map modes to fields
        mode_fields = {
            'mode_area': 'area_id',
            'mode_father': 'father_id',
            'mode_mother': 'mother_id',
            'mode_qua': 'qualification',
            'mode_office_class': 'office_id',
            'mode_teacher': 'teacher_id',
            'mode_subscrip': 'subscription_fee',
            'mode_discount': 'discount_percentage_fee',
            'mode_salary': 'teacher_salary',
        }

        # Get persons from active_ids
        active_model = self.env.context.get('active_model')
        if active_model != 'res.persons':
            raise UserError(
                _('This wizard must be opened from Contacts.')
            )

        active_ids = self.env.context.get('active_ids', [])
        persons = self.env['res.persons'].browse(active_ids)

        update_values = {}
        for mode in mode_fields:
            field = mode_fields[mode]
            mode_value = getattr(self,mode,False)
            if mode_value == 'update':
                update_values[field] = getattr(self,field,False)
            elif mode_value == 'clear':
                update_values[field] = False

            # Special cases for modes that require additional fields
            if mode == 'mode_discount':
                if mode_value == 'update':
                    update_values['reason_discount_fee'] = self.reason_discount_fee
                elif mode_value == 'clear':
                    update_values['reason_discount_fee'] = False

            if mode == 'mode_office_class':
                if mode_value == 'update':
                    update_values['class_id'] = self.class_id
                elif mode_value == 'clear':
                    update_values['class_id'] = False

        if not update_values and not self.mode_tags:
            raise ValidationError(_('Please select at least one field to update'))
        persons.write(update_values)

        if not self.mode_tags:
            return
        # Update tags
        for person in persons:
            tags_value = []
            if self.mode_tags == 'update':
                tags_ids = self.tag_ids.ids
                if self.tags_mode == 'add':
                    # Add tags to existing ones
                    current_tag_ids = person.mapped('tags_ids').ids
                    new_tag_ids = list(set(current_tag_ids + tags_ids))
                    tags_value = [(6, 0, new_tag_ids)]
                else: # tags_mode == 'replace':
                    # Replace all tags
                    tags_value = [(6, 0, tags_ids)]
            else: #mode_tags == 'clear':
                tags_value = [(6, 0, [])]
            person.write({'tags_ids': tags_value})