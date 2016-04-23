# -*- coding: utf-8 -*-
# © 2004-2015 Odoo S.A.
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

{
    'name': 'Payment Orders Management',
    'version': '9.0.1.0.0',
    'author': 'Odoo S.A., '
              'Tecnativa, '
              'Odoo Community Association (OCA)',
    'category': 'Accounting & Finance',
    'depends': [
        'account',
    ],
    'data': [
        'data/account_payment_sequence.xml',
        'security/account_payment_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_payment_pay_view.xml',
        'wizard/account_payment_populate_statement_view.xml',
        'wizard/account_payment_create_order_view.xml',
        'views/payment_mode_view.xml',
        'views/payment_order_view.xml',
        'views/report_paymentorder.xml',
    ],
    'demo': [
        'demo/account_payment_demo.xml'
    ],
    'test': [
        'test/account_payment_demo.yml',
        'test/cancel_payment_order.yml',
        'test/payment_order_process.yml',
        'test/account_payment_report.yml',
    ],
    'installable': True,
}
