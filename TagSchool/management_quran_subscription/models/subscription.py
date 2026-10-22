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
        string='Office',
    )
    
    class_id = fields.Many2one(
        'quran_office.class',
        string='Class',
        domain="[('office_id', '=?', office_id)]",
    )
    
    teacher_id = fields.Many2one(
        'res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]"
    )
    
    subscription_fee = fields.Float(
        string='Subscription Fee',
        readonly=True,
        digits=(16, 2)
    )
    
    discount_percentage_fee = fields.Float(
        string='Discount Percentage',
        readonly=True,
        digits=(5, 2)
    )
    
    # Payment Information
    paid_amount = fields.Float(
        string='Paid Amount',
        required=True,
        digits=(16, 2)
    )
    
    remaining_amount = fields.Float(
        string='Remaining Amount',
        compute='_compute_remaining_amount',
        store=True,
        digits=(16, 2),
        readonly=True
    )

    expected_amount = fields.Float(
        string='Expected Amount',
        compute='_compute_expected_amount',
        store=True,
        readonly=True,
        digits=(16, 2),
    )
    
    # Subscription Month
    subscription_month = fields.Date(
        string='Subscription Month',
        required=True,
        default=lambda self: fields.Date.today(),
        help="Month and year for this subscription"
    )
    
    month_name = fields.Char(
        string='Month Name',
        compute='_compute_month_name',
        store=True,
        readonly=True
    )
    
    # Payment Details
    payment_voucher_number = fields.Char(
        string='Payment Voucher Number',
        help="Voucher number for this payment"
    )
    
    notes = fields.Text(
        string='Notes'
    )

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

            self.subscription_fee = self.student_id.subscription_fee
            self.discount_percentage_fee = self.student_id.discount_percentage_fee
            # Set paid_amount to expected amount as default value
            if self.subscription_fee:
                self.paid_amount = self.expected_amount
            else:
                self.paid_amount = 0
        else:
            self.subscription_fee = 0
            self.discount_percentage_fee = 0
            self.paid_amount = 0

    @api.onchange('office_id')
    def _onchange_office_id(self):
        """
        Clear class_id and teacher_id when office changes to ensure proper filtering.
        """
        if (self.office_id and self.office_id != self.class_id.office_id) or not self.office_id:
            self.class_id = False

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """
        Auto-fill teacher_id when class is selected.
        """
        if self.class_id:
            self.office_id = self.class_id.office_id
        if self.class_id and self.class_id.teacher_id:
            self.teacher_id = self.class_id.teacher_id

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        if self.teacher_id and not self.class_id:
            self.class_id = self.teacher_id.class_ids[0]

    # ========================= constraints Functions =========================

    @api.constrains('subscription_month')
    def _check_future_month(self):
        """Check that subscription month is not in the future"""
        for record in self:
            if record.subscription_month:
                current_month = fields.Date.today()
                subscription_month = record.subscription_month
                if subscription_month > current_month:
                    raise ValidationError(_('Cannot create subscription for future month %s') % record.month_name)

    @api.constrains('student_id')
    def _check_student_status(self):
        """Check student status before allowing subscription"""
        for record in self:
            if record.student_id:
                # Check if student is disconnected
                if record.student_id.student_status == 'disconnected':
                    raise ValidationError(
                        _('Cannot create subscription for disconnected student %s. Please update student status first.') % record.student_id.name)

                # Check if student is active
                if not record.student_id.active:
                    raise ValidationError(
                        _('Cannot create subscription for inactive student %s.') % record.student_id.name)

                if not record.student_id.is_student:
                    raise ValidationError(
                        _('Cannot create subscription for non-student %s.') % record.student_id.name)

    @api.constrains('paid_amount', 'expected_amount')
    def _check_payment_amount(self):
        """Check payment amount and show warning if different from expected"""
        for record in self:
            # Check that paid amount is greater than zero
            if record.paid_amount <= 0:
                raise ValidationError(_('Subscription amount must be greater than zero'))

    @api.constrains('student_id', 'subscription_month')
    def _check_unique_subscription_per_month(self):
        """Check that student doesn't have more than one subscription per month"""
        for record in self:
            if record.student_id and record.subscription_month:
                # Check for existing subscription for same student and month
                existing = self.search([
                    ('student_id', '=', record.student_id.id),
                    ('subscription_month', '=', record.subscription_month),
                    ('id', '!=', record.id),
                ])
                if existing:
                    raise ValidationError(_('Student %s already has a subscription for %s') % (
                        record.student_id.name,
                        record.month_name or record.subscription_month.strftime('%B %Y')
                    ))

    # ========================= compute Functions =========================

    @api.depends('subscription_fee', 'discount_percentage_fee')
    def _compute_expected_amount(self):
        """Compute expected amount after discount"""
        for record in self:
            if record.subscription_fee:
                # we dont divide by 100 because it is already a percentage
                # the field use widget='percent' which divide by 100
                #discount_amount = record.subscription_fee * (record.discount_percentage_fee)/100
                discount_amount = record.subscription_fee * (record.discount_percentage_fee)
                record.expected_amount = record.subscription_fee - discount_amount
            else:
                record.expected_amount = 0
    
    @api.depends('paid_amount', 'expected_amount')
    def _compute_remaining_amount(self):
        """Compute remaining amount"""
        for record in self:
            if record.subscription_fee:
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
    
   # ======================= Action Functions =======================

