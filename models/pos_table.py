from odoo import models, fields
import requests

class RestaurantTable(models.Model):
    _inherit = 'restaurant.table'

    def get_api_headers(self):
        token = self.token
        return {
            "x-validate-api-token": token,
            "Content-Type": "application/json", 
            }
        
    def get_tables(self):
        api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
        
        if not api_url:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Please enter the API URL in Garista Settings first.',
                    'type': 'danger',
                    'sticky': True,
                }
            }

        api_url = api_url.rstrip('/') + '/'
        api_path = "tables/"
        user_restos_id = self.user_restos_id
        headers = self.get_api_headers()
        url = api_url + api_path + user_restos_id
        try:
            response = requests.get(url , headers=headers)
            if response.ok:
                items = response.json()
                model_vals = []

                for item in items:
                    model_vals.append({
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'resto_id': item.get('resto_id'),
                        'seats': item.get('seats'),
                        'locations': item.get('locations'),
                        'shape': item.get('shape'),
                        'staff_id': item.get('staff_id'),
                        'x': item.get('x'),
                        'y': item.get('y'),
                        'created_at': item.get('created_at'),
                        'updated_at': item.get('updated_at'),
                    })

                # Print extracted values
                print(model_vals)
            else:
                print(f"Error: {response.status_code}, {response.text}")

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f"Error: {str(e)}",
                    'type': 'danger',
                    'sticky': True,
                }
        }
        """ Automatically position tables in a grid layout when created. """
        # last_table = self.env['restaurant.table'].search([], order="id desc", limit=1)
        # row_limit = 6  # Max tables per row
        # spacing = 50  # Space between tables
        # width = 150
        # height = 150
        # name,seats,identifier,shape(square or round)
        # if last_table:
        #     new_x = last_table.horizontal_position + last_table.width + spacing  # Move right
        #     new_y = last_table.vertical_position

        #     # If row is full, move to a new row
        #     table_count = self.search_count([])
        #     if table_count % row_limit == 0:
        #         new_x = 10  # Reset to left side
        #         new_y += last_table.height + spacing  # Move down

        #     horizontal_position= new_x
        #     vertical_position = new_y
        # else:
        #     horizontal_position= new_x
        #     vertical_position = new_y

        # category_vals = {'name':name, 'image_128':image_base64, 'garista_category_id': garista_category_id}
        # category_id = self.env['pos.category'].create(category_vals)








