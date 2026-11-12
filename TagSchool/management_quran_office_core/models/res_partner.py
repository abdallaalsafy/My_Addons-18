# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .utils import (fnc_editstring, get_birth_date_from_national_id, get_gender_from_national_id,
                     is_invalid_national_id, get_detailed_age)


class StudentPortal(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner','memorization.mixin']

    # Basic identification fields
    first_name = fields.Char(
        'First Name',
        required=True,
        help="Partner's first name"
    )
    middle_name = fields.Char(
        'Middle Name',
        required=True,
        help="Partner's middle name",
        compute='_compute_partner_middle_last_third_name', store=True, readonly=False,
    )
    third_name = fields.Char(
        'Third Name',
        required=True,
        help="Partner's third name",
        compute='_compute_partner_middle_last_third_name', store=True, readonly=False,
    )
    last_name = fields.Char(
        'Last Name',
        help="Partner's last name",
        compute='_compute_partner_middle_last_third_name', store=True, readonly=False,
    )

    # Computed fields
    age_from_id = fields.Char(
        'Detailed Age',
        compute='_compute_age_from_id',
    )
    age_years = fields.Integer(
        'Age (Years)',
        compute='_compute_age_from_id',
    )
    age_months = fields.Integer(
        'Age (Months)',
        compute='_compute_age_from_id',
    )
    age_days = fields.Integer(
        'Age (Days)',
        compute='_compute_age_from_id',
    )

    # Official identification
    id_number = fields.Char(
        'ID Card Number',
        size=14,
        help="National ID or passport number"
    )

    # Personal information
    birth_date = fields.Date(
        'Birth Date',
        compute='_compute_birthdate_gender_from_id', store=True, readonly=False,
        help="Student's date of birth"
    )

    gender = fields.Selection([
        ('m', 'Male'),
        ('f', 'Female'),
    ], 'Gender', required=True, compute='_compute_birthdate_gender_from_id', store=True, readonly=False, help="Partner's gender")

    # Family relationships
    father_id = fields.Many2one(
        'res.partner', 
        'Father Name',
        domain="[('parent_role', '=', 'father')]",
        help="Select the father from existing partners"
    )
    mother_id = fields.Many2one(
        'res.partner', 
        'Mother Name', 
        domain="[('parent_role', '=', 'mother')]",
        help="Select the mother from existing partners"
    )
    
    # Location information
    area_id = fields.Many2one(
        'quran.office.area',
        'Area/District',
        help="Select the area/district where the partner is located"
    )

    # Document fields
    personal_photo_file = fields.Char(string='Personal Photo File Name')
    birth_certificate_file = fields.Char(string='Birth Certificate File Name')
    id_card_front_file = fields.Char(string='ID Card Front File Name')
    id_card_back_file = fields.Char(string='ID Card Back File Name ')
    personal_photo = fields.Binary(
        'Personal Photo',
        help="Upload personal photo"
    )
    birth_certificate = fields.Binary(
        'Birth Certificate',
        help="Upload birth certificate"
    )
    id_card_front = fields.Binary(
        'ID Card Front',
        help="Upload front side of ID card"
    )
    id_card_back = fields.Binary(
        'ID Card Back',
        help="Upload back side of ID card"
    )
    additional_documents = fields.Many2many(
        'ir.attachment',
        'partner_document_rel',
        'partner_id',
        'attachment_id',
        'Additional Documents',
        help="Upload additional documents"
    )

    is_quran_memorizer = fields.Boolean(
        'Complete Quran Memorizer',
        help="Has memorized the entire Quran"
    )
    
    # Academic qualification field for all partners
    qualification = fields.Char(
        'Qualification',
        help="Academic qualification of the partner"
    )

    # ========== Students Fields ===========================================
    # Education relationships
    office_id = fields.Many2one(
        'quran.office.office',
        'Office',
        help="Quran memorization office this partner belongs to"
    )
    class_id = fields.Many2one(
        'quran.office.class',
        'Class',
        domain="[('office_id', '=?', office_id)]",
        help="Class this student belongs to"
    )
    teacher_id = fields.Many2one(
        'res.partner',
        'Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Students who are teachers"
    )
    subscription_fee = fields.Monetary(
        'Subscription Fee', currency_field='currancy_id',
        help="Student subscription fee amount"
    )
    discount_percentage_fee = fields.Float(
        'Discount %',
        digits=(5, 2),
        help="Discount percentage for student subscription fee"
    )
    reason_discount_fee = fields.Char(
        'Reason for Discount',
        help="Reason for discount on student subscription fee"
    )
    is_fatherless = fields.Boolean(
        'Fatherless',
        help="Is the student fatherless"
    )
    student_status = fields.Selection([
        ('persistent', 'Persistent'),
        ('disconnected', 'Disconnected'),
    ], 'Student Status',
        help="Student attendance status - only shown for students")

    # ====================== Teachers Fields ============================================
    class_ids = fields.One2many(
        'quran.office.class',
        'teacher_id',
        'Classes as Teacher'
    )
    teacher_salary = fields.Monetary(
        'Teacher Salary', currency_field='currancy_id',
        help="Teacher monthly salary"
    )
    currancy_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency for subscription fee"
    )
    #============================== Parent Fields =========================================

    # Parent role selection (only one can be selected)
    parent_role = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
    ], 'Parent Role', help="Select the parent role (only one can be selected)")
    # Children count for fathers and mothers
    children_count = fields.Integer(
        'Children Count',
        compute='_compute_children_count',
        help="Number of children for this partner (only shown for fathers and mothers)"
    )
    #============================================================
    # Backward compatibility boolean fields
    is_student = fields.Boolean("Is a Student")
    is_teacher = fields.Boolean("Is a Teacher")
    is_employee = fields.Boolean("Is a Employee")

    _sql_constraints = [('name_uniq', "unique(name)", "Name must be unique per partner."),
                        ('complete_name_uniq', "unique(complete_name)", "Complete Name must be unique per partner."),
                        ('id_number_uniq', "unique(id_number)", "ID Number must be unique per partner.")]


