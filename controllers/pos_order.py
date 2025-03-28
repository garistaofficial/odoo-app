from odoo import http
from odoo.http import request
import json
from datetime import datetime

class PosOrderController(http.Controller):

    @http.route('/garista/pos_order/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_pos_order(self, **post):
        data = json.loads(request.httprequest.data)
        
        # Extract necessary data
        headers = request.httprequest.headers
        resto_id = data.get('resto_id')
        user_id = data.get('user_id')
        table_id = data.get('table_id')
        garista_order_id = data.get('garista_order_id')
        order_timestamp = data.get('order_timestamp')
        amount_tax = data.get('amount_tax')[0] if isinstance(data.get('amount_tax'), tuple) else data.get('amount_tax')
        amount_total = data.get('amount_total')[0] if isinstance(data.get('amount_total'), tuple) else data.get('amount_total')
        amount_paid = data.get('amount_paid')[0] if isinstance(data.get('amount_paid'), tuple) else data.get('amount_paid')
        amount_return = data.get('amount_return')[0] if isinstance(data.get('amount_return'), tuple) else data.get('amount_return')
        pos_order_lines = data.get('lines')
        api_token = headers.get('api_token')
        username = data.get('username')

        # Validate API token
        if not username or not api_token or not request.env['garista.garista'].sudo().validate_api_token(api_token, username):
            return {'status': 'error', 'message': 'Invalid API token or missing credentials'}

        config_name = request.env['pos.config'].sudo().search([
            ('garista_restaurant_id', '=', resto_id),
        ], limit=1)
        
        # Fetch open POS session
        session = request.env['pos.session'].sudo().search([
            ('state', '=', 'opened'),
            ('config_id.name', '=', config_name.name),
        ], limit=1)
        
        if not session or session.state != 'opened':
            return {'status': 'error', 'message': 'POS session is not active'}

        session_id = session.id
        session_name = session.name.split('/')[-1]  # Extract session number
        
        # Generate POS Reference
        last_orders = request.env['pos.order'].sudo().search([
            ('session_id', '=', session_id)
        ], order="id desc", limit=2)
        
        order_group, order_num = self._generate_pos_reference(last_orders)
        pos_reference = f"Order {session_name}-{order_group}-{order_num}"

        # Get User
        user = request.env['res.users'].sudo().search([("name", "=", user_id)], limit=1)

        # Process Order Timestamp
        create_date = self._process_order_timestamp(order_timestamp)
        
        #Get table ID
        table = request.env['restaurant.table'].sudo().search([("garista_table_id", "=", table_id)],limit=1)
        # Create POS Order
        order_vals = {
            'pos_reference': pos_reference,
            'user_id': user.id,
            'session_id': session.id,
            'table_id': table.id,
            'amount_tax': data.get('amount_tax', 0),
            'amount_total': data.get('amount_total', 0),
            'amount_paid': data.get('amount_paid', 0),
            'amount_return': data.get('amount_return', 0),
            'create_date': create_date,
            'garista_order_id': garista_order_id
        }
        pos_order = request.env['pos.order'].sudo().create(order_vals)
        
        # Create Order Lines
        self._create_order_lines(pos_order, pos_order_lines)
        
        return {'status': 'success', 'message': 'POS Order created successfully!', 'pos_order_id': pos_order.id}

    def _generate_pos_reference(self, last_orders):
        """Generate a unique POS order reference."""
        if last_orders:
            last_ref = last_orders[0].pos_reference
            
            if isinstance(last_ref, str):
                parts = last_ref.split('-')
                
                if len(parts) == 3:
                    last_group = int(parts[1])
                    last_order_num = int(parts[2])
                    
                    # Handle session reset scenario
                    if last_order_num == 1 and len(last_orders) > 1:
                        prev_last_order = last_orders[1].pos_reference.split('-')
                        if len(prev_last_order) == 3 and int(prev_last_order[2]) > 1:
                            order_group = str(last_group + 1).zfill(3)
                        else:
                            order_group = str(last_group).zfill(3)
                    else:
                        order_group = str(last_group).zfill(3)

                    order_num = "0001" if last_order_num >= 9999 else str(last_order_num + 1).zfill(4)
                else:
                    order_group, order_num = "001", "0001"
            else:
                order_group, order_num = "001", "0001"
        else:
            order_group, order_num = "001", "0001"
        
        return order_group, order_num

    def _process_order_timestamp(self, order_timestamp):
        """Process and format order timestamp."""
        if order_timestamp:
            try:
                return datetime.strptime(order_timestamp, "%m/%d/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return {'status': 'error', 'message': 'Invalid date format for order_timestamp. Expected format: MM/DD/YYYY HH:MM:SS'}
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _create_order_lines(self, pos_order, pos_order_lines):
        """Create POS order lines."""
        for line in pos_order_lines:
            product_id = line.get('product_id')
            price_unit = line.get('price_unit')
            qty = line.get('qty')
            # price_subtotal = line.get('price_subtotal')
            # price_subtotal_incl = line.get('price_subtotal_incl')
            extraVariant = line.get('extraVariant', [])
            # attribute_value_ids = line.get('attribute_value_ids')
            product = request.env['product.template'].sudo().search([('garista_product_id', '=', product_id)], limit=1)
            taxes = product.taxes_id
            tax = taxes[0].name
            tax_id = taxes[0].id
            tax_rate = float(tax.strip('%')) / 100 
            attribute_value_ids = []
            for topping in extraVariant:
                # no need for this because we just want attribute_value_ids
                # topping_name = topping.get('name')
                options = topping.get('options', [])
            
                # attribute = request.env['product.attribute'].sudo().search([('name', '=', topping_name)], limit=1)
    
                for option in options:
                    option_name = option.get('name')
                    price = option.get('price')
            
                    attribute_value = request.env['product.attribute.value'].sudo().search([
                        ('name', '=', option_name),
                        ('default_extra_price', '=', price)
                    ], limit=1)
         
                    attribute_value_ids.append(attribute_value.id)
            if not price_unit:
                price_unit = price
                            
            price_subtotal = qty * price   
            price_subtotal_incl =  (price_subtotal * tax_rate) + price_subtotal
            if product:
                attribute_value_ids_list = attribute_value_ids if isinstance(attribute_value_ids, list) else [attribute_value_ids]
                line_vals = {
                    'order_id': pos_order.id,
                    'product_id': product.id,
                    'full_product_name': product.name,
                    'qty': qty,
                    'price_unit': price_unit ,
                    'price_subtotal': price_subtotal,
                    'price_subtotal_incl': price_subtotal_incl,
                    'attribute_value_ids': [(6, 0, attribute_value_ids_list)],
                    'tax_ids':[(6, 0, [tax_id])]
                }
                print("Print Lines Values",line_vals) # i think it should add with order check it please.
                request.env['pos.order.line'].sudo().create(line_vals)