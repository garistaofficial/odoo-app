# -*- coding: utf-8 -*-
{
    'name': "garista",
    'icon': '/garista/static/description/icon.png',  # Web icon for the dashboard
    'installable': True,
    'application': True,
    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
        Garista is Order Menu App ,it's make sync between odoo POS to APP
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale','web','product','pos_restaurant'],
    'assets': {
    'web.assets_backend': [
        'garista/static/src/js/garista_form.js',
            ],
    },
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/url_setting.xml',
        'views/pos_category_views.xml',
        'views/product_template.xml',
        'data/garista_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

