from odoo import models, fields, api
import json

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, vals):
        print("Creating POS Order with values:", json.dumps(vals, indent=4))
        total_amount = vals.get("amount_total", 0)
        table_id = vals.get("table_id", None)

        # Ensure "lines" is a list
        lines = vals.get("lines", [])
        if not isinstance(lines, list):  
            print("Unexpected type for 'lines':", type(lines), lines)  # Debugging
            lines = []  # Default to empty list to avoid error

        # Extract restaurant name from the first product's "name" field
        resto_name = None
        if lines:
            first_product = lines[0]
            if isinstance(first_product, (list, tuple)) and len(first_product) > 2:
                first_product_name = first_product[2].get("name", "")
                if "/" in first_product_name:
                    resto_name = first_product_name.split("/")[0]  # Extract 'rastau' from 'rastau/0020'

        # Get garista_restaurant_id from pos.config using resto_name
        resto_id = None
        if resto_name:
            pos_config = self.env["pos.config"].search([("name", "=", resto_name)], limit=1)
            resto_id = pos_config.garista_restaurant_id if pos_config else None

        # Get garista_table_id from pos.table using table_id
        table_garista_id = None
        if table_id:
            pos_table = self.env["restaurant.table"].search([("id", "=", table_id)], limit=1)
            table_garista_id = pos_table.garista_table_id if pos_table else None

        # Build cartItems list
        cart_items = []
        for line in lines:
            if not isinstance(line, (list, tuple)) or len(line) < 3:
                print(f"Skipping invalid line: {line}")  # Debugging
                continue

            line_data = line[2]

            item = {
                "type": "",
                "id": "",
                "quantity": line_data.get("qty", 0),
                "comment": line_data.get("customer_note", ""),
                "toppings": [],
                "ingredients": [],
                "extraVariant": []
            }

            if line_data.get("product_id"):
                product = self.env["product.template"].browse(line_data["product_id"])
                if product.exists():
                    item['id'] = product.garista_product_id
                    if product.pos_categ_ids:
                        pos_category = product.pos_categ_ids[0]
                        parent_name = pos_category.parent_id.name if pos_category.parent_id else None
                        if parent_name == "Food":
                            item['type'] = "dish"
                        elif parent_name == "Drink":
                            item['type'] = "drink"
                        else:
                            item['type'] = "dish"
                else:
                    print("Products not synced")
                    continue

            # Extract toppings from attribute_value_ids
            if line_data.get("attribute_value_ids"):
                attribute_value = self.env["product.attribute.value"].browse(line_data["attribute_value_ids"][0])
                print("Attributes Data", attribute_value)
                if attribute_value.exists():
                    attribute_name = attribute_value.attribute_id.name if attribute_value.attribute_id else "Custom"
                    attribute_garista_id = attribute_value.attribute_id.garista_attribute_id if attribute_value.attribute_id else "0"
                    print("Name and Garista ID",attribute_name,)
                    item["extraVariant"].append({
                        "id": attribute_garista_id,
                        "name": attribute_name,
                        "option": [{
                            "name": attribute_value.name,
                            "price": attribute_value.default_extra_price
                        }]
                    })

            cart_items.append(item)

        # Build final data object
        data = {
            "total": total_amount,
            "status": "Accepted",
            "table_id": table_garista_id,
            "resto_id": resto_id,
            "cartItems": cart_items
        }

        print("Generated API Data:", json.dumps(data, indent=4))  # Debugging output

        # Get all attributes with their options
        attributes = self.env['product.attribute'].search([])
        attribute_data = []
        for attribute in attributes:
            values = self.env['product.attribute.value'].search([('attribute_id', '=', attribute.id)])
            values_data = [{
                'value_id': value.id,
                'option_name': value.name,
                'default_extra_price': value.default_extra_price
            } for value in values]
            attribute_data.append({
                'attribute_id': attribute.id,
                'attribute_name': attribute.name,
                'values': values_data
            })

        order = super(PosOrder, self).create(vals)
        order.garista_data = json.dumps(data)
        return order

    def add_payment(self, data):
        print("Processing Payment with details:", json.dumps(data, indent=4))
        return super(PosOrder, self).add_payment(data)

    def get_api_headers(self, restos_id):
        restaurent = self.env['garista.garista'].search([('user_restos_id', '=', restos_id)])
        return {
            "x-validate-api-token": restaurent.token,
            "Authorization": f"Bearer {restaurent.api_token}",
            "Content-Type": "application/json",
        }

    def write(self, vals):
        if "state" in vals and vals["state"] == "paid":
            for order in self:
                try:
                    data = json.loads(order.garista_data)
                    resto_id = data.get("resto_id")
                    result = super(PosOrder, self).write(vals)
                    if resto_id:
                        self.env['garista.sync'].sync_order_in_background(order.id)
                        print("Syncing order to Garista API in background.")
                    else:
                        print("Resto ID missing, unable to sync.")
                    # order.garista_data = ""  # Clear after syncing
                except Exception as e:
                    print(f"Error processing order {order.id}: {str(e)}")

        return super(PosOrder, self).write(vals)


