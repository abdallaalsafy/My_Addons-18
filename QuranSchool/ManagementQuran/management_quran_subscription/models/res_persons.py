# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ResPersonsExtension(models.Model):
    _inherit = 'res.persons'

    subscription_ids = fields.One2many(
        'monthly.subscription',
        'student_id',
        'Subscriptions',
        help="Subscriptions in this student"
    )

    # Subscription count for students
    subscription_count = fields.Integer(
        'Subscription Count',
        compute='_compute_subscription_count',
        help="Number of subscriptions for this student (only shown for students)"
    )


# ========================= Compute Functions =========================
    def _compute_subscription_count(self):
        """Compute the number of subscriptions for this student (only for students)"""
        for record in self:
            record.subscription_count = len(record.subscription_ids)

# ========================= Action Functions =========================
    def action_fast_create_subscription(self):
        """Fast create subscription for students in current month"""
        current_month = fields.Date.today()
        data_list = []
        for student in self:
            student.validate_student_for_subscription()
            data_list.append({
                'student_id': student.id,
                'subscription_month': current_month,
                'office_id': student.office_id.id,
                'class_id': student.class_id.id,
                'teacher_id': student.teacher_id.id,
                'paid_amount': student.get_subscription_expected_amount(),
            })
        self.env['monthly.subscription'].create(data_list)

    def action_view_subscriptions(self):
        """View subscriptions of this student"""
        self.ensure_one()
        name = _('Subscriptions of %s') % self.name
        domain = [('student_id', '=', self.id)]
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.subscription',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'default_student_id': self.id,}
        }

# ========================= Helper Functions =========================
    def get_subscription_expected_amount(self):
        self.ensure_one()
        discount_amount = self.subscription_fee * self.discount_percentage_fee / 100
        return self.currency_id.round(self.subscription_fee - discount_amount) if self.currency_id \
            else self.subscription_fee - discount_amount

    def validate_student_for_subscription(self, office=None, subscription_fee=None):
        """Check student status before allowing subscription"""
        self.ensure_one()

        self.validate_status_of_student()
        
        office = office or self.office_id
        subscription_fee = subscription_fee or self.subscription_fee

        if not office:
            raise ValidationError(
                _('Cannot create subscription for student (%s) without office.') % self.name)
        if subscription_fee <= 0:
            raise ValidationError(
                _('Cannot create subscription for student (%s) with zero subscription fee.') % self.name)


