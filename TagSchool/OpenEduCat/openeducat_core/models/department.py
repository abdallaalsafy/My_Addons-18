from odoo import api, fields, models


class OpDepartment(models.Model):
    _name = "op.department"
    _description = "OpenEduCat Department"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    parent_id = fields.Many2one('op.department', 'Parent Department')

    @api.model_create_multi
    def create(self, vals):
        department = super(OpDepartment, self).create(vals)
        self.env.user.write({'department_ids': [(4, department.id)]})
        return department
