# -*- coding: utf-8 -*-

from odoo import models, fields, api
import hashlib
import requests
import base64
import json
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import secrets, string
from datetime import datetime, timedelta



class garista(models.Model):
    _name = 'garista.garista'
    _description = 'garista.garista'

    name = fields.Char(string="Restaurants", default="Restaurant")
    api_email = fields.Char(string="Email" ,required=True , help="Api Login Email address")
    api_password = fields.Char(string="Password", required=True, help="Api Login Password address")
    api_token = fields.Char(string="API Token")
    token = fields.Char(string="Token")
    
    use_existing_restaurant = fields.Boolean(string="Use Existing Restaurant?")
    restaurant_id = fields.Many2one(
        'pos.config', 
        string="Select Restaurant"
    )


    
    # API response fields
    status = fields.Char(string="Status", help="Api Login Status")
    message = fields.Char(string="Message", help="Api Login Message")
    user_id = fields.Char(string="UserID",  help="Api Login UserID")
    user_first_name = fields.Char(string="FirstName" , help="FirstName")
    user_last_name = fields.Char(string="LastName" , help="LastName")
    user_phone = fields.Char(string="Phone",  help="Phone")
    user_username = fields.Char(string="Username" ,  help="Username") 
    user_restos_name = fields.Char(string="Restaurant Name",  help="Restaurant Name")
    user_restos_id = fields.Char(string="RestaurantID",  help="Restaurant ID")
    last_disconnect_timestamp = fields.Datetime(string="Last Disconnected", readonly=True)
    
    def validate_api_token(self, api_token, username):
        print("validate_api_token")
        garista = self.search([('api_email', '=', username), ('api_token', '=', api_token)], limit=1)

        if garista:
            return True
        else:
            return False
        
    def get_api_headers(self):
        return {
            "x-validate-api-token": self.token,
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json", 
            }
    
    def create_pos_config(self, model_vals):
        """Creates a new POS Config."""
        pos_config_vals = {
            'name': model_vals.get('name'),
            'module_pos_restaurant': True,
            'active': True,
            'garista_restaurant_id': model_vals.get('user_restos_id'),
            'journal_id': self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id
        }
        return self.env['pos.config'].create(pos_config_vals)

    def create_or_update_preparation_display(self, pos_config):
        """Creates or updates a Preparation Display for the given POS Config."""
        if not pos_config:
            print("⚠️ No POS Config provided. Skipping Preparation Display update.")
            return

        # ✅ Search for an existing Preparation Display linked to this POS Config
        prep_display = self.env['pos_preparation_display.display'].search([
            ('pos_config_ids', 'in', [pos_config.id])
        ], limit=1)

        # ✅ Define the required stages (always in correct order)
        stage_data = [
            {'name': 'Accepted', 'color': '#FFC107', 'alert_timer': 0},
            {'name': 'To prepare', 'color': '#6C757D', 'alert_timer': 10},
            {'name': 'Ready', 'color': '#4D89D1', 'alert_timer': 5},
            {'name': 'Served', 'color': '#4ea82a', 'alert_timer': 0},
        ]

        if prep_display:
            # ✅ Delete all existing stages
            prep_display.stage_ids.unlink()

            # ✅ Create new stages in the correct order
            stage_ids = [(0, 0, stage) for stage in stage_data]
            prep_display.write({'stage_ids': stage_ids})

            print(f"✅ Updated Preparation Display: {prep_display.id}")

        else:
            # ✅ Create a new Preparation Display with fresh stages
            prep_display_vals = {
                'name': pos_config.name,
                'company_id': self.env.company.id,
                'pos_config_ids': [(6, 0, [pos_config.id])],
                'stage_ids': [(0, 0, stage) for stage in stage_data]
            }
            prep_display = self.env['pos_preparation_display.display'].create(prep_display_vals)
            print(f"✅ Created new Preparation Display: {prep_display.id}")

        return prep_display

    def action_connect_app(self):
        """Handles API connection and POS configuration."""
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
        url = api_url + "auth/login"
        headers = self.get_api_headers()
        data = {
            "login": self.api_email,
            "password": self.api_password
        }

        try:
            print("All Data:", data, headers, url)
            response = requests.post(url, headers=headers, data=json.dumps(data))

            # ✅ Handle HTTP errors properly
            if response.status_code == 200:
                data = response.json()
                print("Response Data:", data)

                model_vals = {
                    'api_email': self.api_email,
                    'api_password': self.api_password,
                    'status': data.get('status'),
                    'message': data.get('message'),
                    'api_token': data.get('token'),
                    'user_id': data['user'].get('id'),
                    'user_first_name': data['user'].get('first_name'),
                    'user_last_name': data['user'].get('last_name'),
                    'user_phone': data['user'].get('phone'),
                    'user_username': data['user'].get('username'),
                    'name': data['user']['restos'][0].get('name') if data['user'].get('restos') else None,
                    'user_restos_id': data['user']['restos'][0].get('id') if data['user'].get('restos') else None
                }
                self.write(model_vals)

                try:
                    # ✅ Create a user in Odoo
                    user_vals = {
                        'name': model_vals['user_username'],
                        'login': model_vals['api_email'],
                        'groups_id': [(6, 0, [
                            self.env.ref('base.group_user').id,  # Internal User
                            self.env.ref('point_of_sale.group_pos_manager').id  # POS Administrator
                        ])],
                    }
                    self.env['res.users'].sudo().create(user_vals)
                except Exception as e:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'User Creation Error',
                            'message': f"Failed to create user: {str(e)}",
                            'type': 'danger',
                            'sticky': True,
                        }
                    }

                # ✅ Handle POS Config Creation
                if not self.restaurant_id:
                    pos_config = self.create_pos_config(model_vals)
                    self.create_or_update_preparation_display(pos_config)
                else:
                    self.restaurant_id.write({'garista_restaurant_id': model_vals.get('user_restos_id')})
                    self.create_or_update_preparation_display(self.restaurant_id)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'API connection successful and record updated!',
                        'type': 'success',
                        'sticky': False,
                    }
                }

            elif response.status_code == 400:
                error_message = "Bad Request: The API did not accept the data."
            elif response.status_code == 401:
                error_message = "Unauthorized: Invalid API credentials."
            elif response.status_code == 403:
                error_message = "Forbidden: You do not have permission to access this API."
            elif response.status_code == 404:
                error_message = "Not Found: The API endpoint is incorrect."
            elif response.status_code == 405:
                error_message = "Method Not Allowed: Check if you're using the correct HTTP method (POST/GET). or Path Missing in Garista URL Setting"
            elif response.status_code == 500:
                error_message = "Internal Server Error: The API server encountered an error."
            else:
                error_message = f"Unexpected Error: {response.status_code} - {response.text}"

            # ✅ Show the exact error message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'API Error',
                    'message': error_message,
                    'type': 'danger',
                    'sticky': True,
                }
            }

        except requests.ConnectionError:
            error_message = "Connection Error: Unable to reach the API server. Check your internet or API URL."
        except requests.Timeout:
            error_message = "Timeout Error: The API server is taking too long to respond."
        except requests.RequestException as e:
            error_message = f"API Request Failed: {str(e)}"
        except Exception as e:
            error_message = f"Unexpected Error: {str(e)}"

        # ✅ Show the correct error message in Odoo
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'API Connection Failed',
                'message': error_message,
                'type': 'danger',
                'sticky': True,
            }
        }

           
    def get_api_url(self):
        try:
            api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
            if not api_url:
                return None
            return api_url.rstrip('/') + '/'
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    
    def fetch_items_from_api(self, endpoint):
        try:
            api_url = self.get_api_url()
            if not api_url:
                return {'error': 'Please enter the API URL in Garista Settings first.'}
            
            headers = self.get_api_headers()
            url = f"{api_url}{endpoint}{self.user_restos_id}"
            response = requests.get(url, headers=headers)
            if response.ok:
                return response.json()
            return {'error': f"Error: {response.status_code} {response.text}"}
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    
    def process_items(self, items):
        try:
            extracted_data = []
            for item in items:
                dish_data = {
                    "id": item["id"],
                    "name": item["name"],
                    "category_id": item["category_id"],
                    "price": item["price"],
                    "isVariant": item.get("isVariant", 0),
                    "resto_id": item["resto_id"],
                    "image": item.get("image1", ""),
                    "extravariants": []
                }
                existing_product = self.env['product.template'].search([
                    ('garista_product_id', '=', dish_data['id'])
                ], limit=1)
                if existing_product:
                    continue  # Skip if the product already exists
                
                for extravariant in item.get("extravariants", []):
                    topping_data = {
                        "id": extravariant["id"],
                        "name": extravariant["name"],
                        "options": json.loads(extravariant["options"]) if isinstance(extravariant["options"], str) else extravariant["options"]
                    }
                    dish_data["extravariants"].append(topping_data)
                extracted_data.append(dish_data)
            
            return extracted_data
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    
    def create_garista_pos_product(self, products):
        try:
            image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
            new_products_count = 0  # Track newly created products

            for product in products:
                product_id = product.get('id')

                # Check if product already exists
                existing_product = self.env['product.template'].sudo().search([
                    ('garista_product_id', '=', product_id)
                ], limit=1)

                if existing_product:
                    continue  # Skip existing products
                
                # If product doesn't exist, create it
                new_products_count += 1  # Increment new product count
                
                product_name = product.get('name')
                product_category_id = product.get('category_id')
                product_price = product.get('price')
                product_isVariant = product.get('isVariant')
                product_image = product.get('image')
                image_url = image_base_url + product_image

                response = requests.get(image_url)

                existing_category = self.env['pos.category'].sudo().search([
                    ('garista_category_id', '=', product_category_id)
                ], limit=1)

                if response.status_code == 200:
                    image_base64 = base64.b64encode(response.content)
                    product_template_vals = {
                        'name': product_name,
                        'list_price': product_price,
                        'garista_product_id': product_id,
                        'available_in_pos': True,
                        'image_1920': image_base64,
                    }

                    if existing_category:
                        product_template_vals['pos_categ_ids'] = [(6, 0, [existing_category.id])]

                    product_template = self.env['product.template'].sudo().create(product_template_vals)

                if product_isVariant == 1:
                    self.create_product_variants(product, product_template)

            return new_products_count  # Return the count of new products

        except Exception as e:
            return -1  # Return -1 in case of an error

    def create_product_variants(self, product, product_template):
        try:
            print("Product Variant Start")
            print(product)
            print(product.get("extravariants", []))
            for extravariant in product.get("extravariants", []):
                extravariant_name = extravariant.get("name")
                extravariant_garista_id = extravariant.get("id")
                options = extravariant.get("options", [])
                
                attribute = self.env['product.attribute'].sudo().search([('garista_attribute_id', '=', extravariant_garista_id)], limit=1)
                print(attribute)
                if not attribute:
                    attribute = self.env['product.attribute'].sudo().create({
                        'name': extravariant_name,
                        'garista_attribute_id':extravariant_garista_id,
                        'display_type': 'multi',
                        'create_variant': 'no_variant',
                    })
                
                attribute_value_ids = []
                for option_data in options:
                    name = option_data['name']
                    extra_price = option_data['price']
                    
                    option_value = self.env['product.attribute.value'].sudo().search([
                        ('name', '=', name),
                        ('attribute_id', '=', attribute.id)
                    ], limit=1)
                    
                    if not option_value:
                        option_value = self.env['product.attribute.value'].sudo().create({
                            'name': name,
                            'attribute_id': attribute.id,
                            'default_extra_price': extra_price
                        })
                    else:
                        option_value.sudo().write({
                            'default_extra_price': extra_price
                        })
                    
                    attribute_value_ids.append(option_value.id)
                
                self.env['product.template.attribute.line'].sudo().create({
                    'product_tmpl_id': product_template.id,
                    'attribute_id': attribute.id,
                    'value_ids': [(6, 0, attribute_value_ids)]
                })
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    
    def get_dishes_pos(self):
        try:
            dishes = self.fetch_items_from_api("dishes/")
            if 'error' in dishes:
                return dishes
            extracted_data = self.process_items(dishes)
            print("extracted_data",extracted_data)
            if extracted_data:
                new_products_count = self.create_garista_pos_product(extracted_data)
                
                if new_products_count == -1:
                    return self.display_notification("Error", "An error occurred while creating products.", "danger")
                elif new_products_count > 0:
                    return self.display_notification("Success", f"{new_products_count} new product(s) created!", "success")
                else:
                    return self.display_notification("Info", "All products already exist.", "info")
            
            return self.display_notification("Info", "No new products found.", "info")

        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    def get_drinks_pos(self):
        try:
            drinks = self.fetch_items_from_api("drinks-resto/")
            if 'error' in drinks:
                return drinks
            
            extracted_data = self.process_items(drinks)
            if extracted_data:
                new_products_count = self.create_garista_pos_product(extracted_data)
                
                if new_products_count == -1:
                    return self.display_notification("Error", "An error occurred while creating drinks.", "danger")
                elif new_products_count > 0:
                    return self.display_notification("Success", f"{new_products_count} new drink(s) created!", "success")
                else:
                    return self.display_notification("Info", "All drinks already exist.", "info")
            
            return self.display_notification("Info", "No new drinks found.", "info")

        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    
    def get_tables(self):
        api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
        row_limit = 6  # Max tables per row
        spacing = 50  # Space between tables
        width = 150
        height = 150
        start_x = 10  # Starting X position
        start_y = 10  # Starting Y position

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
        api_path = 'tables/'
        user_restos_id = self.user_restos_id
        headers = self.get_api_headers()
        url = api_url + api_path + user_restos_id

        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                items = response.json()
                new_tables_count = 0
                total_tables = len(items)

                # Delete only existing tables for the current restaurant instance
                existing_tables = self.env['restaurant.table'].sudo().search([
                    ('floor_id.pos_config_ids.garista_restaurant_id', '=', user_restos_id)
                ])
                try:
                    existing_tables.unlink()
                except Exception as e:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Error',
                            'message': 'Some tables are currently in use. Please close all POS sessions before import.',
                            'type': 'danger',
                            'sticky': True,
                        }
                    }

                for item in items:
                    model_vals = []
                    table_name = item.get('name')
                    table_id = item.get('id')
                    table_x = item.get('x')
                    table_y = item.get('y')
                    table_shape = item.get('shape') or 'square'
                    table_seats = item.get('seats') or 6
                    identifier = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                    restaurant_id = item.get('resto_id')

                    existing_restaurent = self.env['pos.config'].sudo().search(
                        [('garista_restaurant_id', '=', restaurant_id)], limit=1
                    )
                    if not existing_restaurent:
                        continue

                    existing_floor = self.env['restaurant.floor'].sudo().search(
                        [('name', '=', 'Main'), ('pos_config_ids', 'in', [existing_restaurent.id])], limit=1
                    )
                    if not existing_floor:
                        existing_floor = self.env['restaurant.floor'].sudo().create({
                            'name': 'Main',
                            'pos_config_ids': [(6, 0, [existing_restaurent.id])],
                        })

                    if table_x is None or table_y is None:
                        table_x = start_x + (new_tables_count % row_limit) * (width + spacing)
                        table_y = start_y + (new_tables_count // row_limit) * (height + spacing)

                    model_vals.append({
                        'name': table_name,
                        'identifier': identifier,
                        'seats': table_seats,
                        'shape': table_shape,
                        'position_h': table_x,
                        'position_v': table_y,
                        'width': width,
                        'height': height,
                        'floor_id': existing_floor.id,
                        'garista_table_id': table_id
                    })

                    self.env['restaurant.table'].sudo().create(model_vals)
                    new_tables_count += 1

                if new_tables_count > 0:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Success',
                            'message': 'Garista table(s) has been Sync',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Info',
                            'message': 'No new tables were imported.',
                            'type': 'info',
                            'sticky': False,
                        }
                    }

            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': f'Error: {response.status_code}, {response.text}',
                        'type': 'danger',
                        'sticky': True,
                    }
                }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }

   

    def display_notification(self, title, message, notification_type):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': True,
            }
        }
    
    
   
     
    def get_dishes_category(self):
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
        api_path = "categories/"
        user_restos_id = self.user_restos_id
        headers = self.get_api_headers()
        url = api_url + api_path + user_restos_id
        
        try:
            response = requests.get(url , headers=headers)
            if response.ok:
                data = response.json()
                model_vals = []
                
                for item in data:
                    name = item.get('name')
                    category_type = item.get('type')
                    # Check if the category already exists
                    existing_category = self.env['pos.category'].search([('name', '=', name)], limit=1)
                    if existing_category:
                        print(f"Category '{name}' already exists. Skipping...")
                        continue  # Skip this item if it already exists
                    parent_category = self.get_parent_category(category_type) if category_type in ['dish', 'both', 'drink'] else None
                    model_vals.append({
                        'id': item.get('id'),
                        'name': name,
                        'image': item.get('image'),
                        'category_type': category_type,
                        'resto_id': item.get('resto_id'),
                        'parent_category': parent_category
                    })
                if model_vals:
                    self.create_garista_pos_category(model_vals)
                else:
                    return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': 'API connection successful and Sync Complete!',
                        'type': 'danger',
                        'sticky': True,
                    }
                 }  
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'API connection successful and record Created and updated!',
                        'type': 'success',  # 'success', 'warning', 'danger'
                        'sticky': False,   # If True, the message will stay visible until manually closed
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': f"Error: {response.status_code} {response.text}",
                        'type': 'danger',
                        'sticky': True,
                    }
                 }
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
    
                    
    def get_parent_category(self, category_name): 
        if category_name in ['dish', 'both']:
            category_names = ['Food', 'Foods', 'food']
        elif category_name == 'drink':
            category_names = ['Drink','Drinks','drink']
        else:
            return None    
        # Search for existing category
        category = self.env['pos.category'].sudo().search([('name', 'in', category_names)], limit=1)
        # Create if not found
        if not category:
            category = self.env['pos.category'].sudo().create({'name': category_names[0]})  # Use first standard name

        return category.id  # Return the category ID

    def create_garista_pos_category(self, categories):
        image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
        for category in categories:
            name = category.get('name')
            image = category.get('image')  # Assuming this is a path or base64 string
            garista_category_id = category.get('id')

            parent_id = category.get('parent_category') if category.get('parent_category') else None
            image_url = image_base_url + image if image else None  # Handle missing image

            category_vals = {'name': name, 'garista_category_id': garista_category_id}
            # Fetch and encode image
            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_base64 = base64.b64encode(response.content).decode('utf-8')  # Convert bytes to string
                    category_vals['image_128'] = image_base64
                else:
                    print(f"Failed to download the image. Status code: {response.status_code}")
            if parent_id:
                category_vals['parent_id'] = parent_id

            # Uncomment to actually create the category in Odoo
            category = self.env['pos.category'].create(category_vals)
            print("Category has been created",category.id)
        
    @api.model
    def update_garista_status(self):
        """Fetch status from API and update the status field."""
        endpoint = "restos/"
        garista_obj = self.env["garista.garista"].search([], limit=1)

        if not garista_obj:
            print("No Garista record found.")
            return

        api_url = self.get_api_url()
        if not api_url:
            print("Error: Please enter the API URL in Garista Settings first.")
            return

        if not garista_obj.token:
            print("Error: API token is missing in Garista settings.")
            return

        headers = {
            "x-validate-api-token": garista_obj.token,
            "Content-Type": "application/json",
        }

        url = f"{api_url}{endpoint}{garista_obj.user_restos_id}"
        print(url, headers)

        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                data = response.json()
                new_status = data[0]['status'].capitalize() if data else 'Disconnected'

                # Check if status has changed
                if new_status != garista_obj.status:
                    updates = {'status': new_status}

                    # Reset last_disconnect_timestamp when reconnecting
                    if new_status == 'Active':
                        print("This is last disconnect_time:", garista_obj.last_disconnect_timestamp)
                        now_utc = fields.Datetime.now()

                        # Handle case where last_disconnect_timestamp is None
                        last_disconnect_minus_5 = garista_obj.last_disconnect_timestamp - timedelta(minutes=5) if garista_obj.last_disconnect_timestamp else now_utc

                        orders = self.env['pos.order'].search([
                            ('date_order', '>=', last_disconnect_minus_5),
                            ('date_order', '<=', now_utc),
                            ('is_Sync', '=', False)
                        ])
                        print("Both Dates", last_disconnect_minus_5, now_utc, orders)

                        for order in orders:
                            self.env['garista.sync'].sync_order_in_background(order.id, order.date_order)

                        updates['last_disconnect_timestamp'] = False  

                    garista_obj.write(updates)
                    print(f"Updated status for ID {garista_obj.user_restos_id}: {new_status}")

                # If status is "Disconnected" and timestamp is not set, set it
                elif new_status == 'Disconnected' and not garista_obj.last_disconnect_timestamp:
                    garista_obj.write({'last_disconnect_timestamp': fields.Datetime.now()})
                    print(f"Set last disconnect timestamp for ID {garista_obj.user_restos_id}")

            else:
                garista_obj.handle_disconnection()

        except Exception as e:
            print(f"Failed to fetch Garista API: {str(e)}")
            garista_obj.handle_disconnection()

    def handle_disconnection(self):
        """Handles disconnection: Updates timestamp only when status first changes."""
        for record in self:
            if record.status != 'Disconnected':  # Only update if status is changing
                record.write({
                    'status': 'Disconnected',
                    'last_disconnect_timestamp': fields.Datetime.now(),
                })
                print(f"Status changed to Disconnected, timestamp recorded for ID {record.user_restos_id}")
            else:
                print("No need to update")

    # def update_garista_status(self):
    #     """Fetch status from API and update the status field."""
    #     endpoint = "restos/"
    #     garista_obj = self.env["garista.garista"].search([], limit=1)
    #     api_url = self.get_api_url()
    #     if not api_url:
    #         return {'error': 'Please enter the API URL in Garista Settings first.'}
        
    #     headers = {
    #     "x-validate-api-token": garista_obj.token ,
    #     "Content-Type": "application/json",
    #      }
    #     url = f"{api_url}{endpoint}{garista_obj.user_restos_id}"
    #     print(url, headers)
        
    #     try:
    #         response = requests.get(url, headers=headers)
    #         if response.ok:
    #             data = response.json()
    #             new_status = data[0]['status'].capitalize() if data else 'Disconnected'
                
    #             # Check if status has changed
    #             if new_status != garista_obj.status:
    #                 updates = {'status': new_status}

    #                 # Reset last_disconnect_timestamp when reconnecting
    #                 if new_status == 'Active':
    #                     print("This is last disconnect_time",garista_obj.last_disconnect_timestamp)
    #                     now_utc = fields.Datetime.now()
    #                     last_disconnect_minus_5 = garista_obj.last_disconnect_timestamp - timedelta(minutes=5)
    #                     orders = self.env['pos.order'].search([
    #                         ('date_order', '>=', last_disconnect_minus_5),
    #                         ('date_order', '<=', now_utc),
    #                         ('is_Sync','=',False)
    #                     ])
    #                     print("Both Dates",last_disconnect_minus_5,now_utc,orders)
    #                     for order in orders:
    #                         self.env['garista.sync'].sync_order_in_background(order.id,order.date_order)
    #                     updates['last_disconnect_timestamp'] = False  

    #                 garista_obj.write(updates)
    #                 print(f"Updated status for ID {self.user_restos_id}: {new_status}")

    #             # If status is "Disconnected" and timestamp is not set, set it
    #             elif new_status == 'Disconnected' and not self.last_disconnect_timestamp:
    #                 self.write({'last_disconnect_timestamp': datetime.now()})
    #                 print(f"Set last disconnect timestamp for ID {self.user_restos_id}")

    #         else:
    #             self.handle_disconnection()

    #     except Exception as e:
    #         print(f"Failed to fetch Garista API: {str(e)}")
    #         self.handle_disconnection()


    # def handle_disconnection(self):
    #     """Handles disconnection: Updates timestamp only when status first changes."""
    #     if self.status != 'Disconnected':  # Only update if status is changing
    #         self.write({
    #             'status': 'Disconnected',
    #             'last_disconnect_timestamp': datetime.now(),
    #         })
    #         print(f"Status changed to Disconnected, timestamp recorded for ID {self.user_restos_id}")
    #     else:
    #         print("No need to update")

    
    def execute_all_methods(self):
        for method in [self.get_dishes_category, self.get_dishes_pos, self.get_drinks_pos]:
            try:
                method()  # Call the method
            except Exception:
                pass  # Ignore errors and continue