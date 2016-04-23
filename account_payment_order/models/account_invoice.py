# -*- coding: utf-8 -*-
# © 2004-2015 Odoo S.A.
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp.tools.translate import _
from openerp.osv import osv


class Invoice(osv.osv):
    _inherit = 'account.invoice'

    # Forbid to cancel an invoice if the related move lines have already been
    # used in a payment order. The risk is that importing the payment line
    # in the bank statement will result in a crash cause no more move will
    # be found in the payment line
    def action_cancel(self, cr, uid, ids, context=None):
        payment_line_obj = self.pool.get('payment.line')
        for inv in self.browse(cr, uid, ids, context=context):
            pl_line_ids = []
            if inv.move_id and inv.move_id.line_id:
                inv_mv_lines = [x.id for x in inv.move_id.line_id]
                pl_line_ids = payment_line_obj.search(cr, uid, [('move_line_id','in',inv_mv_lines)], context=context)
            if pl_line_ids:
                pay_line = payment_line_obj.browse(cr, uid, pl_line_ids, context=context)
                payment_order_name = ','.join(map(lambda x: x.order_id.reference, pay_line))
                raise osv.except_osv(_('Error!'), _("You cannot cancel an invoice which has already been imported in a payment order. Remove it from the following payment order : %s."%(payment_order_name)))
        return super(Invoice, self).action_cancel(cr, uid, ids, context=context)
