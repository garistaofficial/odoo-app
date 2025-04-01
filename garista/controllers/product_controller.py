from odoo import http
from odoo.http import request
import base64
import json
import requests

class GaristaProductController(http.Controller):

    @http.route('/garista/product/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_garista_products(self):
        data = json.loads(request.httprequest.data)
        headers = request.httprequest.headers
        api_token = headers.get('api_token')
        username = data.get('username')

        if not username or not api_token:
            return {
                'status': 'error',
                'message': 'API token and username are required for access'
            }

        valid = request.env['garista.garista'].sudo().validate_api_token(api_token, username)
        print(valid)

        if not valid:
            return {
                'status': 'error',
                'message': 'API token invalid'
            }

        extracted_data = []
        item = {
            "id": data["id"],
            "name": data["name"],
            "category_id": data["category_id"],
            "price": data["price"],
            "isVariant": data["isVariant"],
            "image": data.get("image", ""),
            "extravariants": []
        }
        
        existing_product = request.env['product.template'].sudo().search([('garista_product_id', '=', data['id'])], limit=1)

        if existing_product:
            return {
                    'status': 'success',
                    'message': 'Product Existing',
                }

        for extravariant in data.get("extravariants", []):
            extravariant_data = {
                "name": extravariant["name"],
                "options": json.loads(extravariant["options"]) if isinstance(extravariant["options"], str) else extravariant["options"]
            }
            item["extravariants"].append(extravariant_data)
        extracted_data.append(item)

        if extracted_data:
            self.create_garista_pos_product(extracted_data)
            return {
                    'status': 'success',
                    'message': 'Access granted Products created successfully',
                }
        else:
            return {
                'status': 'error',
                'message': 'No new products to create',
            }

    def create_garista_pos_product(self, extracted_data):
        image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
        for product_data in extracted_data:
            product_id = product_data.get('id')
            product_name = product_data.get('name')
            product_category_id = product_data.get('category_id')
            product_price = product_data.get('price')
            product_isVariant = product_data.get('isVariant')
            product_image = product_data.get('image')

            existing_category = request.env['pos.category'].sudo().search([('garista_category_id', '=', product_category_id)], limit=1)

            image_url = image_base_url + product_image
            response = requests.get(image_url)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content)
                if existing_category:
                    product_template = request.env['product.template'].sudo().create({
                        'name': product_name,
                        'pos_categ_ids': [(6, 0, [existing_category.id])],
                        'list_price': product_price,
                        'garista_product_id': product_id,
                        'available_in_pos': True,
                        'image_1920': image_base64,
                    })
                    print(product_template, "Product has been Created")
                else:
                    product_template = request.env['product.template'].sudo().create({
                        'name': product_name,
                        'image_1920': image_base64,
                        'list_price': product_price,
                        'garista_product_id': product_id,
                        'available_in_pos': True,
                    })
                    print(product_template, "Product has been Created")

            if product_isVariant == 1:
                for extravariant in product_data.get("extravariants", []):
                    extravariant_name = extravariant.get("name")
                    options = extravariant.get("options", [])
                    attribute = request.env['product.attribute'].sudo().search([('name', '=', extravariant_name)], limit=1)

                    if not attribute:
                        attribute = request.env['product.attribute'].sudo().create({
                            'name': extravariant_name,
                            'display_type': 'multi',
                            'create_variant': 'no_variant',
                        })

                    attribute_value_ids = []
                    for option_data in options:
                        name = option_data['name']
                        extra_price = option_data['price']
                        option_value = request.env['product.attribute.value'].sudo().search([
                            ('name', '=', name),
                            ('attribute_id', '=', attribute.id)
                        ], limit=1)

                        if not option_value:
                            option_value = request.env['product.attribute.value'].sudo().create({
                                'name': name,
                                'attribute_id': attribute.id,
                                'default_extra_price': extra_price
                            })
                        else:
                            option_value.sudo().write({
                                'default_extra_price': extra_price
                            })

                        attribute_value_ids.append(option_value.id)

                    request.env['product.template.attribute.line'].sudo().create({
                        'product_tmpl_id': product_template.id,
                        'attribute_id': attribute.id,
                        'value_ids': [(6, 0, attribute_value_ids)]
                    })


    @http.route('/garista/product/update', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_pos_product(self, **kwargs):
        print("update_pos_product")
        data = json.loads(request.httprequest.data)
        headers = request.httprequest.headers
        api_token = headers.get('api_token')
        username = data.get('username')

        if not username or not api_token:
            return {
                'status': 'error',
                'message': 'API token and username are required for access'
            }

        valid = request.env['garista.garista'].sudo().validate_api_token(api_token, username)
        print(valid)

        if not valid:
            return {
                'status': 'error',
                'message': 'API token invalid'
            }

        product_id = data.get('id')
        if not product_id:
            return {'status': 'error', 'message': 'Product ID is required'}

        existing_product = request.env['product.template'].sudo().search([('garista_product_id', '=', product_id)], limit=1)

        if not existing_product:
            return {'status': 'error', 'message': 'Product ID does not exist'}

        product_name = data.get('name')
        product_category_id = data.get('category_id')
        product_price = data.get('price')
        product_image = data.get('image')
        extravariants = data.get('extravariants', [])


        if product_image:
            image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
            image_url = image_base_url + product_image
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_base64 = base64.b64encode(response.content)
                    existing_product.image_128 = image_base64
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

        product_template_vals = {
            'name': product_name,
            'list_price': product_price,
            'image_1920': image_base64,
        }

        if product_category_id:
            existing_category = request.env['pos.category'].sudo().search([('garista_category_id', '=', product_category_id)], limit=1)
            print(existing_category)
            if existing_category:
                product_template_vals['pos_categ_ids'] = [(6, 0, [existing_category.id])]

        existing_product.sudo().write(product_template_vals)

        if extravariants:
            for extravariant in extravariants:
                extravariant_name = extravariant.get('name')
                options = extravariant.get('options', [])

                attribute = request.env['product.attribute'].sudo().search([('name', '=', extravariant_name)], limit=1)
                if not attribute:
                    attribute = request.env['product.attribute'].sudo().create({
                        'name': extravariant_name,
                        'display_type': 'multi',
                        'create_variant': 'no_variant',
                    })

                attribute_value_ids = []
                for option_data in options:
                    print("start for loop", option_data)
                    name = option_data['name']
                    extra_price = option_data['price']
                    # Search for all matching attribute values
                    option_values = request.env['product.attribute.value'].sudo().search([
                        ('name', '=', name),
                        ('attribute_id', '=', attribute.id)
                    ])
                    if not option_values:
                        # Create new attribute value if it doesn't exist
                        new_value = request.env['product.attribute.value'].sudo().create({
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
                    product_tmpl_attr_values = request.env['product.template.attribute.value'].sudo().search([
                        ('product_attribute_value_id', 'in', option_values.ids)
                    ])

                    for tmpl_attr_value in product_tmpl_attr_values:
                        tmpl_attr_value.sudo().write({'price_extra': extra_price})

                # Search for existing attribute line
                attribute_line = request.env['product.template.attribute.line'].sudo().search([
                    ('product_tmpl_id', '=', existing_product.id),
                    ('attribute_id', '=', attribute.id)
                ])

                if attribute_line:
                    attribute_line.sudo().write({'value_ids': [(6, 0, attribute_value_ids)]})
                
                else:
                    request.env['product.template.attribute.line'].sudo().create({
                        'product_tmpl_id': existing_product.id,
                        'attribute_id': attribute.id,
                        'value_ids': [(6, 0, attribute_value_ids)]
                    })
        
        return {'status': 'success', 'message': 'Access granted Product and variants updated successfully'}



    @http.route('/api/delete_product_and_variant', type='json', auth='public', methods=['DELETE'], csrf=False)
    def delete_product_variant(self, **kwargs):
        data = json.loads(request.httprequest.data)
        headers = request.httprequest.headers
        api_token = headers.get('api_token')
        username = data.get('username')

        if not username or not api_token:
            return {
                'status': 'error',
                'message': 'API token and username are required for access'
            }

        valid = request.env['garista.garista'].sudo().validate_api_token(api_token, username)
        print(valid)

        if not valid:
            return {
                'status': 'error',
                'message': 'API token invalid'
            }
        product_id = data.get('id')
        attribute_name = data.get('attribute_name')
        option_name = data.get('option_name')

        if not product_id:
            return {'status': 'error', 'message': 'Product ID is required'}

        product_template = request.env['product.template'].sudo().search([('garista_product_id', '=', product_id)], limit=1)
        if not product_template:
            return {'status': 'error', 'message': f"Product with ID '{product_id}' does not exist"}

        if not attribute_name and not option_name:
            product_template.sudo().unlink()
            return {'status': 'success', 'message': f"Access granted Product with ID '{product_id}' deleted successfully"}

        # Find the attribute
        attribute = request.env['product.attribute'].sudo().search([('name', '=', attribute_name)], limit=1)
        if not attribute:
            return {'status': 'error', 'message': f"Attribute '{attribute_name}' not found"}

        # If no option name is provided, delete the entire attribute
        if not option_name:
            attribute_line = request.env['product.template.attribute.line'].sudo().search([
                ('product_tmpl_id', '=', product_template.id),
                ('attribute_id', '=', attribute.id)
            ], limit=1)

            if attribute_line:
                attribute_line.sudo().unlink()  # Delete the attribute line

            # Check if the attribute is still in use by any other product; if not, delete it
            attribute_in_use = request.env['product.template.attribute.line'].sudo().search([
                ('attribute_id', '=', attribute.id)
            ], limit=1)

            if not attribute_in_use:
                attribute.sudo().unlink()

            return {'status': 'success', 'message': f"Access granted Attribute '{attribute_name}' deleted successfully"}

        # If option_name is provided, find the specific attribute value (variant option)
        option_value = request.env['product.attribute.value'].sudo().search([
            ('name', '=', option_name),
            ('attribute_id', '=', attribute.id)
        ], limit=1)

        if not option_value:
            return {'status': 'error', 'message': f"Option '{option_name}' for attribute '{attribute_name}' not found"}

        # Find the product template attribute line
        attribute_line = request.env['product.template.attribute.line'].sudo().search([
            ('product_tmpl_id', '=', product_template.id),
            ('attribute_id', '=', attribute.id)
        ], limit=1)

        if attribute_line:
            # Remove the option from the value_ids
            attribute_line.sudo().write({
                'value_ids': [(3, option_value.id)]
            })

            # If no more variants remain for the attribute, delete the attribute line entirely
            if not attribute_line.value_ids:
                attribute_line.sudo().unlink()

        return {'status': 'success', 'message': f"Access granted Option '{option_name}' deleted successfully from attribute '{attribute_name}'"}
