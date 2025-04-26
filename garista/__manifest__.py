# -*- coding: utf-8 -*-
{
    'name': "Garista - Odoo POS Sync",
    'summary': "Seamlessly sync orders, products, and categories between Odoo POS and Garista App.",
    'description': """
Garista is an all-in-one order management solution that syncs orders from **Odoo POS** to the **Garista App**, along with product categories and pricing.
    
Features:
- Real-time order sync between **Odoo POS** and **Garista Order**.
- Sync all **products, categories, and tables** automatically.
- Designed for **restaurants, cafés, and hotels**.
    """,
    'author': "Garista Team",
    'website': "https://www.garista.net/",
    'category': 'Point of Sale',
    
    # Web icon for the dashboard
    'icon': '/garista/static/description/icon.png',
    
    # Dependencies
    'depends': ['base', 'point_of_sale', 'web', 'product', 'pos_restaurant'],
    
    # Assets for backend functionality
    'assets': {
        'point_of_sale._assets_pos': [
            'garista/static/src/js/pos_order_sync.js',
        ],
    },
    
    # Always loaded data files
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/url_setting.xml',
        'views/pos_category_views.xml',
        'views/product_template.xml',
        'data/garista_cron.xml',
    ],
    
    # Demo data (only loaded in demonstration mode)
    'demo': [
        'demo/demo.xml',
    ],

    # Installation settings
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['tzlocal'],
    },
}
