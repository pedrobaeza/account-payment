# -*- coding: utf-8 -*-
# © 2004-2015 Odoo S.A.
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import api, fields, models


class PaymentMode(models.Model):
    _name= 'payment.mode'
    _description= 'Payment Mode'

    name = fields.Char(
        string='Name', required=True, help='Mode of Payment')
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank', string="Bank account",
        help='Bank Account for the Payment Mode',
        domain="[('partner_id', '=', partner_id)]")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one(
        comodel_name='res.partner', related='company_id.partner_id',
        string='Partner', store=True)
