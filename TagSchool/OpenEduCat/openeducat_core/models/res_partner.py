# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .utils import (fnc_editstring, get_birth_date_from_national_id, get_gender_from_national_id,
                     is_invalid_national_id, get_age, get_detailed_age)


class StudentPortal(models.Model):
    _inherit = 'res.partner'

    # Basic identification fields
    first_name = fields.Char(
        'First Name',
        translate=True,
        help="Student's first name"
    )
    middle_name = fields.Char(
        'Middle Name',
        required=True,
        translate=True,
        help="Student's middle name (optional)"
    )
    last_name = fields.Char(
        'Last Name',
        required=True,
        translate=True,
        help="Student's last name"
    )

    # Computed fields
    edited_name = fields.Char(
        'Edited Name',
        compute='_compute_edited_name',
        store=True,
        help="Student name with Arabic character normalization"
    )

    age_from_id = fields.Char(
        'Detailed Age',
        compute='_compute_age_from_id',
        store=True,
        help="Detailed age (years, months, days) calculated from national ID"
    )

    age_years = fields.Integer(
        'Age (Years)',
        compute='_compute_age_from_id',
        store=True,
        help="Age in years for filtering purposes"
    )

    # Official identification
    id_number = fields.Char(
        'ID Card Number',
        size=20,
        help="National ID or passport number"
    )

    # Personal information
    birth_date = fields.Date(
        'Birth Date',
        help="Student's date of birth"
    )

    gender = fields.Selection([
        ('m', 'Male'),
        ('f', 'Female'),
    ], 'Gender', required=True, default='m', help="Student's gender")

    country_id = fields.Many2one(default=lambda self: self.env.ref('base.eg'), )

    emergency_contact = fields.Many2one(
        'res.partner',
        'Emergency Contact',
        help="Emergency contact person"
    )

    # STUDENT ========== Academic relationships ===========================================
    course_detail_ids = fields.One2many(
        'op.student.course',
        'student_id',
        'Course Details',
        tracking=True,
        help="Enrolled courses and academic details"
    )

    # FACULTY ========== Academic relationships ===========================================
    # System integration fields
    login = fields.Char(
        'Login',
        related='user_id.login',
        readonly=True,
        help="Faculty login credentials"
    )
    last_login = fields.Datetime(
        'Latest Connection',
        readonly=True,
        related='user_id.login_date',
        help="Last login date and time"
    )
    # Academic fields
    faculty_subject_ids = fields.Many2many(
        'op.subject',
        string='Subject(s)',
        tracking=True,
        help="Subjects taught by this faculty member"
    )
    emp_id = fields.Many2one(
        'hr.employee',
        'HR Employee',
        help="Related HR employee record"
    )
    # Department fields
    main_department_id = fields.Many2one(
        'op.department',
        'Main Department',
        default=lambda self: self.env.user.dept_id and self.env.user.dept_id.id or False,
        help="Primary department of the faculty member"
    )
    allowed_department_ids = fields.Many2many(
        'op.department', string='Allowed Department',
        default=lambda self:
        self.env.user.department_ids and self.env.user.department_ids.ids or False)
    #====================================================================================================

    is_parent = fields.Boolean("Is a Parent")
    is_student = fields.Boolean("Is a Student")
    is_faculty = fields.Boolean("Is a Faculty")

    ############################## Constraints And Validation #############################################
    @api.constrains('id_number')
    def _check_unique_id_number(self):
        """
        Check if ID number is unique when provided.
        """
        for record in self:
            if record.id_number and is_invalid_national_id(record.id_number):
                raise ValidationError(_(
                    "Invalid Egyptian National ID format! "
                    "Please enter a valid 14-digit national ID number."))
            if record.id_number:
                duplicates = self.search([('id_number', '=', record.id_number), ('id', '!=', record.id),
                                          ('active', 'in', ['True', 'False'])])
                if duplicates:
                    raise ValidationError(_('ID Card Number must be unique per student!'))

    @api.constrains('edited_name')
    def _check_unique_edited_name(self):
        """
        Check if edited name is unique when provided.
        """
        for record in self:
            if record.edited_name:
                duplicates = self.search([('edited_name', '=', record.edited_name), ('id', '!=', record.id),
                                          ('active', 'in', ['True', 'False'])])
                if duplicates:
                    raise ValidationError(_('Edited Name must be unique per student!'))

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """
        Validate that birth date is not in the future.
        """
        for record in self:
            if record.birth_date and record.birth_date > fields.Date.today():
                raise ValidationError(_(
                    "Birth Date can't be greater than current date!"))

    ############################## Onchange Functions #############################################

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_name(self):
        """
        Automatically update the partner name when name fields change.
        This ensures consistency between student and partner records.
        """
        if self.first_name and self.last_name:
            if self.middle_name:
                self.name = f"{self.first_name} {self.middle_name} {self.last_name}"
            else:
                self.name = f"{self.first_name} {self.last_name}"

    @api.onchange('id_number')
    def _onchange_id_number(self):
        """
        Auto-fill birth_date and gender from national ID.
        """
        if self.id_number and not is_invalid_national_id(self.id_number):
            try:
                # Auto-fill birth date
                birth_date = get_birth_date_from_national_id(self.id_number)
                self.birth_date = birth_date

                # Auto-fill gender
                gender_code = get_gender_from_national_id(self.id_number)
                self.gender = gender_code
            except:
                pass

    ############################## Compute Fields #########################################################

    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_edited_name(self):
        """
        Compute edited name with Arabic character normalization.
        """
        for student in self:
            full_name = ""
            if student.first_name:
                full_name += student.first_name
            if student.middle_name:
                full_name += " " + student.middle_name
            if student.last_name:
                full_name += " " + student.last_name

            student.edited_name = fnc_editstring(full_name)

    @api.depends('id_number', 'birth_date')
    def _compute_age_from_id(self):
        """
        Compute age from national ID or birth date using unified functions.
        """
        for student in self:
            try:
                # Use unified functions that handle both ID and birth date
                student.age_from_id = get_detailed_age(national_id=student.id_number, birth_date=student.birth_date)
                student.age_years = get_age(national_id=student.id_number, birth_date=student.birth_date)
            except:
                student.age_from_id = _("Not specified")
                student.age_years = 0

    ############################## Bulitin Functions #############################################

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to generate registration number automatically.
        """
        for vals in vals_list:
            # Generate registration number if not provided
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('op.student')

        return super(OpStudent, self).create(vals_list)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Enhanced name search to find students by name or registration number.
        """
        if name:
            # Search by registration number first
            domain = [('ref', operator, name)]
            students = self.search(domain + (args or []), limit=limit)
            if students:
                return students.name_get()

            # Then search by name
            domain = [('name', operator, name)]
            students = self.search(domain + (args or []), limit=limit)
            if students:
                return students.name_get()

        return super(OpStudent, self).name_search(name, args, operator, limit)

    ############################## Actions Functions #############################################

    @api.model
    def get_import_templates_student(self):
        """
        Return import template configuration for student data.
        """
        return [{
            'label': _('Import Template for Students'),
            'template': '/openeducat_core/static/xls/op_student.xls'
        }]

    def create_student_user(self):
        """
        Create portal user account for the student.
        Uses student's inherited email field for login credentials.
        """
        portal_group = self.env.ref("base.group_portal")
        if not portal_group:
            raise ValidationError(_("Portal group not found!"))

        for student in self:
            if not student.user_id and student.email:
                # Create user account with portal access
                user_vals = {
                    'name': student.name,
                    'partner_id': student.id,
                    'login': student.email,
                    'groups_id': [(4, portal_group.id)],
                    'is_student': True,
                    'tz': self._context.get('tz') or 'UTC',
                    'company_id': student.company_id.id if student.company_id else False,
                }
                user_id = self.env['res.users'].create(user_vals)
                student.user_id = user_id

    def create_employee(self):
        for record in self:
            vals = {
                'name': record.name,
                'country_id': record.country_id.id,
                'gender': record.gender,
            }
            emp_id = self.env['hr.employee'].create(vals)
            record.write({'emp_id': emp_id.id})
            record.partner_id.write({'partner_share': True, 'employee': True})

    @api.model
    def get_import_templates_faculty(self):
        """
        Return import templates for faculty data.

        Returns:
            list: List of import template configurations
        """
        return [{
            'label': _('Import Template for Faculties'),
            'template': '/openeducat_core/static/xls/op_faculty.xls'
        }]
