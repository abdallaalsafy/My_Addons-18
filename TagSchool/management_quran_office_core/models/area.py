# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Area(models.Model):
    _name = 'quran_office.area'
    _description = 'Area/District'
    _order = 'name asc'

    name = fields.Char(
        'Area Name',
        required=True,
        help="Name of the area/district"
    )
    
    code = fields.Char(
        'Area Code',
        help="Unique code for the area"
    )
    
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

    @api.depends('partner_ids')
    def _compute_partner_count(self):
        """
        Compute the number of partners in this area.
        """
        for area in self:
            area.partner_count = len(area.partner_ids)

    @api.constrains('code')
    def _check_unique_code(self):
        """
        Ensure area code is unique.
        """
        for area in self:
            if area.code:
                duplicates = self.search([
                    ('code', '=', area.code),
                    ('id', '!=', area.id)
                ])
                if duplicates:
                    raise ValidationError(_(
                        "Area Code must be unique! This code is already used."))

    @api.constrains('name')
    def _check_unique_name(self):
        """
        Ensure area name is unique.
        """
        for area in self:
            if area.name:
                duplicates = self.search([
                    ('name', '=', area.name),
                    ('id', '!=', area.id)
                ])
                if duplicates:
                    raise ValidationError(_(
                        "Area Name must be unique! This name is already used."))

    def name_get(self):
        """
        Override name_get to show code and name.
        """
        result = []
        for area in self:
            if area.code:
                name = f"[{area.code}] {area.name}"
            else:
                name = area.name
            result.append((area.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Enhanced name search to find areas by name or code.
        """
        if name == '':
            return super().name_search(name, args, operator, limit)
        
        if args is None:
            args = []
            
        # Search by code first
        domain = [('code', operator, name)]
        areas = self.search(domain + args, limit=limit)
        if areas:
            return areas.name_get()
        
        # Then search by name
        domain = [('name', operator, name)]
        areas = self.search(domain + args, limit=limit)
        if areas:
            return areas.name_get()

        return super().name_search(name, args, operator, limit)

    def action_view_partners(self):
        """
        Action to view partners in this area.
        """
        self.ensure_one()
        action = self.env.ref('base.action_partner_tree_view2').read()[0]
        action['domain'] = [('area_id', '=', self.id)]
        action['context'] = {'default_area_id': self.id}
        return action
