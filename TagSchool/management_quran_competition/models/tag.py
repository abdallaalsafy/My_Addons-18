# -*- coding: utf-8 -*-

from random import randint

from odoo import fields, models


class QuranCompetitionTag(models.Model):
    _name = 'quran.competition.tag'
    _description = 'Quran Competition Tag'
    _order = 'name'


    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(
        string='Tag Name',
        required=True,
        translate=True,
        help="Name of the competition tag"
    )
    color = fields.Integer(
        string='Color Index',
        default=_get_default_color,
        help="Color index for the tag"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="If unchecked, this tag will be hidden"
    )
