# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .constants import _STUDENT_STATUS_SELECTION
from .utils import (fnc_editstring, get_birth_date_from_national_id, get_gender_from_national_id,
                     is_invalid_national_id, get_detailed_age)


class StudentPortal(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner','memorization.mixin', 'school.organization.mixin']

    # Basic identification fields
    first_name = fields.Char(
        'First Name',
        help="Partner's first name"
    )
    middle_name = fields.Char(
        'Middle Name',
        help="Partner's middle name",
        )
    third_name = fields.Char(
        'Third Name',
        help="Partner's third name",
        )
    last_name = fields.Char(
        'Last Name',
        help="Partner's last name",
        )

    # Computed fields
    age_from_id = fields.Char(
        'Detailed Age',
        compute='_compute_age_from_id',
    )
    age_years = fields.Integer(
        'Age (Years)',
        compute='_compute_age_from_id',
        search='_search_age_years'
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
        help="Egyptian national ID number (14 digits)"
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
    ], 'Gender', compute='_compute_birthdate_gender_from_id', store=True, readonly=False, help="Partner's gender")

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
    # Identity documents of minors: visible only to Quran office users
    birth_certificate = fields.Binary(
        'Birth Certificate',
        groups='management_quran_office_core.group_quran_office_user',
        help="Upload birth certificate"
    )
    id_card_front = fields.Binary(
        'ID Card Front',
        groups='management_quran_office_core.group_quran_office_user',
        help="Upload front side of ID card"
    )
    id_card_back = fields.Binary(
        'ID Card Back',
        groups='management_quran_office_core.group_quran_office_user',
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
    subscription_fee = fields.Monetary(
        'Subscription Fee', currency_field='currency_id',
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
    student_status = fields.Selection(_STUDENT_STATUS_SELECTION, 'Student Status',
        help="Student persistence status - only shown for students")

# ====================== Teachers Fields ============================================
    class_ids = fields.One2many(
        'quran.office.class',
        'teacher_id',
        'Classes as Teacher'
    )
    teacher_salary = fields.Monetary(
        'Teacher Salary', currency_field='currency_id',
        groups='management_quran_office_core.group_quran_office_manager',
        help="Teacher monthly salary"
    )
    currency_id = fields.Many2one(
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

    _sql_constraints = [('id_number_uniq', "unique(id_number)", "ID Number must be unique per partner.")]

    # Fields used to build the display name of a person
    _NAME_PARTS = ('first_name', 'middle_name', 'third_name')

    @api.model
    def _quran_join_name(self, *parts):
        """Join only the non empty name parts (avoids 'False' in names)."""
        return ' '.join(p.strip() for p in parts if p and p.strip())


############################## Builtin Functions #############################################
    @api.model_create_multi
    def create(self, vals_list):
        """Generate the registration number (students, teachers and parents only)
        and build the name from the non empty name parts."""
        for vals in vals_list:
            if not vals.get('ref') and (vals.get('is_student') or vals.get('is_teacher') or vals.get('parent_role')):
                vals['ref'] = self.env['ir.sequence'].next_by_code('res.partner')

            if vals.get('father_id') and vals.get('first_name'):
                father = self.env['res.partner'].browse(vals['father_id'])
                vals['middle_name'] = father.first_name
                vals['third_name'] = father.middle_name
                vals['last_name'] = self._quran_join_name(father.third_name, father.last_name)
                
            if vals.get('first_name') and vals.get('middle_name') and vals.get('third_name') and not vals.get('is_company') and not vals.get('name'):
                vals['name'] = self._quran_join_name(
                    vals.get('first_name'), vals.get('middle_name'), vals.get('third_name'))
        return super().create(vals_list)

    def write(self, vals):
        """Rebuild the name per record when a name part changes, and give a
        registration number to partners that just became student/teacher/parent."""
        result = super().write(vals)

        father = self.father_id
        if (any(f in vals for f in self._NAME_PARTS) or 'father_id' in vals) and len(self) == 1 and father:
            self.name = self._quran_join_name(self.first_name, father.first_name, father.middle_name)
            self.last_name = self._quran_join_name(father.third_name, father.last_name)

        if any(k in vals for k in ('is_student', 'is_teacher', 'parent_role')):
            for record in self.filtered(lambda r: not r.ref and (r.is_student or r.is_teacher or r.parent_role)):
                record.ref = self.env['ir.sequence'].next_by_code('res.partner')
        return result

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name',
                 'ref', 'is_student', 'is_teacher', 'parent_role')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        super()._compute_display_name()
        for partner in self:
            if partner.ref and (partner.is_student or partner.is_teacher or partner.parent_role):
                partner.display_name = f"[{partner.ref}] {partner.display_name}".strip()

############################## Onchange Functions #############################################
    @api.onchange('first_name', 'middle_name', 'third_name')
    def _onchange_name(self):
        """
        Automatically update the partner name when name fields change.
        This ensures consistency between student and partner records.
        """
        if self.first_name:
            self.name = self._quran_join_name(self.first_name, self.middle_name, self.third_name)

############################## Compute & Search Functions #########################################################
    def _search_age_years(self, operator, value):
        """Search by age in full years, honouring the operator.
        age >= N  <=>  birth_date <= today - N years
        age <  N  <=>  birth_date >  today - N years"""
        if value is False or value is None:
            return [('birth_date', '=' if operator in ('=', '==') else '!=', False)]
        try:
            value = int(value)
        except (TypeError, ValueError):
            return [('id', '=', 0)]
        today = fields.Date.today()
        born_before = today - relativedelta(years=value)        # age >= value
        born_before_next = today - relativedelta(years=value + 1)  # age >= value + 1
        if operator in ('=', '=='):
            return [('birth_date', '>', born_before_next), ('birth_date', '<=', born_before)]
        if operator == '!=':
            return ['|', ('birth_date', '<=', born_before_next), ('birth_date', '>', born_before)]
        if operator == '>':
            return [('birth_date', '<=', born_before_next)]
        if operator == '>=':
            return [('birth_date', '<=', born_before)]
        if operator == '<':
            return [('birth_date', '>', born_before)]
        if operator == '<=':
            return [('birth_date', '>', born_before_next)]
        raise ValueError(_("Unsupported operator %s for age search.") % operator)

    @api.depends('id_number', 'parent_role')
    def _compute_birthdate_gender_from_id(self):
        """Fill birth_date and gender from a valid national ID.
        Without a valid ID, existing manual values are kept; a parent role only
        provides a default gender when none is set."""
        for record in self:
            id_number = record.id_number
            if id_number and not is_invalid_national_id(id_number):
                record.birth_date = get_birth_date_from_national_id(id_number)
                record.gender = get_gender_from_national_id(id_number)
            else:
                record.birth_date = record.birth_date
                if record.parent_role == 'mother':
                    record.gender = record.gender or 'f'
                elif record.parent_role == 'father':
                    record.gender = record.gender or 'm'
                else:
                    record.gender = record.gender

    @api.onchange('father_id')
    def _onchange_father_set_partner_middle_last_third_name(self):
        """
        Auto-fill partner's name fields from father's name.
        Father's first_name -> partner's middle_name
        Father's middle_name -> partner's third_name
        Father's third_name -> partner's last_name
        """
        if self.father_id:
            father_first_name = self.father_id.first_name
            father_middle_name = self.father_id.middle_name
            father_third_name = self.father_id.third_name
            father_last_name = self.father_id.last_name
            
            self.middle_name = father_first_name
            self.third_name = father_middle_name
            self.last_name = self._quran_join_name(father_third_name, father_last_name)

    @api.depends('first_name', 'middle_name', 'third_name', 'last_name', 'is_company', 'name',
                 'parent_id.name', 'type', 'company_name', 'commercial_company_name')
    def _compute_complete_name(self):
        """Compute complete_name from the non empty name parts (original spelling is kept)."""
        super()._compute_complete_name()
        for partner in self:
            if partner.first_name and partner.middle_name and partner.third_name and not partner.is_company:
                partner.complete_name = self._quran_join_name(
                    partner.first_name, partner.middle_name, partner.third_name, partner.last_name)

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
        self.children_count = 0
        for role, field_name in [('father', 'father_id'),('mother', 'mother_id'),]:
            records = self.filtered(lambda r: r.parent_role == role)
            if not records:
                continue

            counts = self.env['res.partner']._read_group(
                domain=[(field_name, 'in', records.ids)],
                groupby=[field_name],
                aggregates=['id:count'],)
            if counts:
                for record,count in counts:
                    record.children_count = count
            else:
                records.children_count = 0
        

############################## Constraints And Validation #############################################
    @api.constrains('id_number')
    def _check_unique_id_number(self):
        """Check if ID number is unique when provided."""
        for record in self:
            if record.id_number and is_invalid_national_id(record.id_number):
                raise ValidationError(_(
                    "Invalid Egyptian National ID format! "
                    "Please enter a valid 14-digit national ID number."))

    @api.constrains('first_name', 'middle_name', 'third_name', 'last_name', 'birth_date')
    def _check_duplicate_person(self):
        """Two different people may share the same four names; block only an
        identical name together with an identical birth date."""
        for record in self:
            if not (record.first_name and record.birth_date):
                continue
            duplicate = self.with_context(active_test=False).search_count([
                ('id', '!=', record.id),
                ('first_name', '=', record.first_name),
                ('middle_name', '=', record.middle_name or False),
                ('third_name', '=', record.third_name or False),
                ('last_name', '=', record.last_name or False),
                ('birth_date', '=', record.birth_date),
            ])
            if duplicate:
                raise ValidationError(_(
                    "A partner with the same name and birth date already exists."))

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

    def action_set_partner_as_fatherless(self):
        """Set student as fatherless"""
        self.is_fatherless = True
        return True
    
    def action_set_partner_not_fatherless(self):
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


