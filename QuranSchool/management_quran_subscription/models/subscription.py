# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.tools import format_date


class MonthlySubscription(models.Model):
    _name = 'monthly.subscription'
    _inherit = ['school.organization.mixin']
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
    office_id = fields.Many2one(ondelete='restrict')
    
    subscription_fee = fields.Monetary(string='Subscription Fee' ,currency_field='currency_id', compute='_compute_expected_amount', store=True)
    discount_percentage_fee = fields.Float(string='Discount %', compute='_compute_expected_amount', store=True)
    expected_amount = fields.Monetary(string='Expected Amount',compute='_compute_expected_amount',currency_field='currency_id',store=True,)
    # Payment Information
    paid_amount = fields.Monetary(string='Paid Amount',currency_field='currency_id')
    remaining_amount = fields.Monetary(string='Remaining Amount',compute='_compute_remaining_amount', currency_field='currency_id',store=True,)
    payment_voucher_number = fields.Char(string='Payment Voucher Number',help="Voucher number for this payment")
    currency_id = fields.Many2one(
            'res.currency',
            'Currency',
            required=True,
            default=lambda self: self.env.company.currency_id,
            help="Currency for subscription fee"
        )
    notes = fields.Text(string='Notes')

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
            record.remaining_amount = (record.expected_amount or 0.0) - (record.paid_amount or 0.0)
    
    @api.depends('subscription_month')
    @api.depends_context('lang')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.subscription_month:
                record.month_name = format_date(self.env, record.subscription_month, date_format='MMMM yyyy')
            else:
                record.month_name = ''

# ========================= constraints Functions =========================
    @api.constrains('student_id', 'subscription_month', 'office_id')
    def _check_duplicate_subscription(self):
        """Check for duplicate subscription for the same student in the same month and office"""
        for record in self:
            if not record.student_id or not record.subscription_month or not record.office_id:
                continue

            month_start = record.subscription_month.replace(day=1)
            month_end = (month_start + relativedelta(months=1))

            domain = [
                ('student_id', '=', record.student_id.id),
                ('office_id', '=', record.office_id.id),
                ('subscription_month', '>=', month_start),
                ('subscription_month', '<', month_end),
                ('id', '!=', record.id),
            ]

            if self.search_count(domain):
                raise ValidationError(_(
                    'This student already has a subscription '
                    'for this office in the selected month!'))
        
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
            if record.paid_amount < 0:
                raise ValidationError(_('Subscription not allowed with negative paid amount. Please enter a valid amount.'))
            if record.paid_amount == 0 and record.discount_percentage_fee < 100:
                raise ValidationError(_('Subscription not allowed with zero paid amount unless discount is 100%. Please enter a valid amount or adjust the discount.'))
    
   # ======================= Action Functions =======================

