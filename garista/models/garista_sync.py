from odoo import models, api
import json
import requests
from datetime import datetime
from tzlocal import get_localzone

class GaristaSync(models.Model):
    _name = 'garista.sync'
    _description = 'Garista API Sync'
    
    def _sync_order_in_thread(self, order_id):
        """Run sync process in a separate thread to avoid blocking."""
        # Ensure no locks before running
        self.sync_order_in_background(order_id)

    @api.model
    def get_api_headers(self, restos_id):
        """Retrieve API headers for Garista."""
        restaurant = self.env['garista.garista'].search([('user_restos_id', '=', restos_id)])
        token = restaurant.token
        api_token = restaurant.api_token
        return {
            "x-validate-api-token": token,
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json", 
        }

    # @api.model
    # def sync_order_in_background(self, order_id):
    #     """Sync the order with Garista in the background."""
    #     order = self.env['pos.order'].browse(order_id)
    #     if not order:
    #         return
    #     if order.is_Sync == False:
    #         print("Order date and time",order.date_order)
    #         data = json.loads(order.garista_data)  # Assuming this field contains the necessary data
    #         self._sync_with_garista(order, data)
    #     else:
    #         print("No Need to Sync")
    #         return
    @api.model
    def sync_order_in_background(self, order_id, date_order=None):
        """Sync the order with Garista in the background."""
        order = self.env['pos.order'].browse(order_id)
        if not order:
            return

        if not order.is_Sync:
            # Load existing payload
            data = json.loads(order.garista_data)  # Assuming this field contains the necessary data

            # Add date_order only if it's provided
            if date_order:
                # Get system timezone dynamically
                local_tz = get_localzone()
                print("local_tz",local_tz)
                tz_abbr = datetime.now(local_tz).strftime("%Z")  # Get timezone abbreviation (e.g., "PKT", "EST")

                # Format date_order and append timezone
                order_timestamp_with_tz = f"{date_order} - {tz_abbr}"
                data["order_timestamp"] = order_timestamp_with_tz  # Add date_order to payload
            
            print("Final Data send to API",data)
            # Sync with Garista
            self._sync_with_garista(order, data)
        else:
            print("No Need to Sync")
            return

    def _sync_with_garista(self, order, data):
        print("Start Syncing")
        """Perform the actual sync with the Garista API."""
        headers = self.get_api_headers(data.get("resto_id"))
        api_url = self.env['garista.garista'].get_api_url()
        endpoint = "orders"
        url = f"{api_url}{endpoint}"
        json_payload = json.dumps(data)

        try:
            # Sending POST request to Garista API
            response = requests.post(url, headers=headers, data=json_payload)

            if response.ok:
                response_data = response.json()
                message = response_data.get("message")
                garista_order_id = response_data.get("order", {}).get("id")
                # Update the order with the Garista order ID
                if garista_order_id:
                    order.write({'garista_order_id': garista_order_id, 'is_Sync':True})
                    print(f"Order synced with Garista. Order ID: {garista_order_id}")
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Success',
                            'message': f"Order synced with Garista. Order ID: {garista_order_id}",
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': f"Error: {message} Not Sync",
                        'type': 'danger',
                        'sticky': True,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': f"Error syncing order: {response.status_code} - {response.text}",
                        'type': 'danger',
                        'sticky': True,
                    }
                }

        except Exception as e:
            print(f"Error syncing order to Garista: {str(e)}")