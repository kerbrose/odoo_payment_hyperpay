# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Payment Provider: Hyperpay",
    'version': '19.0.0.1.2',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider which supports Hyperpay.",
    'description': "for development and support visit www.strategyfa.com ",
    'author': "Khaled Said (kerbrose)",
    'website': 'https://kerbrose.github.io/',
    'depends': [
        'payment',
        'web',
    ],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_hyperpay_templates.xml',

        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'payment_hyperpay_sfa/static/src/xml/payment_form_template.xml',
            'payment_hyperpay_sfa/static/src/xml/hyperpay_dialog.xml',
            'payment_hyperpay_sfa/static/src/js/generate_blob.js',
            'payment_hyperpay_sfa/static/src/js/hyperpay_dialog.js',
            'payment_hyperpay_sfa/static/src/js/payment_form.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
    "currency ": "USD",
    "price": 120,
}
