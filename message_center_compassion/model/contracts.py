# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Cyril Sester. Copyright Compassion Suisse
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import orm, fields
from openerp.tools import mod10r
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import pdb
import logging
import time

logger = logging.getLogger(__name__)

class simple_recurring_contract(orm.Model):
    """ We add here creation of messages concerning commitments. """
    _inherit = "simple.recurring.contract"
    
    def _active (self, cr, uid, ids, field_name, args, context=None) :
        """ Create messages to GMC when new sponsorship is activated. """
        res = super(simple_recurring_contract, self)._active(cr, uid, ids, field_name, args, context=context)
        message_obj = self.pool.get('gmc.message.pool')
        action_obj = self.pool.get('gmc.action')
        action_id = 0
        message_vals = {}
        
        for contract in self.browse(cr, uid, ids, context=context):
            # UpsertConstituent Message
            action_id = action_obj.search(cr, uid, [('name','=','UpsertConstituent')], limit=1, context=context)[0]
            message_vals = {
                'action_id': action_id,
                'object_id': contract.partner_id.id,
                'date': contract.first_payment_date,
            }
            message_obj.create(cr, uid, message_vals, context=context)
            
            # CreateCommitment Message
            action_id = action_obj.search(cr, uid, [('name','=','CreateCommitment')], limit=1, context=context)[0]
            message_vals['action_id'] = action_id
            message_vals['object_id'] = contract.id
            message_obj.create(cr, uid, message_vals, context=context)
        
        return res
        
    def contract_terminated(self, cr, uid, ids):
        """ Inform GMC when sponsorship is terminated. """
        res = super(simple_recurring_contract, self).contract_terminated(cr, uid, ids)
        if res:
            message_obj = self.pool.get('gmc.message.pool')
            action_obj = self.pool.get('gmc.action')
            action_id = action_obj.search(cr, uid, [('name','=','CancelCommitment')], limit=1, context=context)[0]
            message_vals = {'action_id': action_id}
            
            for id in ids:
                message_vals['object_id'] = id
                message_obj.create(cr, uid, message_vals)
        
        return res
        
    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Check if invoice paid contains
            a child gift and creates a message to GMC. """
        gift_product_names = [
            'Birthday Gift', 'General Gift', 'Family Gift',
            'Project Gift', 'Graduation Gift'
        ]
        message_obj = self.pool.get('gmc.message.pool')
        action_obj = self.pool.get('gmc.action')
        action_id = action_obj.search(cr, uid, [('name','=','CreateGift')], limit=1, context=context)[0]
        message_vals = {'action_id': action_id}
        gift_ids = self.pool.get('product.product').search(cr, uid, [('name_template','in',gift_product_names)], context={'lang':'en_US'})

        for invoice_line in invoice.invoice_line:
            if invoice_line.product_id.id in gift_ids:
                message_vals['object_id'] = invoice_line.id
                message_vals['date'] = invoice.date_invoice
                message_obj.create(cr, uid, message_vals)
