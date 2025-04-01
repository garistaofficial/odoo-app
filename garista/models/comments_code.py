 # @api.model
    # def create(self, vals):
    #     if 'api_password' in vals:
    #         vals['api_password'] = hashlib.sha256(vals['api_password'].encode()).hexdigest()
    #     return super(garista, self).create(vals)
        
    # @api.constrains('phone')
    # def _check_phone_number(self):
    #     phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 phone number format
    #     for record in self:
    #         if record.phone and not phone_pattern.match(record.phone):
    #             raise ValidationError("Please enter a valid phone number in international format (e.g., +123456789).")
  
  
    # def action_connect_app(self):
    #     api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
        
    #     if not api_url:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': 'Please enter the API URL in Garista Settings first.',
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }

    #     api_url = api_url.rstrip('/') + '/'
        
    #     api_path = "auth/login"
    #     url = api_url + api_path
    #     headers = self.get_api_headers()
    #     data = {
    #         "login": self.api_email,
    #         "password": self.api_password
    #     }
    #     try:
    #         # Make the API request
    #         response = requests.post(url, headers=headers, data=json.dumps(data))  

    #         if response.status_code == 200:
    #             data  = response.json()
    #             print(data)
    #             model_vals = {
    #                 'api_email': self.api_email,  # Include entered email
    #                 'api_password': self.api_password,  # Include entered password
    #                 'status': data.get('status'),
    #                 'message': data.get('message'),
    #                 'api_token': data.get('token'),
    #                 'user_id': data['user'].get('id'),
    #                 'user_first_name': data['user'].get('first_name'),
    #                 'user_last_name': data['user'].get('last_name'),
    #                 'user_phone': data['user'].get('phone'),
    #                 'user_username': data['user'].get('username'),
    #                 'name': data['user']['restos'][0].get('name') if data['user'].get('restos') else None,
    #                 'user_restos_id': data['user']['restos'][0].get('id') if data['user'].get('restos') else None
    #             }
    #             login_id = self.write(model_vals)
                
    #             # Also create Restaurant of pos.config module 
    #             pos_restaurant_vals = {
    #                 'name':model_vals.get('name'),
    #                 'module_pos_restaurant': True,
    #                 'active':True,
    #                 'garista_restaurant_id':model_vals.get('user_restos_id'),
    #                 'journal_id': self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id
    #                 }
    #             pos_config_id = self.env['pos.config'].create(pos_restaurant_vals)
    #             print(pos_config_id)
    #             print(login_id)
    #             # Create the Preparation Display and assign the newly created pos.config
    #             prep_display_vals = {
    #                 'name': model_vals.get('name'),
    #                 'company_id': self.env.company.id,
    #                 'pos_config_ids': [(6, 0, [pos_config_id.id])],  # Assign the newly created pos.config
    #                 'stage_ids': [
    #                     (0, 0, {'name': 'Accepted', 'color': '#FFC107', 'alert_timer': 0}),  # New stage "Accepted"
    #                     (0, 0, {'name': 'To prepare', 'color': '#6C757D', 'alert_timer': 10}),
    #                     (0, 0, {'name': 'Ready', 'color': '#4D89D1', 'alert_timer': 5}),
    #                     (0, 0, {'name': 'Completed', 'color': '#4ea82a', 'alert_timer': 0}),
    #                 ]
    #             }
    #             prep_display_id = self.env['pos_preparation_display.display'].create(prep_display_vals)
    #             print(prep_display_id)
    #             # Show success message
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Success',
    #                     'message': 'API connection successful and record updated!',
    #                     'type': 'success',  # 'success', 'warning', 'danger'
    #                     'sticky': False,   # If True, the message will stay visible until manually closed
    #                 }
    #             }
    #         else:
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Error',
    #                     'message': f"API Connection Failed: {response.text}",
    #                     'type': 'danger',
    #                     'sticky': True,
    #                 }
    #              }
    #     except Exception as e:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': f"API Connection Error: {str(e)}",
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #     }
    
     # def create_garista_pos_category(self, categories):
    #     image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
    #     for category in categories:
    #         name = category.get('name')
    #         image = category.get('image')  # Assuming this is a path or base64 string
    #         garista_category_id = category.get('id')
    #         parent_id = category.get('parent_category') if category.get('parent_category') else None
    #         image_url = image_base_url+image
            
    #         response = requests.get(image_url)
    #         if response.status_code == 200:
    #             image_base64 = base64.b64encode(response.content)
    #             category_vals = {'name':name, 'image_128':image_base64, 'garista_category_id': garista_category_id,'parent_id':parent_id}
    #             # category_id = self.env['pos.category'].create(category_vals)
    #             print(category_vals)
    #         else:
    #             print(f"Failed to download the image. Status code: {response.status_code}")
    #             category_vals = {'name':name, 'garista_category_id': garista_category_id, 'parent_id':parent_id}
    #             # category_id = self.env['pos.category'].create(category_vals)
    #             print(category_vals)
    
    # def update_garista_status(self):
    #     """Fetch status from API and update the status field."""
    #     endpoint = "restos/"
        
    #     api_url = self.get_api_url()
    #     if not api_url:
    #         return {'error': 'Please enter the API URL in Garista Settings first.'}
        
    #     headers = self.get_api_headers()
    #     url = f"{api_url}{endpoint}{self.user_restos_id}"
    #     print(url,headers)
    #     try:
    #         response = requests.get(url, headers=headers)
    #         if response.ok:
    #             data = response.json()
    #             status_value = data[0]['status'].capitalize() if data else 'Disconnected'
    #             self.write({'status': status_value})
    #             print(f"Updated status for ID {self.user_restos_id}: {status_value}")
    #         else:
    #             self.search([('user_restos_id', '=', self.user_restos_id)]).write({'status': 'Disconnected','last_disconnect_timestamp': datetime.now()})


    #     except Exception as e:
    #         print(f"Failed to fetch Garista API: {str(e)}")
    #         self.search([('user_restos_id', '=', self.user_restos_id)]).write({'status': 'Disconnected','last_disconnect_timestamp': datetime.now()})
        # def create_garista_pos_product(self, products):
    #     try:
    #         image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
    #         for product in products:
    #             product_id = product.get('id')
    #             product_name = product.get('name')
    #             product_category_id = product.get('category_id')
    #             product_price = product.get('price')
    #             product_isVariant = product.get('isVariant')
    #             product_image = product.get('image')
    #             image_url = image_base_url + product_image
                
    #             response = requests.get(image_url)
    #             existing_category = self.env['pos.category'].sudo().search([
    #                 ('garista_category_id', '=', product_category_id)
    #             ], limit=1)
                
    #             if response.status_code == 200:
    #                 image_base64 = base64.b64encode(response.content)
    #                 product_template_vals = {
    #                     'name': product_name,
    #                     'list_price': product_price,
    #                     'garista_product_id': product_id,
    #                     'available_in_pos': True,
    #                     'image_1920': image_base64,
    #                 }
                    
    #                 if existing_category:
    #                     product_template_vals['pos_categ_ids'] = [(6, 0, [existing_category.id])]
                    
    #                 product_template = self.env['product.template'].sudo().create(product_template_vals)
                
    #             if product_isVariant == 1:
    #                 self.create_product_variants(product, product_template)
            
    #         return self.display_notification("Success", "Products successfully created!", "success")
    #     except Exception as e:
    #         return self.display_notification("Error", str(e), "danger")
    # def get_tables(self):
    #     api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
    #     row_limit = 6  # Max tables per row
    #     spacing = 50  # Space between tables
    #     width = 150
    #     height = 150
    #     start_x = 10  # Starting X position
    #     start_y = 10  # Starting Y position
        
    #     if not api_url:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': 'Please enter the API URL in Garista Settings first.',
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }

    #     api_url = api_url.rstrip('/') + '/'
    #     api_path = "tables/"
    #     user_restos_id = self.user_restos_id
    #     headers = self.get_api_headers()
    #     url = api_url + api_path + user_restos_id

    #     try:
    #         response = requests.get(url, headers=headers)
    #         if response.ok:
    #             items = response.json()
    #             table_count = 0  # Track the number of tables added

    #             for item in items:
    #                 model_vals = []
    #                 table_name = item.get('name')
    #                 table_id = item.get('id')
    #                 table_x = item.get('x')
    #                 table_y = item.get('y')
    #                 table_shape = item.get('shape') or "square"
    #                 table_seats = item.get('seats') or 6
    #                 floor = item.get('locations')
    #                 identifier = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    #                 restaurant_id = item.get('resto_id')

    #                 existing_restaurent = self.env['pos.config'].sudo().search(
    #                     [('garista_restaurant_id', '=', restaurant_id)], limit=1
    #                 )
    #                 if not existing_restaurent:
    #                     print("Restaurant does not exist, skipping table creation.")
    #                     continue

    #                 if floor is None:
    #                     existing_floor = self.env['restaurant.floor'].sudo().search(
    #                         [('name', '=', 'Main')], limit=1
    #                     )
    #                     if not existing_floor:
    #                         print("Creating new Floor")
    #                         existing_floor = self.env["restaurant.floor"].create({
    #                             'name': 'Main',
    #                             'pos_config_ids': [(6, 0, [existing_restaurent.id])],
    #                         })
    #                 # Optional: Remove "My Company" floor if it was auto-created
    #                 unwanted_floor = self.env['restaurant.floor'].sudo().search(
    #                     [('name', '=', 'My Company'), ('pos_config_ids', 'in', [existing_restaurent.id])], limit=1
    #                 )
    #                 if unwanted_floor:
    #                     print("Removing 'My Company' floor")
    #                     unwanted_floor.unlink()
    #                 existing_table = self.env['restaurant.table'].sudo().search([
    #                 ('name', '=', table_name),
    #                 ('floor_id', '=', existing_floor.id)
    #                 ], limit=1)

    #                 if existing_table:
    #                     print(f"Table '{table_name}' already exists on the floor '{existing_floor.name}', skipping creation.")
    #                     continue     
    #                 # Calculate position
    #                 if table_x is None or table_y is None:
    #                     table_x = start_x + (table_count % row_limit) * (width + spacing)
    #                     table_y = start_y + (table_count // row_limit) * (height + spacing)

    #                 model_vals.append({
    #                     'name': item.get('name'),
    #                     'identifier': identifier,
    #                     'seats': table_seats,
    #                     'shape': table_shape,
    #                     'position_h': table_x,
    #                     'position_v': table_y,
    #                     'width': width,
    #                     'height': height,
    #                     'floor_id': existing_floor.id,
    #                     'garista_table_id':table_id
    #                 })

    #                 print("Table Data:", model_vals)
    #                 self.env['restaurant.table'].sudo().create(model_vals)
    #                 table_count += 1  # Increase the table counter

    #         else:
    #             print(f"Error: {response.status_code}, {response.text}")

    #     except Exception as e:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': f"Error: {str(e)}",
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }
    
     
     # def get_dishes(self):
    #     api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
    #     headers = self.get_api_headers()
    #     if not api_url:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': 'Please enter the API URL in Garista Settings first.',
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }

    #     api_url = api_url.rstrip('/') + '/'
    #     api_path_dishes = "dishes/"
    #     api_path_drinks = "drinks-resto/"
    #     user_restos_id = self.user_restos_id
    #     dishes_url = api_url + api_path_dishes + user_restos_id
    #     drinks_url = api_url + api_path_drinks + user_restos_id
        
    #     try:
    #         response = requests.get(dishes_url, headers=headers) 
    #         if response.ok:
    #             item = response.json()
    #             extracted_data = []
    #             for item in item:
    #                 # Create a dictionary for each dish
    #                 dish_data = {
    #                     "id": item["id"],
    #                     "name": item["name"],
    #                     "category_id": item["category_id"],
    #                     "price": item["price"],
    #                     "isVariant": item["isVariant"],
    #                     "resto_id": item["resto_id"],
    #                     "image": item.get("image1", ""),
    #                     "toppings": []
    #                 }
    #                 existing_product = self.env['product.template'].search([('garista_product_id', '=', dish_data['id'])], limit=1)
                    
    #                 if existing_product:
    #                     print(f"Product '{dish_data['name']}' already exists. Skipping...")
    #                     continue  # Skip this item if it already exists
    #                 # Extract toppings and deserialize options if necessary
    #                 for topping in item.get("toppings", []):
    #                     topping_data = {
    #                         "id": topping["id"],
    #                         "name": topping["name"],
    #                         "options": json.loads(topping["options"]) if isinstance(topping["options"], str) else topping["options"]
    #                     }
    #                     dish_data["toppings"].append(topping_data)
                    
    #                 # Add the formatted dish data to the extracted_data list
    #                 extracted_data.append(dish_data)
    #             if extracted_data:
    #                 self.create_garista_pos_product(extracted_data)
    #                 return {
    #                     'type': 'ir.actions.client',
    #                     'tag': 'display_notification',
    #                     'params': {
    #                         'title': 'Success',
    #                         'message': 'API connection successful and record updated!',
    #                         'type': 'success',  # 'success', 'warning', 'danger'
    #                         'sticky': False,   # If True, the message will stay visible until manually closed
    #                     }
    #                 }
    #             else:
    #                 return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Error',
    #                     'message': 'API connection successful but no record exist!',
    #                     'type': 'danger',
    #                     'sticky': True,
    #                 }
    #              }    
    #             # print(type(extracted_data[3]['toppings'][0]['options'][0]))
    #             # print(extracted_data[3])
    #         else:
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Error',
    #                     'message': f"Error: {response.status_code} {response.text}",
    #                     'type': 'danger',
    #                     'sticky': True,
    #                 }
    #              }   
                
    #     except Exception as e:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': f"Error: {str(e)}",
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #     }
        
    # def create_garista_pos_product(self, products):
    #     image_base_url = "https://garista.s3.eu-north-1.amazonaws.com/"
    #     for product in products:
    #         product_id = product.get('id')
    #         product_name = product.get('name')
    #         product_category_id = product.get('category_id')
    #         product_price = product.get('price')
    #         product_isVariant = product.get('isVariant')
    #         product_image = product.get('image')
    #         image_url = image_base_url+product_image
            
    #         response = requests.get(image_url)
    #         existing_category = self.env['pos.category'].sudo().search([('garista_category_id', '=', product_category_id)], limit=1)
    #         if response.status_code == 200:
    #             image_base64 = base64.b64encode(response.content)
    #             if existing_category:
    #                 product_template = self.env['product.template'].sudo().create({
    #                     'name': product_name,
    #                     'pos_categ_ids': [(6, 0, [existing_category.id])],
    #                     'list_price':product_price,
    #                     'garista_product_id':product_id,
    #                     'available_in_pos':True,
    #                     'image_1920': image_base64,
    #                 })
    #                 print(product_template,"Product has been Created")
    #             else:
    #                 product_template = self.env['product.template'].sudo().create({
    #                     'name': product_name,
    #                     'image_1920': image_base64,
    #                     'list_price':product_price,
    #                     'garista_product_id':product_id,
    #                     'available_in_pos':True,
    #                 })
    #                 print(product_template,"Product has been Created")
    #         if product_isVariant == 1:
    #             for topping in product.get("toppings", []):
    #                 # topping_id = topping.get("id")
    #                 topping_name = topping.get("name")
    #                 options = topping.get("options", [])
    #                 attribute  = self.env['product.attribute'].sudo().search([('name', '=', topping_name)], limit=1)
    #                 if not attribute :
    #                     attribute  = self.env['product.attribute'].sudo().create({
    #                         'name': topping_name,
    #                         'display_type': 'multi-checkbox',
    #                     })
    #                 attribute_value_ids = []
    #                 for option_data in options:
    #                     name = option_data['name']
    #                     extra_price = option_data['price']
    #                     option_value = self.env['product.attribute.value'].sudo().search([
    #                         ('name', '=', name),
    #                         ('attribute_id', '=', attribute.id)
    #                     ], limit=1)
    #                     if not option_value:
    #                         option_value = self.env['product.attribute.value'].sudo().create({
    #                             'name': name,
    #                             'attribute_id': attribute.id,
    #                             'default_extra_price': extra_price
    #                         })
    #                     else:
    #                         option_value.sudo().write({
    #                             'default_extra_price': extra_price
    #                         })

    #                     attribute_value_ids.append(option_value.id)
    #                 self.env['product.template.attribute.line'].sudo().create({
    #                     'product_tmpl_id': product_template.id,
    #                     'attribute_id': attribute.id,
    #                     'value_ids': [(6, 0, attribute_value_ids)]
    #                 })
                    
     
    # def get_tables(self):
    #     api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
    #     row_limit = 6  # Max tables per row
    #     spacing = 50  # Space between tables
    #     width = 150
    #     height = 150
        
        
    #     if not api_url:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': 'Please enter the API URL in Garista Settings first.',
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }

    #     api_url = api_url.rstrip('/') + '/'
    #     api_path = "tables/"
    #     user_restos_id = self.user_restos_id
    #     headers = self.get_api_headers()
    #     url = api_url + api_path + user_restos_id
    #     try:
    #         response = requests.get(url , headers=headers)
    #         if response.ok:
    #             items = response.json()
                
    #             for item in items:
    #                 model_vals = []
    #                 table_x = item.get('x')
    #                 table_y = item.get('y')
    #                 table_shape = item.get('shape')
    #                 table_seats = item.get('seats')
    #                 floor = item.get('locations')
    #                 identifier = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    #                 restaurant_id = item.get('resto_id')
    #                 existing_restaurent = self.env['pos.config'].sudo().search([('garista_restaurant_id', '=', restaurant_id)], limit=1)
    #                 if not existing_restaurent:
    #                     print("Restaurent is Not Exist so no need of Floor or Table thanku")
    #                     continue
    #                 if floor is None:
    #                     existing_floor = self.env['restaurant.floor'].sudo().search([('name', '=', 'Main')], limit=1)
    #                     if not existing_floor:
    #                         print("Now Creating new Floor")
    #                         existing_floor = self.env["restaurant.floor"].create({
    #                         'name': 'Main',
    #                         'pos_config_ids': [(6, 0, [existing_restaurent.id])],
    #                     })
    #                 last_table = self.env['restaurant.table'].sudo().search([('floor_id','=',existing_floor.id)], order="id desc", limit=1)
    #                 new_x = last_table.position_h + width + spacing if last_table else 10
    #                 new_y = last_table.position_v if last_table else 10
    #                 table_count = self.env['restaurant.table'].sudo().search_count([('floor_id','=',existing_floor.id)])        
    #                 print("table count",table_count)
    #                 if table_count == 0:
    #                     new_y = 10
    #                 if table_x is None or table_y is None or table_shape is None or table_seats is None:
    #                     if table_count % row_limit == 0:  # Move to a new row
    #                         new_x = 100
    #                         new_y += height + spacing
    #                     table_x = new_x
    #                     table_y = new_y
    #                     table_shape = "square"
    #                     table_seats = 6
    #                 model_vals.append({
    #                     'name': item.get('name'),
    #                     'identifier': identifier,
    #                     'seats': table_seats,
    #                     'shape': table_shape,
    #                     'position_h': table_x,
    #                     'position_v': table_y,
    #                     'width': width,
    #                     'height':height,
    #                     'floor_id': existing_floor.id
    #                 })

    #                 # Print extracted values
    #                 print("Table Data is here",model_vals)
    #                 self.env['restaurant.table'].sudo().create(model_vals)
                
    #         else:
    #             print(f"Error: {response.status_code}, {response.text}")

    #     except Exception as e:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': f"Error: {str(e)}",
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #     }
       
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


 # def get_tables(self):
    #     api_url = self.env['ir.config_parameter'].sudo().get_param('garista.api_url')
    #     row_limit = 6  # Max tables per row
    #     spacing = 50  # Space between tables
    #     width = 150
    #     height = 150
    #     start_x = 10  # Starting X position
    #     start_y = 10  # Starting Y position

    #     if not api_url:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': 'Please enter the API URL in Garista Settings first.',
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }

    #     api_url = api_url.rstrip('/') + '/'
    #     api_path = "tables/"
    #     user_restos_id = self.user_restos_id
    #     headers = self.get_api_headers()
    #     url = api_url + api_path + user_restos_id

    #     try:
    #         response = requests.get(url, headers=headers)
    #         if response.ok:
    #             items = response.json()
    #             new_tables_count = 0  # Track newly added tables
    #             total_tables = len(items)  # Get the total number of tables from API

    #             for item in items:
    #                 model_vals = []
    #                 table_name = item.get('name')
    #                 table_id = item.get('id')
    #                 table_x = item.get('x')
    #                 table_y = item.get('y')
    #                 table_shape = item.get('shape') or "square"
    #                 table_seats = item.get('seats') or 6
    #                 floor = item.get('locations')
    #                 identifier = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    #                 restaurant_id = item.get('resto_id')

    #                 existing_restaurent = self.env['pos.config'].sudo().search(
    #                     [('garista_restaurant_id', '=', restaurant_id)], limit=1
    #                 )
    #                 if not existing_restaurent:
    #                     print("Restaurant does not exist, skipping table creation.")
    #                     continue

    #                 if floor is None:
    #                     existing_floor = self.env['restaurant.floor'].sudo().search(
    #                         [('name', '=', 'Main')], limit=1
    #                     )
    #                     if not existing_floor:
    #                         print("Creating new Floor")
    #                         existing_floor = self.env["restaurant.floor"].sudo().create({
    #                             'name': 'Main',
    #                             'pos_config_ids': [(6, 0, [existing_restaurent.id])],
    #                         })
                    
    #                 # Remove "My Company" auto-created floor
    #                 unwanted_floor = self.env['restaurant.floor'].sudo().search(
    #                     [('name', '=', 'My Company'), ('pos_config_ids', 'in', [existing_restaurent.id])], limit=1
    #                 )
    #                 if unwanted_floor:
    #                     print("Removing 'My Company' floor")
    #                     unwanted_floor.unlink()

    #                 existing_table = self.env['restaurant.table'].sudo().search([
    #                     ('name', '=', table_name),
    #                     ('floor_id', '=', existing_floor.id)
    #                 ], limit=1)

    #                 if existing_table:
    #                     print(f"Table '{table_name}' already exists on the floor '{existing_floor.name}', skipping creation.")
    #                     continue  # Skip existing tables
                    
    #                 # Calculate position
    #                 if table_x is None or table_y is None:
    #                     table_x = start_x + (new_tables_count % row_limit) * (width + spacing)
    #                     table_y = start_y + (new_tables_count // row_limit) * (height + spacing)

    #                 model_vals.append({
    #                     'name': table_name,
    #                     'identifier': identifier,
    #                     'seats': table_seats,
    #                     'shape': table_shape,
    #                     'position_h': table_x,
    #                     'position_v': table_y,
    #                     'width': width,
    #                     'height': height,
    #                     'floor_id': existing_floor.id,
    #                     'garista_table_id': table_id
    #                 })

    #                 print("Table Data:", model_vals)
    #                 self.env['restaurant.table'].sudo().create(model_vals)
    #                 new_tables_count += 1  # Increase the table counter

    #             # Display appropriate message
    #             if new_tables_count > 0:
    #                 return {
    #                     'type': 'ir.actions.client',
    #                     'tag': 'display_notification',
    #                     'params': {
    #                         'title': 'Success',
    #                         'message': f"{new_tables_count} new table(s) created!",
    #                         'type': 'success',
    #                         'sticky': False,
    #                     }
    #                 }
    #             elif new_tables_count == 0 and total_tables > 0:
    #                 return {
    #                     'type': 'ir.actions.client',
    #                     'tag': 'display_notification',
    #                     'params': {
    #                         'title': 'Info',
    #                         'message': "All tables already exist.",
    #                         'type': 'info',
    #                         'sticky': False,
    #                     }
    #                 }
    #             else:
    #                 return {
    #                     'type': 'ir.actions.client',
    #                     'tag': 'display_notification',
    #                     'params': {
    #                         'title': 'Info',
    #                         'message': "No tables found in the API response.",
    #                         'type': 'info',
    #                         'sticky': False,
    #                     }
    #                 }

    #         else:
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Error',
    #                     'message': f"Error: {response.status_code}, {response.text}",
    #                     'type': 'danger',
    #                     'sticky': True,
    #                 }
    #             }

    #     except Exception as e:
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Error',
    #                 'message': f"Error: {str(e)}",
    #                 'type': 'danger',
    #                 'sticky': True,
    #             }
    #         }