from odoo import http
from odoo.http import request
import base64
import json
import requests

class GaristaCategoryController(http.Controller):

    @http.route('/garista/pos_category/create',  type= 'json' ,auth='public', methods=['POST'], csrf=False)
    def create_pos_category(self, **kwargs):
        print("create_pos_category")
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

        category_name = data.get('name')
        category_image = data.get('image')
        parent_type = data.get('parent_type')
        garista_category_id = data.get('id')
        parent_category_id = request.env['garista.garista'].get_parent_category(parent_type)
        
        existing_category = request.env['pos.category'].sudo().search([
            ('garista_category_id', '=', garista_category_id)
        ], limit=1)
        
        if not existing_category:
            if category_image:
                image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
                image_url = image_base_url + category_image
                try:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image_base64 = base64.b64encode(response.content)
                except Exception as e:
                    return {'status': 'error', 'message': str(e)}

            category_vals = {
                'name': category_name,
                'image_128': image_base64,
                'parent_id':parent_category_id,
                'garista_category_id':garista_category_id
            }

            category = request.env['pos.category'].sudo().create(category_vals)

            return {'status': 'success', 'message': 'Access granted Category created successfully', 'category_id': category.id}
        else:
            return {'status': 'error', 'message': 'Category Already found'}
        
    # @http.route('/api/update_pos_category', type='json', auth='public', methods=['PUT'], csrf=False)
    # def update_category(self, **kwargs):
    #     print("update_pos_category")
    #     data = json.loads(request.httprequest.data)
    #     headers = request.httprequest.headers
    #     api_token = headers.get('api_token')
    #     username = data.get('username')

    #     if not username or not api_token:
    #         return {
    #             'status': 'error',
    #             'message': 'API token and username are required for access'
    #         }

    #     valid = request.env['garista.garista'].sudo().validate_api_token(api_token, username)
    #     print(valid)

    #     if not valid:
    #         return {
    #             'status': 'error',
    #             'message': 'API token invalid'
    #         }

    #     category_id = data.get('id')
    #     category_name = data.get('name')
    #     category_image = data.get('image')

    #     # Find the existing_category
    #     existing_category = request.env['pos.category'].sudo().search([
    #         ('garista_category_id', '=', category_id)
    #     ], limit=1)

    #     if not existing_category:
    #         return {'status': 'error', 'message': 'Category ID not found'}

    #     # update existing_category
    #     if existing_category:
    #         if category_name:
    #             existing_category.name = category_name
    #         if category_image:
    #             image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
    #             image_url = image_base_url + category_image
    #             try:
    #                 response = requests.get(image_url)
    #                 if response.status_code == 200:
    #                     image_base64 = base64.b64encode(response.content)
    #                     existing_category.image_128 = image_base64
    #             except Exception as e:
    #                 return {'status': 'error', 'message': str(e)}

    #     return {'status': 'success', 'message': 'Access granted Category updated successfully', 'category_id': existing_category.id}
    @http.route('/garista/pos_category/update', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_category(self, **kwargs):
        print("update_pos_category")
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

        category_id = data.get('id')
        category_name = data.get('name')
        category_image = data.get('image')
        parent_type = data.get('parent_type')
        parent_category_id = request.env['garista.garista'].get_parent_category(parent_type)
        # Find the existing category
        existing_category = request.env['pos.category'].sudo().search([
            ('garista_category_id', '=', category_id)
        ], limit=1)

        if not existing_category:
            return {'status': 'error', 'message': 'Category ID not found'}

        # Prepare update values
        update_values = {}

        if category_name:
            update_values['name'] = category_name

        if category_image:
            image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
            image_url = image_base_url + category_image
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                    update_values['image_128'] = image_base64
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        if parent_category_id:
            update_values['parent_id'] = parent_category_id
            
        # Perform the actual update
        if update_values:
            existing_category.sudo().write(update_values)

        return {
            'status': 'success',
            'message': 'Category updated successfully',
            'category_id': existing_category.id
        }

    @http.route('/garista/pos_category/delete', type='json', auth='public', methods=['DELETE'], csrf=False)
    def delete_category(self, **kwargs):
        print("delete_pos_category")
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

        category_id = data.get('id')

        # Find the existing_category
        category = request.env['pos.category'].sudo().search([
            ('garista_category_id', '=', category_id)
        ], limit=1)

        if not category:
            return {'status': 'error', 'message': 'Category ID not found'}
        try:
            category.sudo().unlink()
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)  # Return the exact error message from Odoo
            }

        return {'status': 'success', 'message': 'Category deleted successfully'}