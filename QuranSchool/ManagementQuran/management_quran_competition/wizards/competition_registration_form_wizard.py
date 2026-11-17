# -*- coding: utf-8 -*-

from odoo import fields, models, api,_
from odoo.exceptions import ValidationError,UserError


class CompetitionRegistrationFormWizard(models.TransientModel):
    _name = 'competition.registration.form.wizard'
    _description = 'Competition Registration Form Wizard'

    competition_id = fields.Many2one(
        'quran.competition',
        string='Competition',
        required=True,
        domain="[('status', '=', 'opening')]",
        help='Competition for which the blank registration form will be printed'
    )
    copies = fields.Integer(
        string='Number of Copies',
        default=1,
        help='How many blank registration sheets to print'
    )

    @api.model
    def default_get(self, fields):
        res = super(CompetitionRegistrationFormWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            res['competition_id'] = active_id
        return res


    def action_print_blank_registration_form(self):
        self.ensure_one()
        if not self.competition_id:
            raise ValidationError(_('Please select a competition before printing.'))

        if not 1 <= self.copies <= 100:
            raise UserError(
                _('Number of copies must be between 1 and 100.')
            )

        return self.env.ref(
            'management_quran_competition.report_blank_participant_registration_form'
        ).report_action(
            self.id,
            data={'copies': self.copies,
                   'competition_name': self.competition_id.name}
        )
