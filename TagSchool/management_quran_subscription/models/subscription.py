# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import calendar

class MonthlySubscription(models.Model):
    _name = 'monthly.subscription'
    _description = 'Monthly Student Subscription'
    _order = 'subscription_month desc, student_id'

    # Sequence Details
    name = fields.Char(
        string='Subscription Number',
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    subscription_month = fields.Date(
            string='Subscription Month',
            required=True,
            default=lambda self: fields.Date.today(),
            help="Month and year for this subscription"
        )
    month_name = fields.Char(string='Month Name',compute='_compute_month_name',store=True,)

    # Basic Information
    student_id = fields.Many2one(
        'res.partner', 
        string='Student Name',
        required=True,
        domain="[('is_student', '=', True)]"
    )
    
    # Related Fields (computed from student)
    office_id = fields.Many2one(
        'quran.office.office',
        required=True,
        string='Office',
    )
    class_id = fields.Many2one(
        'quran.office.class',
        string='Class',
        domain="[('office_id', '=?', office_id)]",
    )
    teacher_id = fields.Many2one(
        'res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]"
    )
    
    subscription_fee = fields.Monetary(string='Subscription Fee' ,currency_field='currancy_id', compute='_compute_expected_amount', store=True)
    discount_percentage_fee = fields.Float(string='Discount %', compute='_compute_expected_amount', store=True)
    expected_amount = fields.Monetary(string='Expected Amount',compute='_compute_expected_amount',currency_field='currancy_id',store=True,)
    # Payment Information
    paid_amount = fields.Monetary(string='Paid Amount',currency_field='currancy_id')
    remaining_amount = fields.Monetary(string='Remaining Amount',compute='_compute_remaining_amount', currency_field='currancy_id',store=True,)
    payment_voucher_number = fields.Char(string='Payment Voucher Number',help="Voucher number for this payment")
    currancy_id = fields.Many2one(
            'res.currency',
            'Currency',
            required=True,
            default=lambda self: self.env.company.currency_id,
            help="Currency for subscription fee"
        )
    notes = fields.Text(string='Notes')

    _sql_constraints = [('subscription_uniq', "unique(student_id,subscription_month,office_id)", "Subscription must be unique per student per month per office.")]

# ========================= Built-in Functions =========================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence for subscription number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('monthly.subscription.number.alt') or _('New')
        
        return super().create(vals_list)

    # ========================= OnChange Functions =========================
    @api.onchange('student_id')
    def _onchange_student_id(self):
        """When student changes, populate subscription fee and discount percentage"""
        if self.student_id:
            self.office_id = self.student_id.office_id
            self.class_id = self.student_id.class_id
            self.teacher_id = self.student_id.teacher_id
            self.paid_amount = self.student_id.get_subscription_expected_amount()

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

# ========================= compute Functions =========================
    @api.depends('student_id')
    def _compute_expected_amount(self):
        """Compute expected amount after discount"""
        for record in self:
            if record.student_id:
                record.expected_amount = record.student_id.get_subscription_expected_amount()
                record.subscription_fee = record.student_id.subscription_fee
                record.discount_percentage_fee = record.student_id.discount_percentage_fee
            else:
                record.expected_amount = 0
                record.subscription_fee = 0
                record.discount_percentage_fee = 0
    
    @api.depends('paid_amount', 'expected_amount')
    def _compute_remaining_amount(self):
        """Compute remaining amount"""
        for record in self:
            if record.expected_amount:
                record.remaining_amount = record.expected_amount - record.paid_amount
            else:
                record.remaining_amount = 0
    
    @api.depends('subscription_month')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.subscription_month:
                record.month_name = record.subscription_month.strftime('%B %Y')
            else:
                record.month_name = ''

# ========================= constraints Functions =========================
    @api.constrains('subscription_month')
    def _check_subscription_month(self):
        """Check that subscription month is not in the future"""
        for record in self:
            if record.subscription_month:
                if record.subscription_month > fields.Date.today():
                    raise ValidationError(_('Cannot create subscription for future month %s') % record.month_name)

    @api.constrains('student_id')
    def _check_student_status(self):
        """Check student status before allowing subscription"""
        for record in self:
            if not record.student_id:
                raise ValidationError(_('Please select a student first.'))
            record.student_id.validate_status_of_student()

    @api.constrains('paid_amount')
    def _check_payment_amount(self):
        """Check payment amount and show warning if different from expected"""
        for record in self:
            # Check that paid amount is greater than zero
            if record.paid_amount <= 0:
                raise ValidationError(_('Subscription amount must be greater than zero'))
    
   # ======================= Action Functions =======================

