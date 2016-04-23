# -*- coding: utf-8 -*-
# © 2004-2015 Odoo S.A.
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import api, models, fields


class PaymentOrder(models.Model):
    _name = 'payment.order'
    _description = 'Payment Order'
    _rec_name = 'reference'
    _order = 'id desc'

    date_scheduled = fields.Date(
        string='Scheduled Date', states={'done':[('readonly', True)]},
        help='Select a date if you have chosen Preferred Date to be fixed.')
    reference = fields.Char(
        string='Reference', required=True, default='/',
        states={'done': [('readonly', True)]}, copy=False)
    mode = fields.Many2one(
        comodel_name='payment.mode', string='Payment Mode', index=True,
        required=True, states={'done': [('readonly', True)]},
        help='Select the Payment Mode to be applied.')
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('cancel', 'Cancelled'),
                   ('open', 'Confirmed'),
                   ('done', 'Done')],
        string='Status', select=True, copy=False, default='draft',
        help='When an order is placed the status is \'Draft\'.\n'
             'Once the bank is confirmed the status is set to \'Confirmed\'.\n'
             'Then the order is paid the status is \'Done\'.')
    line_ids = fields.One2many(
        comodel_name='payment.line', inverse_name='order_id',
        string='Payment lines', states={'done': [('readonly', True)]})
    total = fields.Float(
        compute="_compute_total", string="Total", store=True)
    user_id = fields.Many2one(
        comodel_name='res.users', string='Responsible',
        required=True, states={'done': [('readonly', True)]},
        default=lambda self: self.env.user)
    date_prefered = fields.Selection(
        selection=[('now', 'Directly'),
                   ('due', 'Due date'),
                   ('fixed', 'Fixed date')],
        string="Preferred Date", change_default=True, required=True,
        states={'done': [('readonly', True)]}, default='due',
        help="Choose an option for the Payment Order:'Fixed' stands for a "
             "date specified by you.'Directly' stands for the direct "
             "execution.'Due date' stands for the scheduled date of "
             "execution.")
    date_created = fields.Date(
        string='Creation Date', readonly=True, default=fields.Date.today)
    date_done = fields.Date(string='Execution Date', readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related='mode.company_id',
        string='Company', store=True, readonly=True)

    @api.multi
    @api.depends('line_ids', 'line_ids.amount')
    def _compute_total(self):
        for order in self:
            order.total = sum(order.line_ids.mapped(lambda x: x.amount))

    @api.model
    def create(self, vals):
        if vals.get('reference', '/') == '/':
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'payment.order')
        return super(PaymentOrder, self).create(vals)

    @api.multi
    def write(self, vals):
        if ((vals.get('date_prefered') == 'fixed' and
                not vals.get('date_scheduled')) or vals.get('date_scheduled')):
            self.mapped('line_ids').write({'date': vals.get('date_scheduled')})
        elif vals.get('date_prefered') == 'due':
            vals.update({'date_scheduled': False})
            for line in self.mapped('line_ids'):
                line.date = line.ml_maturity_date
        elif vals.get('date_prefered') == 'now':
            vals.update({'date_scheduled': False})
            self.mapped('line_ids').write({'date': False})
        return super(PaymentOrder, self).write(vals)

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def set_open(self):
        self.write({'state': 'open'})

    @api.multi
    def set_done(self):
        self.write({
            'date_done': fields.Date.today(),
            'state': 'done',
        })

    @api.multi
    def set_cancel(self):
        self.write({'state': 'cancel'})


