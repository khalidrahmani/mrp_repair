import decimal_precision as dp
from osv import osv, fields
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from tools.translate import _

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = 'purchase.order'  

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += line.price_subtotal
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, (line.prix_fournisseur*(1 - (line.discount/100))), line.product_qty, order.partner_address_id.id, line.product_id.id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
              
    _columns = {
        'transport' : fields.float('Transport'),
        'douane' : fields.float('Douane'),
        'transit' : fields.float('Transit'),
        'divers' : fields.float('Divers'),
        'totale_facture' : fields.float('Total facture'),        
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Purchase Price'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax"),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Purchase Price'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Purchase Price'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),       
    }    


        
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line 
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.prix_fournisseur*(1 - (order_line.discount/100)) or order_line.price_unit*(1 - (order_line.discount/100)) or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
        }
"""        
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        purchase_order_line_object = self.pool.get('purchase.order.line')
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error !'),_('You cannot confirm a purchase order without any lines !!.'))               
            for line in po.order_line:                
                price = (line.price_subtotal + line.transport + line.douane + line.transit+ line.divers) / (line.product_qty )  
                purchase_order_line_object.write(cr, uid, [line.id],{'price_unit': price})
        return super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
"""
        
purchase_order()

class purchase_order_line(osv.osv):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'      

    def _prix_de_revient(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            subtotal = (line.prix_fournisseur*(1 - (line.discount/100)))*line.product_qty
            trns = (line.product_qty * line.order_id.transport * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture) 
            douane = (line.product_qty * line.order_id.douane * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)  
            transit = (line.product_qty * line.order_id.transit * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)
            divers = (line.product_qty * line.order_id.divers * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)  
            res[line.id] = (subtotal +  trns + douane + transit + divers ) /line.product_qty 
        return res
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.prix_fournisseur*(1 - (line.discount/100)), line.product_qty)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res
    
    def _transport(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context): 
            if line.order_id.totale_facture != 0 :           
                res[line.id] = (line.product_qty * line.order_id.transport * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)  
            else :
                res[line.id] = 0    
        return res
    
    def _douane(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context): 
            if line.order_id.totale_facture != 0 :           
                res[line.id] = (line.product_qty * line.order_id.douane * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)  
            else :
                res[line.id] = 0    
        return res

    def _transit(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context): 
            if line.order_id.totale_facture != 0 :           
                res[line.id] = (line.product_qty * line.order_id.transit * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)  
            else :
                res[line.id] = 0    
        return res

    def _divers(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context): 
            if line.order_id.totale_facture != 0 :           
                res[line.id] = (line.product_qty * line.order_id.divers * line.prix_fournisseur * (1 - (line.discount/100))) / (line.order_id.totale_facture)  
            else :
                res[line.id] = 0    
        return res
        
#    def _price_unit(self, cr, uid, ids, field_name, arg, context=None):
#        res = {}
#        for line in self.browse(cr, uid, ids, context=context):                      
#            res[line.id] = line.price_subtotal + line.transport + line.douane / (line.product_qty )                 
#        return res
        
    _columns = {
        'default_code': fields.char('Reference', size=256, required=True),
        'prix_fournisseur': fields.float('Tarif Fournisseur', size=256, required=True),
        'transport' : fields.function(_transport, string='Transport', store = True),
        'douane' : fields.function(_douane, string='Douane', store = True),
        'transit' : fields.function(_transit, string='Transit', store = True),
        'divers' : fields.function(_divers, string='Divers', store = True),
        'price_unit' : fields.function(_prix_de_revient, string='Prix de Revient', store = True),        
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Purchase Price')),
#        'price_unit' : fields.function(_price_unit, string='prix de revient', store = True),
    } 
    

    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        
        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'notes': notes or '', 'product_uom' : uom_id or False}}
        if not product_id:
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_supplierinfo = self.pool.get('product.supplierinfo')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        if not pricelist_id:
            raise osv.except_osv(_('No Pricelist !'), _('You have to select a pricelist or a supplier in the purchase form !\nPlease set one before choosing a product.'))
        if not partner_id:
            raise osv.except_osv(_('No Partner!'), _('You have to select a partner in the purchase form !\nPlease set one partner before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        lang = res_partner.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        res['value'].update({'name': product.name, 'default_code':product.default_code, 'notes': notes or product.description_purchase})
        
        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id
        
        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            res['warning'] = {'title': _('Warning'), 'message': _('Selected UOM does not belong to the same category as the product UOM')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.date.context_today(cr,uid,context=context)

        qty = qty or 1.0
        supplierinfo = False
        supplierinfo_ids = product_supplierinfo.search(cr, uid, [('name','=',partner_id),('product_id','=',product.id)])
        if supplierinfo_ids:
            supplierinfo = product_supplierinfo.browse(cr, uid, supplierinfo_ids[0], context=context)
            if supplierinfo.product_uom.id != uom_id:
                res['warning'] = {'title': _('Warning'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
            min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
            if qty < min_qty: # If the supplier quantity is greater than entered from user, set minimal.
                res['warning'] = {'title': _('Warning'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                qty = min_qty

        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        res['value'].update({'date_planned': date_planned or dt, 'product_qty': qty})

        # - determine price_unit and taxes_id
        price = product_pricelist.price_get(cr, uid, [pricelist_id],
                    product.id, qty or 1.0, partner_id, {'uom': uom_id, 'date': date_order})[pricelist_id]
        
        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
        res['value'].update({'price_unit': price, 'prix_fournisseur': price, 'taxes_id': taxes_ids})

        return res    
    
purchase_order_line()        
