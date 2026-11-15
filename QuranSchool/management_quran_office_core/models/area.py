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
    
    partner_count = fields.Integer(
        'Number of Partners',
        compute='_compute_partner_count',
        store=True,
        help="Total number of partners in this area"
    )
    
    # Relationships
    partner_ids = fields.One2many(
        'res.partner',
        'area_id',
        'Partners',
        help="Partners located in this area"
    )


    _sql_constraints = [('name_uniq', "unique(name)", "Name must be unique per area."),]
    
############################## Builtin Functions #############################################
    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate registration number automatically."""
        for vals in vals_list:
            vals['code'] = self.env['ir.sequence'].next_by_code('quran.office.area')

        return super().create(vals_list)

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Override _compute_display_name to show code and name."""
        for area in self:
            area.display_name = f"[{area.code}] {area.name}"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search to find areas by name or code."""
        if name == '':
            return super().name_search(name, args, operator, limit)
        
        if args is None:
            args = []
            
        # Search by code first
        domain = [('code', operator, name)]
        areas = self.search(domain + args, limit=limit)
        if areas:
            return [(record.id, record.display_name) for record in areas]
        
        # Then search by name
        domain = [('name', operator, name)]
        areas = self.search(domain + args, limit=limit)
        if areas:
            return [(record.id, record.display_name) for record in areas]

        return super().name_search(name, args, operator, limit)

############################## Compute Fields #########################################################
    @api.depends('partner_ids')
    def _compute_partner_count(self):
        """Compute the number of partners in this area."""
        for area in self:
            area.partner_count = len(area.partner_ids)

############################## Actions Functions #############################################
    def action_view_partners(self):
        """Action to view partners in this area."""
        self.ensure_one()
        action = self.env.ref('base.action_partner_tree_view2').read()[0]
        action['domain'] = [('area_id', '=', self.id)]
        action['context'] = {'default_area_id': self.id}
        return action
