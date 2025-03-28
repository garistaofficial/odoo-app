from odoo import http
from odoo.http import request
import json
import requests
import base64

class APIAuthController(http.Controller):

    @http.route('/api/connectivity_check', type='json', auth='public', methods=['POST'], csrf=False)
    def connectivity_check(self, **kwargs):
        print("Received request for connectivity check")

        # Load request data
        data = json.loads(request.httprequest.data)
        headers = request.httprequest.headers
        api_token = headers.get('api_token')
        username = data.get('username')

        # Check if API token and username are provided
        if not username or not api_token:
            return {
                'status': 'error',
                'message': 'API token and username are required for access'
            }

        # Validate API token
        valid = request.env['garista.garista'].sudo().validate_api_token(api_token, username)
        print(f"API token validation result: {valid}")

        if not valid:
            return {
                'status': 'error',
                'message': 'API token invalid'
            }

        # If API token is valid, return the connectivity check response
        return {
            'status': 'success',
            'message': 'Server is reachable',
        }

    @http.route('/api/get_token', type='json', auth='public', methods=['POST'], csrf=False)
    def get_api_token(self, **kwargs):
        data = json.loads(request.httprequest.data)
        print("get_api_token")
        username = data.get('username')
        password = data.get('password')
        token = data.get('token')

        if not username or not password or not token:
            return {
                'status': 'error',
                'message': 'Username, password, and token are required to generate an API token'
            }

        garista = request.env['garista.garista'].sudo().search([('api_email', '=', username)], limit=1)

        if garista.api_password == password and garista.token == token:
            if garista.api_token:
                return {
                    'status': 'success',
                    'message': 'Existing API token found',
                    'api_token': garista.api_token
                }
            else:
                return {
                'status': 'Failed',
                'message': 'Please Login First on Odoo with you Garista Credentials, then try again ',
                'api_token': token
            }
            # token = garista.generate_token()
            # garista.sudo().write({'api_token': token})
        else:
            return {
                'status': 'error',
                'message': 'No access found for this user'
            }
