from odoo import api, models
import json
import requests
class PosPreparationOrder(models.Model):
    _inherit = 'pos_preparation_display.order'
    

    def change_order_stage(self, stage_id, preparation_display_id):
        """Print order stage changes in the preparation display."""
        self.ensure_one()
        old_stage = self.order_stage_ids[-1].stage_id.name if self.order_stage_ids else "Not Started"


        # Call the original method to change the stage
        current_stage = super().change_order_stage(stage_id, preparation_display_id)

        new_stage = self.env['pos_preparation_display.stage'].browse(stage_id).name
        pos_order = self.env['pos.order'].search([('id', '=', self.pos_order_id.id)], limit=1)
        if pos_order:
            self.update_order_status(pos_order, new_stage)
            
        print(f"Preparation Order ID {self.id} stage changed from '{old_stage}' to '{new_stage}'")
        # print(f"Garista Order ID: {garista_order_id}")

        return current_stage

    def done_orders_stage(self, preparation_display_id):
        """Print when an order reaches the final stage (Done)."""
        preparation_display = self.env['pos_preparation_display.display'].browse(preparation_display_id)
        last_stage = preparation_display.stage_ids[-1]

        for order in self:
            old_stage = order.order_stage_ids[-1].stage_id.name if order.order_stage_ids else "Not Started"

            # Call the original method to mark the order as done
            super().done_orders_stage(preparation_display_id)
            pos_order = order.env['pos.order'].search([('id', '=', order.pos_order_id.id)], limit=1)
            if pos_order:
                self.update_order_status(pos_order, "Done")
            # Get garista_order_id using self.id
            print(f"Done Preparation Order ID {order.id} stage changed from '{old_stage}' to 'Done'")
            
    def update_order_status(self, pos_order, new_stage):
        print("Code Refactor Call")
        garista_order_id = pos_order.garista_order_id
        restaurant = pos_order.name
        if "/" in restaurant:
            resto_name = restaurant.split("/")[0]
            print("Resto Name",resto_name)
        if resto_name:
            pos_config = self.env["pos.config"].search([("name", "=", resto_name)], limit=1)
            resto_id = pos_config.garista_restaurant_id if pos_config else None    
            headers = self.env['garista.sync'].get_api_headers(resto_id)
            api_url = self.env['garista.garista'].get_api_url()
            endpoint = "orders/"
            url = f"{api_url}{endpoint}{garista_order_id}"
            if new_stage == 'To prepare':
                data = {
                        "status": "Preparing"
                    }
            elif new_stage == 'Ready':
                data = {
                        "status": "Ready"
                    }
            elif new_stage == 'Served':  
                data = {
                        "status": "Served"
                    }  
            elif new_stage == 'Done':
                data = {
                        "status": "Completed"
                    } 
            else:
                 data = {
                        "status": "Accepted"
                    }    
            json_payload = json.dumps(data)
            print(json_payload,headers,url)
            response = requests.put(url, headers=headers, data=json_payload)   
            if response.status_code == 200:
                print("Request successful:", response.json())
            else:
                print(f"Request failed with status code {response.status_code}: {response.text}")