############################## Builtin Functions #############################################
    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate registration number automatically."""
        for vals in vals_list:
            # Generate registration number if not provided
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('res.partner')

        return super().create(vals_list)

    def name_get(self):
        """Override name_get to show code and name."""
        result = []
        for partner in self:
            if partner.ref:
                name = f"[{partner.ref}] {partner.name}"
            else:
                name = partner.name
            result.append((partner.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search to find partners by name or reference."""
        if name == '':
            # Search by reference first
            domain = [('ref', operator, name)]
            students = self.search(domain + (args or []), limit=limit)
            if students:
                return students.name_get()

            # Then search by name
            domain = [('name', operator, name)]
            students = self.search(domain + (args or []), limit=limit)
            if students:
                return students.name_get()

        return super().name_search(name, args, operator, limit)

############################## Onchange Functions #############################################
    @api.onchange('first_name', 'middle_name', 'third_name')
    def _onchange_name(self):
        """
        Automatically update the partner name when name fields change.
        This ensures consistency between student and partner records.
        """
        if self.first_name and self.middle_name and self.third_name:
            self.name = f"{self.first_name} {self.middle_name} {self.third_name}"

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
            self.class_id = self.teacher_id.class_ids[0]

############################## Compute Fields #########################################################
    @api.depends('id_number','parent_role')
    def _compute_birthdate_gender_from_id(self):
        """Auto_fill birth_date and gender from national ID."""
        for record in self:
            id_number = record.id_number
            if not is_invalid_national_id(id_number):
                try:
                    # Auto_fill birth_date
                    record.birth_date = get_birth_date_from_national_id(id_number)
                    # Auto-fill gender
                    record.gender = get_gender_from_national_id(id_number)
                except:
                    pass
            else:
                record.gender = 'f' if record.parent_role == 'mother' else 'm'

    @api.depends('father_id')
    def _compute_partner_middle_last_third_name(self):
        """
        Auto-fill partner's name fields from father's name.
        Father's first_name -> partner's middle_name
        Father's middle_name -> partner's third_name
        Father's third_name -> partner's last_name
        """
        for record in self:
            if record.father_id:
                record.middle_name = record.father_id.first_name
                record.third_name = record.father_id.middle_name
                record.last_name = (record.father_id.third_name + " " + (record.father_id.last_name or "")).strip()


    @api.depends('first_name', 'middle_name', 'third_name','last_name')
    def _compute_complete_name(self):
        """Compute complete_name with Arabic character normalization."""
        for partner in self:
            if partner.first_name and partner.middle_name and partner.third_name:
                full_name = partner.first_name + " " + partner.middle_name + " " + partner.third_name
                if partner.last_name:
                    full_name += " " + partner.last_name
                partner.complete_name = fnc_editstring(full_name)
            else:
                partner.complete_name = partner.name

    def _compute_age_from_id(self):
        """Compute age from national ID or birthdate using unified functions."""
        for student in self:
            try:
                # Use unified functions that handle both ID and birthdate
                student.age_from_id,student.age_years,student.age_months,student.age_days = get_detailed_age(national_id=student.id_number, birth_date=student.birth_date)
            except:
                student.age_from_id = _("Not specified")
                student.age_years = 0

    @api.depends('parent_role')
    def _compute_children_count(self):
        """Compute the number of children for this partner (only for fathers and mothers)"""
        for record in self:
            if record.parent_role == 'father':
                # Count students where this partner is the father
                children = self.search([('father_id', '=', record.id)])
                record.children_count = len(children)
            elif record.parent_role == 'mother':
                # Count students where this partner is the mother
                children = self.search([('mother_id', '=', record.id)])
                record.children_count = len(children)
            else:
                record.children_count = 0