class PosOrderLineCustom(models.Model):
    _inherit = 'pos.order.line'

    def unlink(self):
        """Check if all order lines are deleted, then log order cancellation."""
        order_ids = self.mapped('order_id')  # Get affected orders before deleting lines
        res = super(PosOrderLineCustom, self).unlink()

        for order in order_ids:
            remaining_lines = self.env['pos.order.line'].search_count([('order_id', '=', order.id)])

            if remaining_lines == 0:
                print(f"Order Canceled: Order ID {order.id}, Reference: {order.pos_reference}")

        return res
# from odoo import models, fields, api
# import json
# import requests
# # from models import get_api_url
# class PosOrder(models.Model):
#     _inherit = 'pos.order'

    
#     @api.model
#     def create(self, vals):
#         print("Creating POS Order with values:", json.dumps(vals, indent=4))
#         total_amount = vals.get("amount_total", 0)
#         table_id = vals.get("table_id", None)

#         # Extract restaurant name from the first product's "name" field
#         resto_name = None
#         if vals.get("lines"):
#             first_product_name = vals["lines"][0][2].get("name", "")
#             if "/" in first_product_name:
#                 resto_name = first_product_name.split("/")[0]  # Extract 'rastau' from 'rastau/0020'

#         # Get garista_restaurant_id from pos.config using resto_name
#         resto_id = None
#         if resto_name:
#             pos_config = self.env["pos.config"].search([("name", "=", resto_name)], limit=1)
#             resto_id = pos_config.garista_restaurant_id if pos_config else None

#         # Get garista_table_id from pos.table using table_id
#         table_garista_id = None
#         if table_id:
#             pos_table = self.env["restaurant.table"].search([("id", "=", table_id)], limit=1)
#             table_garista_id = pos_table.garista_table_id if pos_table else None

#         # Build cartItems list
#         cart_items = []
#         for line in vals.get("lines", []):
#             line_data = line[2]

#             item = {
#                 "type": "",
#                 "id":"",
#                 "quantity": line_data.get("qty"),
#                 "comment": line_data.get("customer_note") or "",
#                 "toppings": [],
#                 "ingredients": [],
#                 "extraVariant": []
#             }
#             if line_data.get("product_id"):
#                 product = self.env["product.template"].browse(line_data["product_id"])
#                 if product.exists():
#                     item['id'] = product.garista_product_id
#                     if product.pos_categ_ids:
#                         pos_category = product.pos_categ_ids[0]  # Take the first category
#                         parent_name = pos_category.parent_id.name if pos_category.parent_id else None
#                         if parent_name == "Food":
#                             item['type'] = "dish"
#                         elif parent_name == "Drink":
#                              item['type'] = "drink"
#                         else:
#                             item['type'] = "dish"        
#                 else:
#                     print("Products not sync")
#                     continue
#             # Extract toppings from attribute_value_ids
#             if line_data.get("attribute_value_ids"):
#                 # Fetch the attribute value record based on the given ID
#                 attribute_value = self.env["product.attribute.value"].browse(line_data["attribute_value_ids"][0])