class PaymentLine(models.Model):
    _name = 'payment.line'
    _description = 'Payment Line'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The payment line name must be unique!'),
    ]

    def _default_date(self):
        order_id = self.env.context.get('order_id')
        if order_id:
            order = self.env['payment.order'].browse(order_id)
            if order.date_prefered == 'fixed':
                return order.date_scheduled
            elif order.date_prefered == 'now':
                return fields.Date.today()
        return False

    name = fields.Char(
        string='Your Reference', required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'payment.line'))
    communication = fields.Char(
        string='Communication', required=True,
        help="Used as the message between ordering customer and current "
             "company. Depicts 'What do you want to say to the recipient "
             "about this order ?'")
    communication2 = fields.Char(
        string='Communication 2', readonly=True,
        help='The successor message of Communication.',
        states={'structured': [('readonly', False)]})
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Entry line',
        domain=[('reconcile_id', '=', False),
                ('account_id.type', '=', 'payable')],
        help='This Entry Line will be referred for the information of the '
             'ordering customer.')
    amount_currency = fields.Float(
        string='Amount in Partner Currency', digits=(16, 2),
        required=True, help='Payment amount in the partner currency')
    currency = fields.Many2one(
        comodel_name='res.currency', string='Partner Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    company_currency = fields.Many2one(
        comodel_name='res.currency', string='Company Currency', readonly=True,
        default=lambda self: self.env.user.company_id.currency_id)
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank', string='Destination Bank Account',
        domain="[('partner_id', '=', partner_id)]")
    order_id = fields.Many2one(
        comodel_name='payment.order', string='Order', required=True,
        ondelete='cascade', index=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string="Partner", required=True,
        help='The Ordering Customer')
    amount = fields.Float(
        compute="_compute__amount", string='Amount in Company Currency',
        help='Payment amount in the company currency')
    ml_date_created = fields.Date(
        compute="_compute_ml_date_created", string="Effective Date",
        help="Invoice Effective Date")
    ml_maturity_date = fields.Date(
        compute="_compute_ml_maturity_date", string='Due Date')
    ml_inv_ref = fields.Many2one(
        compute="_compute_ml_inv_ref", comodel_name='account.invoice',
        string='Invoice Ref.')
    info_owner = fields.Text(
        compute="_compute_info_owner", string="Owner Account",
        help='Address of the Main Partner')
    info_partner = fields.Text(
        compute="_compute_info_partner", string="Destination Account",
        help='Address of the Ordering Customer.')
    date = fields.Date(
        string='Payment Date', default=_default_date,
        help="If no payment date is specified, the bank will treat this "
             "payment line directly")
    create_date = fields.Datetime(string='Created', readonly=True)
    state = fields.Selection(
        selection=[('normal','Free'),
                   ('structured','Structured')],
        string='Communication Type', required=True, default='normal')
    bank_statement_line_id = fields.Many2one(
        comodel_name='account.bank.statement.line',
        string='Bank statement line')
    company_id = fields.Many2one(
        comodel_name="res.company", related='order_id.company_id',
        string='Company', store=True, readonly=True)

    @api.multi
    @api.depends('amount_currency', 'currency')
    def _compute_amount(self):
        for line in self:
            line.amount = line.currency.with_context(
                line.order_id.date_done or fields.Date.today()).compute(
                line.company_currency.id, line.amount_currency)

    @api.multi
    def _compute_ml_date_created(self):
        for line in self:
            line.ml_date_created = line.move_line_id.date_created

    @api.multi
    def _compute_ml_maturity_date(self):
        for line in self:
            line.ml_maturity_date = line.move_line_id.date_maturity

    @api.multi
    def _compute_ml_inv_ref(self):
        for line in self:
            line.ml_inv_ref = line.move_line_id.invoice.id

    @api.multi
    def _compute_info_owner(self):
        for line in self:
            owner = line.order_id.mode.bank_id.partner_id
            line.info_owner = self._get_info_partner(owner)

    @api.multi
    def _compute_info_partner(self):
        for line in self:
            line.info_partner = self._get_info_partner(line.partner_id)

    @api.onchange('move_line_id')
    def onchange_move_line(self):
        if self.move_line_id:
            self.amount_currency = self.move_line_id.amount_residual_currency
            self.partner_id = self.move_line_id.partner_id.id
            self.currency = (self.move_line_id.currency_id.id or
                             self.move_line_id.invoice.currency_id.id)
            self.communication = self.move_line_id.ref
            if self.order_id.date_prefered == 'now':
                #no payment date => immediate payment
                self.date = False
            elif self.order_id.date_prefered == 'due':
                self.date = self.move_line_id.date_maturity
            elif self.order_id.date_prefered == 'fixed':
                self.date = self.order_id.date_scheduled

    @api.onchange('amount')
    def onchange_amount(self):
        self.amount = self.currency.compute(self.company_currency, self.amount)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.bank_id = self.partner_id.bank_ids[:1]

    @api.model
    def _get_info_partner(self, partner_record):
        if not partner_record:
            return False
        st = partner_record.street
        st1 = partner_record.street2
        zip = partner_record.zip
        city = partner_record.city
        zip_city = zip + ' ' + city
        cntry = partner_record.country_id.name
        return (partner_record.name + "\n" + st + " " + st1 + "\n" +
                zip_city + "\n" + cntry)

