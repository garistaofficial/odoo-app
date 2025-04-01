from odoo import models, fields

class ApiSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    
    api_url = fields.Char(
        string="API URL",
        config_parameter='garista.api_url',
        help="Enter Garista API Endpoint"
    )