#                 if attribute_value.exists():
#                     # Extract attribute name from product.attribute
#                     attribute_name = attribute_value.attribute_id.name if attribute_value.attribute_id else "Custom"
#                     attribute_garista_id = attribute_value.attribute_id.garista_attribute_id if attribute_value.attribute_id else "0"
#                     # Append data into toppings
#                     item["toppings"].append({
#                         "id": attribute_garista_id,
#                         "name": attribute_name,  # Name of the product attribute (e.g., "Size", "Color")
#                         "option": [{
#                             "name": attribute_value.name,  # Name of the attribute value (e.g., "XL", "Red")
#                             "price": attribute_value.default_extra_price  # Extra price for this value
#                         }]
#                     })

#             cart_items.append(item)

#         # Build final data object
#         data = {
#             "total": total_amount,
#             "status": "Accepted",
#             "table_id": table_garista_id,  # Mapped table_id
#             "resto_id": resto_id,  # Mapped restaurant_id
#             "cartItems": cart_items
#         }

#         print("Generated API Data:", json.dumps(data, indent=4))  # Debugging output
#          # Get all attributes with their options
#         attributes = self.env['product.attribute'].search([])

#         # Store the attribute data
#         attribute_data = []
#         for attribute in attributes:
#             values = self.env['product.attribute.value'].search([('attribute_id', '=', attribute.id)])

#             # Store attribute options
#             values_data = [{
#                 'value_id': value.id,
#                 'option_name': value.name,
#                 'default_extra_price': value.default_extra_price
#             } for value in values]

#             # Store the complete attribute information
#             attribute_data.append({
#                 'attribute_id': attribute.id,
#                 'attribute_name': attribute.name,
#                 'values': values_data
#             })

#         order = super(PosOrder, self).create(vals)
#         order.garista_data = json.dumps(data)
#         return order
#     def add_payment(self, data):
#         """Override to log payment details when payment is added"""
#         print("Processing Payment with details:", json.dumps(data, indent=4))
#         res = super(PosOrder, self).add_payment(data)
#         return res
    
#     def get_api_headers(self,restos_id):
#         restaurent = self.env['garista.garista'].search([('user_restos_id', '=', restos_id)])
#         token = restaurent.token
#         api_token = restaurent.api_token
#         return {
#             "x-validate-api-token": token,
#             "Authorization": f"Bearer {api_token}",
#             "Content-Type": "application/json", 
#             }
#     def write(self, vals):
#         """Override write method to update order and then sync to Garista."""
#         if "state" in vals and vals["state"] == "paid":
#             for order in self:
#                 try:
#                     # Retrieve stored API data from garista_data field
#                     data = json.loads(order.garista_data)
#                     resto_id = data.get("resto_id")
                    
#                     # Perform standard write first
#                     result = super(PosOrder, self).write(vals)
#                     # If headers and API URL are available, call the sync process in background
#                     if resto_id:
#                         # Call the background sync process for Garista
#                         self.env['garista.sync'].sync_order_in_background(order.id)
#                         print("Syncing order to Garista API in background.")
#                     else:
#                         print("Resto ID missing, unable to sync.")
                    
#                     # Clear garista data field after syncing
#                     order.garista_data = ""

#                 except Exception as e:
#                     print(f"Error processing order {order.id}: {str(e)}")
          