############################## Constraints And Validation #############################################
    @api.constrains('id_number')
    def _check_unique_id_number(self):
        """Check if ID number is unique when provided."""
        for record in self:
            if record.id_number and is_invalid_national_id(record.id_number):
                raise ValidationError(_(
                    "Invalid Egyptian National ID format! "
                    "Please enter a valid 14-digit national ID number."))

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """Validate that birthdate is not in the future."""
        for record in self:
            if record.birth_date and record.birth_date > fields.Date.today():
                raise ValidationError(_(
                    "Birth Date can't be greater than current date!"))

    @api.constrains('father_id')
    def _check_father_gender(self):
        """
        Validate that father is male.
        Check that a partner cannot be their own father.
        """
        for record in self:
            if record.father_id:
                if record.father_id.gender != 'm':
                    raise ValidationError(_("Father must be male! Please select a male partner as father."))
                if record.father_id.id == record.id:
                    raise ValidationError(_('A partner cannot be their own father!'))

    @api.constrains('mother_id')
    def _check_mother_gender(self):
        """
        Validate that mother is female.
        Check that a partner cannot be their own mother.
        """
        for record in self:
            if record.mother_id:
                if record.mother_id.gender != 'f':
                    raise ValidationError(_("Mother must be female! Please select a female partner as mother."))
                if record.mother_id.id == record.id:
                    raise ValidationError(_('A partner cannot be their own mother!'))

    @api.constrains('teacher_id')
    def _check_teacher_not_self(self):
        """Check that a partner cannot be their own teacher."""
        for record in self:
            if record.teacher_id and record.teacher_id.id == record.id:
                raise ValidationError(_('A partner cannot be their own teacher!'))

    @api.constrains('juze_amount', 'memorization_method','surah_id', 'ayah_num')
    def _constrains_memorization_amount_consistency(self):
        """Validate memorization amount consistency with surah and ayah calculation."""
        for record in self:
            if (record.surah_id or record.ayah_num !=0 or record.juze_amount != 0) and record.memorization_method != 'mixed':
                record._check_memorization_amount_consistency()

