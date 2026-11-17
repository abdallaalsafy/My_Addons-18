# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .constants import _STUDENT_STATUS_SELECTION
from .utils import (fnc_editstring, get_birth_date_from_national_id, get_gender_from_national_id,
                     is_invalid_national_id, get_detailed_age)


class ResPersons(models.Model):
    _name = 'res.persons'
    _inherit = ['memorization.mixin', 'school.organization.mixin']
    _description = 'Quran School person Extension'
    _order = 'complete_name'

    # Basic identification fields
    name = fields.Char(
        'Name',
        compute='_compute_main_person_name', store=True,
        help="Computed person's name"
    )
    ref = fields.Char(
        'Reference',
        default=_('New'),
        readonly=True,
        help="Internal reference number"
    )
    complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name', store=True,
        help="Complete person's name"
    )
    first_name = fields.Char(
        'First Name',
        required=True,
        help="person's first name"
    )
    middle_name = fields.Char(
        'Middle Name', required=True,
        compute='_compute_father_set_person_middle_last_third_name', readonly=False,store=True,
        help="person's middle name",
        )
    third_name = fields.Char(
        'Third Name', required=True,
        compute='_compute_father_set_person_middle_last_third_name', readonly=False,store=True,
        help="person's third name",
        )
    last_name = fields.Char(
        'Last Name',
        compute='_compute_father_set_person_middle_last_third_name', readonly=False,store=True,
        help="person's last name",
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
    ], 'Gender', compute='_compute_birthdate_gender_from_id', store=True, readonly=False, help="person's gender")

    photo = fields.Binary(
        'Photo',
        help="Upload a photo of the person"
    )
    street = fields.Char(
        'Street',
        help="Street address of the person"
    )
    function = fields.Char(
        'Function',
        help="Function or role of the person"
    )
    phone = fields.Char(
        'Phone',
        help="Phone number of the person"
    )
    mobile = fields.Char(
        'Mobile',
        help="Mobile number of the person"
    )
    email = fields.Char(
        'Email',
        help="Email address of the person"
    )
    website = fields.Char(
        'Website',
        help="Website of the person"
    )
    title = fields.Many2one(
        'res.partner.title',
        'Title',
        help="Title of the person"
    )
    tags_ids = fields.Many2many(
        'res.partner.category',
        'res_partner_res_partner_tags_rel',
        'partner_id', 'tag_id',
        'Tags',
        help="Tags for categorizing the person"
    )
    # Family relationships
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
    
    # Location information
    area_id = fields.Many2one(
        'quran.office.area',
        'Area/District',
        help="Select the area/district where the person is located"
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
        'person_document_rel',
        'person_id',
        'attachment_id',
        'Additional Documents',
        help="Upload additional documents"
    )

    is_quran_memorizer = fields.Boolean(
        'Complete Quran Memorizer',
        help="Has memorized the entire Quran"
    )
    
    # Academic qualification field for all persons
    qualification = fields.Char(
        'Qualification',
        help="Academic qualification of the person"
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
    status = fields.Selection(_STUDENT_STATUS_SELECTION, 'Student Status',
        help="Student persistence status - only shown for students")

# ====================== Teachers Fields ============================================
    class_ids = fields.One2many(
        'quran.office.class',
        'teacher_id',
        'Classes as Teacher'
    )
    teacher_salary = fields.Monetary(
        'Teacher Salary', currency_field='currency_id',
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
        help="Number of children for this person (only shown for fathers and mothers)"
    )
#============================================================
    # Backward compatibility boolean fields
    is_student = fields.Boolean("Is a Student")
    is_teacher = fields.Boolean("Is a Teacher")
    
    active = fields.Boolean("Active", default=True)
    notes = fields.Text("Internal Notes")
    _sql_constraints = [('id_number_uniq', "unique(id_number)", "ID Number must be unique per person.")]

    # Fields used to build the display name of a person
    _NAME_PARTS = ('first_name', 'middle_name', 'third_name')

    @api.model
    def _quran_join_name(self, *parts):
        """Join only the non empty name parts (avoids 'False' in names)."""
        return ' '.join(p.strip() for p in parts if p and p.strip())


#================================ Builtin Functions ========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Generate the reference number."""
        for vals in vals_list:
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('res.persons')

        return super().create(vals_list)

    @api.depends('name', 'ref')
    def _compute_display_name(self):
        super()._compute_display_name()
        for person in self:
            person.display_name = f"[{person.ref}] {person.name}"

#================================ Search Functions ==============================================
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

#================================= Compute Functions =========================================
    @api.depends('father_id.first_name', 'father_id.middle_name',
             'father_id.third_name', 'father_id.last_name')
    def _compute_father_set_person_middle_last_third_name(self):
        """
        Auto-fill person's name fields from father's name.
        Father's first_name -> person's middle_name
        Father's middle_name -> person's third_name
        Father's third_name -> person's last_name
        """
        for record in self:
            father = record.father_id
            if father:
                father_first_name = father.first_name
                father_middle_name = father.middle_name
                father_third_name = father.third_name
                father_last_name = father.last_name
                
                record.middle_name = father_first_name
                record.third_name = father_middle_name
                record.last_name = self._quran_join_name(father_third_name, father_last_name)

    @api.depends('first_name', 'middle_name', 'third_name')
    def _compute_main_person_name(self):
        """Compute the main name of the person based on first, middle, and third names."""
        for person in self:
            person.name = self._quran_join_name(person.first_name, person.middle_name, person.third_name)

    @api.depends('name', 'last_name')
    def _compute_complete_name(self):
        """Compute the complete name of the person based on name and last_name."""
        for person in self:
            person.complete_name = self._quran_join_name(person.name, person.last_name)

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

    def _compute_age_from_id(self):
        """Compute age from national ID or birthdate using unified functions."""
        for student in self:
            # Use unified functions that handle both ID and birthdate
            student.age_from_id,student.age_years,student.age_months,student.age_days = get_detailed_age(national_id=student.id_number, birth_date=student.birth_date)

    @api.depends('parent_role')
    def _compute_children_count(self):
        self.children_count = 0
        for role, field_name in [('father', 'father_id'),('mother', 'mother_id'),]:
            records = self.filtered(lambda r: r.parent_role == role)
            if not records:
                continue

            counts = self.env['res.persons']._read_group(
                domain=[(field_name, 'in', records.ids)],
                groupby=[field_name],
                aggregates=['id:count'],)
            if counts:
                for record,count in counts:
                    record.children_count = count
            else:
                records.children_count = 0
        
#=================================== Constraints And Validation =========================================
    @api.constrains('id_number')
    def _check_valid_id_number(self):
        """Check if ID number is unique when provided."""
        for record in self:
            if record.id_number and is_invalid_national_id(record.id_number):
                raise ValidationError(_(
                    "Invalid Egyptian National ID format! "
                    "Please enter a valid 14-digit national ID number."))

    @api.constrains('first_name', 'middle_name', 'third_name', 'last_name')
    def _check_duplicate_person(self):
        """Check for duplicate persons based on their complete name."""
        for record in self:
            if not record.complete_name:
                raise ValidationError(_("Complete name cannot be empty. Please fill in the name fields."))
            duplicate = self.with_context(active_test=False).search_count([
                ('id', '!=', record.id),
                ('complete_name', '=', record.complete_name),
            ])
            if duplicate:
                raise ValidationError(_("A person %s with the same complete name already exists." % record.complete_name))

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
        Check that a person cannot be their own father.
        """
        for record in self:
            if record.father_id:
                if record.father_id.gender != 'm':
                    raise ValidationError(_("Father must be male! Please select a male person as father."))
                if record.father_id.id == record.id:
                    raise ValidationError(_('A person cannot be their own father!'))

    @api.constrains('mother_id')
    def _check_mother_gender(self):
        """
        Validate that mother is female.
        Check that a person cannot be their own mother.
        """
        for record in self:
            if record.mother_id:
                if record.mother_id.gender != 'f':
                    raise ValidationError(_("Mother must be female! Please select a female person as mother."))
                if record.mother_id.id == record.id:
                    raise ValidationError(_('A person cannot be their own mother!'))

    @api.constrains('teacher_id')
    def _check_teacher_not_self(self):
        """Check that a person cannot be their own teacher."""
        for record in self:
            if record.teacher_id and record.teacher_id.id == record.id:
                raise ValidationError(_('A person cannot be their own teacher!'))

    @api.constrains('juze_amount', 'memorization_method','surah_id', 'ayah_num')
    def _constrains_memorization_amount_consistency(self):
        """Validate memorization amount consistency with surah and ayah calculation."""
        for record in self:
            if (record.surah_id or record.ayah_num !=0 or record.juze_amount != 0) and record.memorization_method != 'mixed':
                record._check_memorization_amount_consistency()

#==================================== Actions Functions ========================================
    def action_make_teacher(self):
        """Convert person to teacher"""
        self.write({'is_teacher': True})

    def action_make_student(self):
        """Convert person to student"""
        self.write({'is_student': True})

    def action_make_mother(self):
        """Convert female person to mother"""
        for record in self:
            if record.gender != 'f':
                raise ValidationError(_("Only female persons can be converted to mother."))
            record.parent_role = 'mother'

    def action_make_father(self):
        """Convert male person to father"""
        for record in self:
            if record.gender != 'm':
                raise ValidationError(_("Only male persons can be converted to father."))
            record.parent_role = 'father'

    def action_remove_father_role(self):
        """Remove father role if no active children"""
        for record in self:
            if record.parent_role == 'father':
                if record.children_count > 0:
                    raise ValidationError(_("Cannot remove father role: This person has active children."))
                record.parent_role = False

    def action_remove_mother_role(self):
        """Remove mother role if no active children"""
        for record in self:
            if record.parent_role == 'mother':
                if record.children_count > 0:
                    raise ValidationError(_("Cannot remove mother role: This person has active children."))
                record.parent_role = False

    def action_remove_teacher_role(self):
        """Remove teacher role if no active students or classes"""
        self.write({'is_teacher': False, 'class_ids': False, 'teacher_salary': 0.0})

    def action_remove_student_role(self):
        """Remove student role if no active assignments"""
        self.write({'is_student': False,'office_id': False,'class_id': False,'teacher_id': False,'subscription_fee': 0.0})

    def action_set_person_as_fatherless(self):
        """Set student as fatherless"""
        self.is_fatherless = True
        return True
    
    def action_set_person_not_fatherless(self):
        """Set student as not fatherless"""
        self.is_fatherless = False
        return True
    
    def action_view_children(self):
        """View children of this person (father or mother)"""
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
            'res_model': 'res.persons',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_father_id': self.id if self.parent_role == 'father' else False,
                'default_mother_id': self.id if self.parent_role == 'mother' else False,
            }
        }

    def action_open_update_person_data_wizard(self):
        return {
            'name': _('Update person Data Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.person.data.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'is_student': self._context.get('default_is_student', False),
                'is_teacher': self._context.get('default_is_teacher', False),
            }
        }

############################## Helper Functions #############################################
    def validate_status_of_student(self):
        """Check student status"""
        self.ensure_one()

        if not self.is_student:
            raise ValidationError(
                _('This person is not a student (%s).') % self.name)
        if self.status == 'disconnected':
            raise ValidationError(
                _('This student is disconnected (%s).') % self.name)
        if not self.active:
            raise ValidationError(
                _('This student is not active (%s).') % self.name)


