from odoo import models, fields

class PosCategory(models.Model):
    _inherit = 'pos.category'
    
    garista_category_id = fields.Char(string="Garista Category ID")
    
class PosProduct(models.Model):
    _inherit = 'product.template'
    
    garista_product_id = fields.Char(string="Garista Product ID")

class PosProductAttributes(models.Model):
    _inherit = 'product.attribute'
    
    garista_attribute_id = fields.Char(string="Garista Attribute ID")    

   
class PosShop(models.Model):
    _inherit = 'pos.config'
    
    garista_restaurant_id = fields.Char(string="Garista Restaurant ID")
    
class PosTable(models.Model):
    _inherit = 'restaurant.table'
    
    garista_table_id = fields.Char(string="Garista Table ID")
    
class PosOrder(models.Model):
    _inherit = "pos.order"

    garista_data = fields.Text("Garista API Data")
    garista_order_id = fields.Char(string="Garista Order ID")
    is_Sync = fields.Boolean(string="Garista Sync", default=False )