############################## Actions Functions #############################################
    def action_make_teacher(self):
        """Convert partner to teacher"""
        self.write({'is_teacher': True})

    def action_make_student(self):
        """Convert partner to student"""
        self.write({'is_student': True})

    def action_make_mother(self):
        """Convert female partner to mother"""
        for record in self:
            if record.gender != 'f':
                raise ValidationError(_("Only female partners can be converted to mother."))
            record.parent_role = 'mother'

    def action_make_father(self):
        """Convert male partner to father"""
        for record in self:
            if record.gender != 'm':
                raise ValidationError(_("Only male partners can be converted to father."))
            record.parent_role = 'father'

    def action_remove_father_role(self):
        """Remove father role if no active children"""
        for record in self:
            if record.parent_role == 'father':
                if record.children_count > 0:
                    raise ValidationError(_("Cannot remove father role: This partner has active children."))
                record.parent_role = False

    def action_remove_mother_role(self):
        """Remove mother role if no active children"""
        for record in self:
            if record.parent_role == 'mother':
                if record.children_count > 0:
                    raise ValidationError(_("Cannot remove mother role: This partner has active children."))
                record.parent_role = False

    def action_remove_teacher_role(self):
        """Remove teacher role if no active students or classes"""
        for record in self:
            if record._check_teacher_has_students_or_classes() and record.is_teacher:
                raise ValidationError(_("Cannot remove teacher role: This teacher has active students or classes."))
            record.is_teacher = False

    def action_remove_student_role(self):
        """Remove student role if no active assignments"""
        for record in self:
            if record._check_student_has_assignments() and record.is_student:
                raise ValidationError(_("Cannot remove student role: This student has active assignments (office, class, teacher, or subscription)."))
            record.is_student = False

    def action_mark_persistent(self):
        """Mark selected students as persistent"""
        for record in self:
            record.student_status = 'persistent' if record.is_student else False

    def action_mark_disconnected(self):
        """Mark selected students as disconnected"""
        for record in self:
            record.student_status = 'disconnected' if record.is_student else False

    def Action_set_partner_as_fatherless(self):
        """Set student as fatherless"""
        self.is_fatherless = True
        return True
    
    def Action_set_partner_not_fatherless(self):
        """Set student as not fatherless"""
        self.is_fatherless = False
        return True
    
    def action_view_children(self):
        """View children of this partner (father or mother)"""
        self.ensure_one()
        name = ''
        domain = []
        if self.parent_role == 'father':
            domain = [('father_id', '=', self.id)]
            name = _('Children of %s (Father)') % self.name
        elif self.parent_role == 'mother':
            domain = [('mother_id', '=', self.id)]
            name = _('Children of %s (Mother)') % self.name
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_father_id': self.id if self.parent_role == 'father' else False,
                'default_mother_id': self.id if self.parent_role == 'mother' else False,
            }
        }

    def action_open_update_partner_data_wizard(self):
        return {
            'name': _('Update Partner Data Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.partner.data.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'is_student': self._context.get('default_is_student', False),
                'is_teacher': self._context.get('default_is_teacher', False),
            }
        }

############################## Helper Functions #############################################
    def _check_teacher_has_students_or_classes(self):
        """Check if teacher has active students or classes"""
        self.ensure_one()
        # Check if teacher is assigned to any students
        students = self.env['res.partner'].search([('teacher_id', '=', self.id)])
        return bool(students) or bool(self.class_ids)

    def _check_student_has_assignments(self):
        """Check if student has active assignments"""
        self.ensure_one()
        return bool(
            self.office_id or 
            self.class_id or 
            self.teacher_id or 
            self.subscription_fee > 0
        )

    def validate_status_of_student(self):
        """Check student status"""
        self.ensure_one()

        if not self.is_student:
            raise ValidationError(
                _('This partner is not a student (%s).') % self.name)
        if self.student_status == 'disconnected':
            raise ValidationError(
                _('This student is disconnected (%s).') % self.name)
        if not self.active:
            raise ValidationError(
                _('This student is not active (%s).') % self.name)


