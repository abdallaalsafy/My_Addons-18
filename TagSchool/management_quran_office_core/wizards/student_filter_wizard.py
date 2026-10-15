# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StudentFilterWizard(models.TransientModel):
    _name = 'student.filter.wizard'
    _description = 'Advanced Student Filter Wizard'

    # Office filtering
    office_id = fields.Many2one(
        'quran_office.office',
        'Office',
        help="Filter by office or leave empty to include all"
    )
    has_office = fields.Selection([
        ('with_office', 'Has Office'),
        ('without_office', 'Without Office'),
    ], 'Office Filter')

    # Class filtering
    class_id = fields.Many2one(
        'quran_office.class',
        'Class',
        domain="[('office_id', '=?', office_id)]",
        help="Filter by class or leave empty to include all"
    )
    has_class = fields.Selection([
        ('with_class', 'Has Class'),
        ('without_class', 'Without Class'),
    ], 'Class Filter')

    # Teacher filtering
    teacher_id = fields.Many2one(
        'res.partner',
        'Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Filter by teacher or leave empty to include all"
    )
    has_teacher = fields.Selection([
        ('with_teacher', 'Has Teacher'),
        ('without_teacher', 'Without Teacher'),
    ], 'Teacher Filter')

    # Status filtering
    student_status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
    ], 'Student Status')

    # Parent filtering
    father_id = fields.Many2one(
        'res.partner',
        'Father',
        domain="[('parent_role', '=', 'father')]",
        help="Filter by father or leave empty to include all"
    )
    has_father = fields.Selection([
        ('with_father', 'Has Father'),
        ('without_father', 'Without Father'),
    ], 'Father Filter')

    mother_id = fields.Many2one(
        'res.partner',
        'Mother',
        domain="[('parent_role', '=', 'mother')]",
        help="Filter by mother or leave empty to include all"
    )
    has_mother = fields.Selection([
        ('with_mother', 'Has Mother'),
        ('without_mother', 'Without Mother'),
    ], 'Mother Filter')

    # Identification filtering
    id_number = fields.Char(
        'ID Number',
        help="Filter by ID number or leave empty to include all"
    )
    has_id_number = fields.Selection([
        ('with_id', 'Has ID Number'),
        ('without_id', 'Without ID Number'),
    ], 'ID Number Filter')

    # Contact filtering
    phone = fields.Char(
        'Phone',
        help="Filter by phone number or leave empty to include all"
    )
    has_phone = fields.Selection([
        ('with_phone', 'Has Phone'),
        ('without_phone', 'Without Phone'),
    ], 'Phone Filter')

    # Gender filtering
    gender = fields.Selection([
        ('m', 'Male'),
        ('f', 'Female'),
    ], 'Gender')

    # Age filtering
    age_filter_type = fields.Selection([
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
    ], 'Age Filter Type')
    age_value = fields.Integer(
        'Age Value',
        help="Age value for filtering"
    )

    # Documents filtering
    has_personal_photo = fields.Selection([
        ('with_photo', 'Has Personal Photo'),
        ('without_photo', 'Without Personal Photo'),
    ], 'Personal Photo Filter')
    
    has_birth_certificate = fields.Selection([
        ('with_certificate', 'Has Birth Certificate'),
        ('without_certificate', 'Without Birth Certificate'),
    ], 'Birth Certificate Filter')
    
    has_id_card_front = fields.Selection([
        ('with_id_front', 'Has ID Card Front'),
        ('without_id_front', 'Without ID Card Front'),
    ], 'ID Card Front Filter')

    # Status filtering
    is_fatherless = fields.Selection([
        ('fatherless', 'Fatherless'),
        ('not_fatherless', 'Not Fatherless'),
    ], 'Fatherless Filter')
    
    is_quran_memorizer = fields.Selection([
        ('memorizer', 'Complete Quran Memorizer'),
        ('not_memorizer', 'Not Complete Quran Memorizer'),
    ], 'Quran Memorizer Filter')


    def calculate_filtered_students(self):
        """Compute filtered students based on all criteria"""
        wizard = self
        domain = [('is_student', '=', True)]

        # Office filtering
        if wizard.has_office == 'with_office':
            domain.append(('office_id', '!=', False))
        elif wizard.has_office == 'without_office':
            domain.append(('office_id', '=', False))
        elif wizard.office_id:
            domain.append(('office_id', '=', wizard.office_id.id))

        # Class filtering
        if wizard.has_class == 'with_class':
            domain.append(('class_id', '!=', False))
        elif wizard.has_class == 'without_class':
            domain.append(('class_id', '=', False))
        elif wizard.class_id:
            domain.append(('class_id', '=', wizard.class_id.id))

        # Teacher filtering
        if wizard.has_teacher == 'with_teacher':
            domain.append(('teacher_id', '!=', False))
        elif wizard.has_teacher == 'without_teacher':
            domain.append(('teacher_id', '=', False))
        elif wizard.teacher_id:
            domain.append(('teacher_id', '=', wizard.teacher_id.id))

        # Status filtering
        if wizard.student_status:
            domain.append(('student_status', '=', wizard.student_status))

        # Father filtering
        if wizard.has_father == 'with_father':
            domain.append(('father_name', '!=', False))
        elif wizard.has_father == 'without_father':
            domain.append(('father_name', '=', False))
        elif wizard.father_id:
            domain.append(('father_name', '=', wizard.father_id.id))

        # Mother filtering
        if wizard.has_mother == 'with_mother':
            domain.append(('mother_name', '!=', False))
        elif wizard.has_mother == 'without_mother':
            domain.append(('mother_name', '=', False))
        elif wizard.mother_id:
            domain.append(('mother_name', '=', wizard.mother_id.id))

        # ID Number filtering
        if wizard.has_id_number == 'with_id':
            domain.append(('id_number', '!=', False))
        elif wizard.has_id_number == 'without_id':
            domain.append(('id_number', '=', False))
        elif wizard.id_number:
            domain.append(('id_number', 'ilike', wizard.id_number))

        # Phone filtering
        if wizard.has_phone == 'with_phone':
            domain.extend(['|', ('phone', '!=', False), ('mobile', '!=', False)])
        elif wizard.has_phone == 'without_phone':
            domain.extend([('phone', '=', False), ('mobile', '=', False)])
        elif wizard.phone:
            domain.extend(['|', ('phone', 'ilike', wizard.phone), ('mobile', 'ilike', wizard.phone)])

        # Gender filtering
        if wizard.gender:
            domain.append(('gender', '=', wizard.gender))

        # Age filtering
        if wizard.age_filter_type == 'equals':
            domain.append(('age_years', '=', wizard.age_value))
        elif wizard.age_filter_type == 'greater_than':
            domain.append(('age_years', '>', wizard.age_value))
        elif wizard.age_filter_type == 'less_than':
            domain.append(('age_years', '<', wizard.age_value))

        # Documents filtering
        if wizard.has_personal_photo == 'with_photo':
            domain.append(('personal_photo', '!=', False))
        elif wizard.has_personal_photo == 'without_photo':
            domain.append(('personal_photo', '=', False))
            
        if wizard.has_birth_certificate == 'with_certificate':
            domain.append(('birth_certificate', '!=', False))
        elif wizard.has_birth_certificate == 'without_certificate':
            domain.append(('birth_certificate', '=', False))
            
        if wizard.has_id_card_front == 'with_id_front':
            domain.append(('id_card_front', '!=', False))
        elif wizard.has_id_card_front == 'without_id_front':
            domain.append(('id_card_front', '=', False))

        # Status filtering
        if wizard.is_fatherless == 'fatherless':
            domain.append(('is_fatherless', '=', True))
        elif wizard.is_fatherless == 'not_fatherless':
            domain.append(('is_fatherless', '=', False))
            
        if wizard.is_quran_memorizer == 'memorizer':
            domain.append(('is_quran_memorizer', '=', True))
        elif wizard.is_quran_memorizer == 'not_memorizer':
            domain.append(('is_quran_memorizer', '=', False))

        return self.env['res.partner'].search(domain)

    def action_show_filter_students(self):
        """Filter students and show results"""
        self.ensure_one()
        view_form = self.env.ref('management_quran_office_core.res_partner_form_view_quran_office').id
        view_list = self.env.ref('management_quran_office_core.res_partner_tree_view_quran_office').id
        return {
            'name': _('Filtered Students'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list',
            'views': [(view_list, 'list'),(view_form, 'form')],
            'domain':[('id','in',self.calculate_filtered_students().ids)],
            'context':{'default_is_student': True}
        }

    def action_print_results(self):
        """Print filtered students report"""
        self.ensure_one()
        records = self.calculate_filtered_students()

        if not records:
            raise ValidationError(_('No students found matching the criteria.'))

        return self.env.ref('management_quran_office_core.action_report_all_partners_basic_data').report_action(
            records.ids
        )
