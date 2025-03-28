from odoo import models, api
import requests
import base64
import json

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'
    

    def get_api_headers(self):
        """Retrieve API headers for Garista."""	
        restaurant = self.env['garista.garista'].search([('message', '=', 'Login successful')], limit=1)
        token = restaurant.token
        api_token = restaurant.api_token
        return {
            "x-validate-api-token": token,
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json", 
        }
    
    def get_api_url(self):
        try:
            api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
            if not api_url:
                return None
            return api_url.rstrip('/') + '/'
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
        
    def action_sync_garista(self):
        """Sync a single dish only if garista_product_id exists"""
        try:
            if not self.garista_product_id:
                return self.display_notification("Info", "No product ID found. Sync skipped.", "info")

            dish_data = self.fetch_single_item()
            if 'error' in dish_data:
                return self.display_notification("Error", dish_data['error'], "danger")

            return self.process_single_item(dish_data)
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")

    # def fetch_single_item(self):
    #     """Fetch a single dish from Garista API"""
    #     try:
    #         api_url = self.get_api_url()
    #         if not api_url:
    #             return {'error': 'Please enter the API URL in Garista Settings first.'}

    #         headers = self.get_api_headers()
    #         url = f"{api_url}getDishe/{self.garista_product_id}"

    #         response = requests.get(url, headers=headers)
    #         if response.ok:
    #             return response.json()
    #         return {'error': f"Error: {response.status_code} {response.text}"}
    #     except Exception as e:
    #         return {'error': str(e)}
    def fetch_single_item(self):
        """Fetch a single dish or drink from Garista API based on category"""
        try:
            api_url = self.get_api_url()
            if not api_url:
                return {'error': 'Please enter the API URL in Garista Settings first.'}

            headers = self.get_api_headers()

            # Determine if the product belongs to Food or Drink
            parent_category = None
            for category in self.pos_categ_ids:
                if 'Food' in category.display_name:
                    parent_category = 'Food'
                    break
                elif 'Drink' in category.display_name:
                    parent_category = 'Drink'
                    break

            # Construct the appropriate API URL
            if parent_category == 'Food':
                url = f"{api_url}getDishe/{self.garista_product_id}"
            elif parent_category == 'Drink':
                url = f"{api_url}getDrink/{self.garista_product_id}"
            else:
                return {'error': 'Category not recognized as Food or Drink.'}

            response = requests.get(url, headers=headers)
            if response.ok:
                return response.json()
            return {'error': f"Error: {response.status_code} {response.text}"}
        except Exception as e:
            return {'error': str(e)}

    def process_single_item(self, item):
        """Update product and attributes only if product exists"""
        try:
            product_id = item.get("id")
            product_name = item.get("name")
            product_price = item.get("price")
            product_image = item.get("image1", "")
            is_variant = item.get("isVariant", 0)
            image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
            image_url = f"{image_base_url}{product_image}"

            existing_product = self.env['product.template'].sudo().search([
                ('garista_product_id', '=', product_id)
            ], limit=1)

            if not existing_product:
                return self.display_notification("Info", "Product does not exist in Odoo. Sync skipped.", "info")

            image_base64 = None
            response = requests.get(image_url)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content)

            product_vals = {
                'name': product_name,
                'list_price': product_price,
                'image_1920': image_base64 if image_base64 else False,
            }

            existing_product.sudo().write(product_vals)

            # If product has variants, update them
            if is_variant == 1:
                self.create_or_update_variants(existing_product, item.get("extravariants", []))

            self.display_notification("Success", f"Product '{product_name}' updated!", "success")
            return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    
    def create_or_update_variants(self, product_template, extravariants):
        """Create or update product attributes and variants"""
        try:
            print("Starting extra variant", extravariants)
            for extravariant in extravariants:
                extravariant_name = extravariant.get("name")
                extravariant_garista_id = extravariant.get("id")
                options = extravariant.get("options", [])

                # Search for existing attribute
                attribute = self.env['product.attribute'].sudo().search([
                    ('garista_attribute_id', '=', extravariant_garista_id)
                ], limit=1)
               

                if not attribute:
                    attribute = self.env['product.attribute'].sudo().create({
                        'name': extravariant_name,
                        'garista_attribute_id': extravariant_garista_id,
                        'display_type': 'multi',
                        'create_variant': 'no_variant',
                    })

                attribute_value_ids = []
                print("Options", type(options))

                if isinstance(options, str):
                    try:
                        options = json.loads(options)  # Convert string to list
                    except json.JSONDecodeError:
                        print("Error: Invalid JSON format for options:", options)
                        continue  # Skip this variant if JSON is invalid

                for option_data in options:
                    print("start for loop", option_data)
                    name = option_data['name']
                    extra_price = option_data['price']
                    # Search for all matching attribute values
                    option_values = self.env['product.attribute.value'].sudo().search([
                        ('name', '=', name),
                        ('attribute_id', '=', attribute.id)
                    ])
                    if not option_values:
                        # Create new attribute value if it doesn't exist
                        new_value = self.env['product.attribute.value'].sudo().create({
                            'name': name,
                            'attribute_id': attribute.id,
                            'default_extra_price': extra_price
                        })
                        attribute_value_ids.append(new_value.id)
                        option_values = new_value  # Assign newly created value to update price_extra below
                    else:
                        # Update all existing values
                        for option_value in option_values:
                            option_value.sudo().write({'default_extra_price': extra_price})
                            attribute_value_ids.append(option_value.id)

                    # Update price_extra in product.template.attribute.value
                    product_tmpl_attr_values = self.env['product.template.attribute.value'].sudo().search([
                        ('product_attribute_value_id', 'in', option_values.ids)
                    ])

                    for tmpl_attr_value in product_tmpl_attr_values:
                        tmpl_attr_value.sudo().write({'price_extra': extra_price})

                # Search for existing attribute line
                attribute_line = self.env['product.template.attribute.line'].sudo().search([
                    ('product_tmpl_id', '=', product_template.id),
                    ('attribute_id', '=', attribute.id)
                ])

                if attribute_line:
                    attribute_line.sudo().write({'value_ids': [(6, 0, attribute_value_ids)]})
                else:
                    self.env['product.template.attribute.line'].sudo().create({
                        'product_tmpl_id': product_template.id,
                        'attribute_id': attribute.id,
                        'value_ids': [(6, 0, attribute_value_ids)]
                    })
        except Exception as e:
            return self.display_notification("Error", str(e), "danger")
    # def create_or_update_variants(self, product_template, extravariants):
    #     """Create or update product attributes and variants"""
    #     try:
    #         print("Starting extra variant",extravariants)
    #         for extravariant in extravariants:
    #             extravariant_name = extravariant.get("name")
    #             extravariant_garista_id = extravariant.get("id")
    #             options = extravariant.get("options", [])

    #             # Search for existing attribute
    #             attribute = self.env['product.attribute'].sudo().search([
    #                 ('garista_attribute_id', '=', extravariant_garista_id)
    #             ], limit=1)
    #             print("attribute name", attribute.name,attribute.id)
    #             if not attribute:
    #                 attribute = self.env['product.attribute'].sudo().create({
    #                     'name': extravariant_name,
    #                     'garista_attribute_id': extravariant_garista_id,
    #                     'display_type': 'multi',
    #                     'create_variant': 'no_variant',
    #                 })

    #             attribute_value_ids = []
    #             print("Options",type(options))
    #             if isinstance(options, str):
    #                 try:
    #                     options = json.loads(options)  # Convert string to list
    #                 except json.JSONDecodeError:
    #                     print("Error: Invalid JSON format for options:", options)
    #                     continue  # Skip this variant if JSON is invalid
    #             for option_data in options:
    #                 print("start for loop",option_data)
    #                 name = option_data['name']
    #                 extra_price = option_data['price']
    #                 print("name,extra_price",name,extra_price)
    #                 # Search for all matching attribute values
    #                 option_values = self.env['product.attribute.value'].sudo().search([
    #                     ('name', '=', name),
    #                     ('attribute_id', '=', attribute.id)
    #                 ])
    #                 print("option_values",option_values)
    #                 if not option_values:
    #                     # Create new attribute value if it doesn't exist
    #                     new_value = self.env['product.attribute.value'].sudo().create({
    #                         'name': name,
    #                         'attribute_id': attribute.id,
    #                         'default_extra_price': extra_price
    #                     })
    #                     attribute_value_ids.append(new_value.id)
    #                 else:
    #                     # Update all existing values
    #                     for option_value in option_values:
    #                         option_value.sudo().write({'default_extra_price': extra_price})
    #                         attribute_value_ids.append(option_value.id)

    #             # Search for existing attribute line
    #             attribute_line = self.env['product.template.attribute.line'].sudo().search([
    #                 ('product_tmpl_id', '=', product_template.id),
    #                 ('attribute_id', '=', attribute.id)
    #             ])

    #             if attribute_line:
    #                 attribute_line.sudo().write({'value_ids': [(6, 0, attribute_value_ids)]})
    #             else:
    #                 self.env['product.template.attribute.line'].sudo().create({
    #                     'product_tmpl_id': product_template.id,
    #                     'attribute_id': attribute.id,
    #                     'value_ids': [(6, 0, attribute_value_ids)]
    #                 })
    #     except Exception as e:
    #         return self.display_notification("Error", str(e), "danger")

        
    
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
    # def action_sync_garista(self):
    #     # Logic for syncing with Garista will be added later
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Sync Garista',
    #             'message': 'Sync action triggered!',
    #             'sticky': False,
    #         }
    #     }