#         return super(PosOrder, self).write(vals)
    
    # def write(self, vals):
    #     if "state" in vals and vals["state"] == "paid":
    #         for order in self:
    #             try:
    #                 # Retrieve stored API data
    #                 data = json.loads(order.garista_data)
    #                 # data["status"] = "Paid"  # Update status in the JSON
    #                 resto_id = data.get("resto_id")
    #                 # print("Order Paid, Final Data:", json.dumps(data, indent=4))  # Print after payment
    #                 headers = self.get_api_headers(resto_id)
    #                 garista = self.env["garista.garista"]
    #                 api_url = garista.get_api_url()
    #                 if headers and api_url:
    #                     result = self.creat_garista_order(api_url,headers,data)
    #                     message = result.get("message", "Not Sync")
    #                     garista_order_id = result.get("id", "0")
    #                     vals["garista_order_id"] = garista_order_id 
    #                     print(message,garista_order_id)
    #                 else:
    #                     print("Any issue on header")    
    #                 order.garista_data = ""
    #             except Exception as e:
    #                 print("Error retrieving order data:", str(e))
          
    #     return super(PosOrder, self).write(vals)
       
    # def creat_garista_order(self,api_url,headers,data):
    #     endpoint = "orders"
    #     try:
    #         api_url = api_url
    #         headers = headers
    #         data = data
    #         url = f"{api_url}{endpoint}"
    #         json_payload = json.dumps(data)
    #         # Send the POST request
    #         response = requests.post(url, headers=headers, data=json_payload)
    #         if response.ok:
    #             response_data =  response.json()
    #             return {
    #             "message": response_data.get("message"),
    #             "id": response_data.get("order", {}).get("id")
    #             }
    #         return {'error': f"Error: {response.status_code} {response.text}"}
    #     except Exception as e:
    #         return {"Error", str(e), "danger"}
        # tree_view_fields = [
        #     'name', 'session_id', 'date_order', 'config_id', 'pos_reference',
        #     'partner_id', 'user_id', 'amount_total', 'state'
        # ]

        # product_data = self._get_product_data(order)
        # category_data = self._get_category_data(order)

        # order_data = {}
        # for field in tree_view_fields:
        #     if field == 'partner_id':
        #         order_data[field] = order.partner_id.name if order.partner_id else 'N/A'
        #     elif field == 'session_id':
        #         order_data[field] = order.session_id.name if order.session_id else 'N/A'
        #     elif field == 'user_id':
        #         order_data[field] = order.user_id.name if order.user_id else 'N/A'
        #     elif field == 'config_id':
        #         order_data[field] = order.config_id.name if order.config_id else 'N/A'
        #     elif field == 'date_order':
        #         order_data[field] = order.date_order.strftime('%Y-%m-%d %H:%M:%S') if order.date_order else 'N/A'
        #     else:
        #         order_data[field] = getattr(order, field, 'N/A')

        # order_data['products'] = product_data
        # order_data['categories'] = category_data

        # json_data = json.dumps(order_data, indent=4)
        # print("POS Order Created:", json_data)

        # return order

    
    # def _get_product_data(self, order):
    #     products = []
    #     print("Fetching product data for order:", order.name)
    #     for line in order.lines:
    #         extra_variants = self._get_product_toppings(line.product_id)
    #         product_info = {
    #             'product_name': line.product_id.name,
    #             'pack_lot_ids': [lot.lot_name for lot in line.pack_lot_ids] if line.pack_lot_ids else [],
    #             'quantity': line.qty,
    #             'price_unit': line.price_unit,
    #             'discount': line.discount,
    #             'tax_ids_after_fiscal_position': [tax.name for tax in line.tax_ids_after_fiscal_position] if line.tax_ids_after_fiscal_position else [],
    #             'price_subtotal': line.price_subtotal,
    #             'price_subtotal_incl': line.price_subtotal_incl,
    #             'extra_variants': extra_variants
    #         }
    #         print("Product Info:", json.dumps(product_info, indent=4))
    #         products.append(product_info)
    #     return products

    # def _get_product_toppings(self, product):
    #     extra_variants = []
    #     print("Fetching toppings for product:", product.name)
    #     for attribute_line in product.attribute_line_ids:
    #         attribute = {
    #             'attribute_name': attribute_line.attribute_id.name,
    #             'attribute_values': [value.name for value in attribute_line.value_ids]
    #         }
    #         print("Topping Info:", json.dumps(attribute, indent=4))
    #         extra_variants.append(attribute)
    #     return extra_variants

    # def _get_category_data(self, order):
    #     categories = []
    #     print("Fetching category data for order:", order.name)
    #     for line in order.lines:
    #         category_name = line.product_id.categ_id.name if line.product_id.categ_id else 'N/A'
    #         categories.append(category_name)
    #     print("Categories:", json.dumps(categories, indent=4))
    #     return categories

