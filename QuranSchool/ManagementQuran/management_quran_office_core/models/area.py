# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class Area(models.Model):
    _name = 'quran.office.area'
    _description = 'Area/District'
    _order = 'name asc'

    name = fields.Char(
        'Name',
        required=True,
        help="Name of the area/district"
    )
    code = fields.Char('Code', help="Unique code for the area",readonly=True)
    
    description = fields.Text(
        'Description',
        help="Additional information about the area"
    )
    
    active = fields.Boolean(
        'Active',
        default=True,
        help="If unchecked, this area will not be available for selection"
    )
    
    person_count = fields.Integer(
        'Number of persons',
        compute='_compute_person_count',
        store=True,
        help="Total number of persons in this area"
    )
    
    # Relationships
    person_ids = fields.One2many(
        'res.persons',
        'area_id',
        'persons',
        help="persons located in this area"
    )


    _sql_constraints = [('name_uniq', "unique(name)", "Name must be unique per area."),]
    _rec_names_search = ['code', 'name']
    
############################## Builtin Functions #############################################
    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate registration number automatically."""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('quran.office.area')

        return super().create(vals_list)

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Override _compute_display_name to show code and name."""
        for area in self:
            area.display_name = f"[{area.code}] {area.name}"

############################## Compute Fields #########################################################
    @api.depends('person_ids')
    def _compute_person_count(self):
        """Compute the number of persons in this area."""
        for area in self:
            area.person_count = len(area.person_ids)

############################## Actions Functions #############################################
    def action_view_persons(self):
        """Action to view persons in this area."""
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.res_persons_tree_view_quran_office').read()[0]
        action['domain'] = [('area_id', '=', self.id)]
        action['context'] = {'default_area_id': self.id}
        return action
