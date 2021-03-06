
from osv import fields,osv
import netsvc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _
import decimal_precision as dp
from lxml import etree
import random
import time

class car_marque(osv.osv):
    
    _name = 'car.marque'
    _description = "Marque de voitures"
    _order = "name"
    _columns = {
        'name': fields.char("Marque", size=64),
    }
    
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The Name must be unique"),
    ]
    
car_marque()

class car_modele(osv.osv):
    
    _name = 'car.modele'
    _description = "Modele de voitures"
    _order = "name"
    _columns = {
        'name': fields.char("Modele", size=64),
        'marque_id': fields.many2one('car.marque', 'Marque'),
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The Name must be unique"),
    ]
        
car_modele()

class car_symptomes(osv.osv):
    _name = "car.symptomes"
    _description = "Car Symptomes"
    _columns = {
        'name' : fields.char('Symptome', size=64, required=True),        
        'repair_id': fields.many2one('mrp.repair', 'Repair Order', ondelete='cascade'),
    }
car_symptomes()

class mrp_repair(osv.osv):
    _name = 'mrp.repair'
    _description = 'Repair Order'
    _order = "name DESC"
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}       
        res = super(mrp_repair, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if view_type == 'form':
            root = etree.fromstring(unicode(res['arch'], 'utf8'))            
            nodes = root.xpath("//field[@name='operations']")

            u =  """
            <field colspan="4" mode="tree,form" name="operations" nolabel="1" widget="one2many_list">
                            <form string="Operations">
                                <notebook>
                                    <page string="Repair Line">
                                     <field name="cr_uid" invisible="1"/>                                        
                                        <field name="product_id" colspan="4" on_change="product_id_change(parent.pricelist_id,product_id,product_uom,product_uom_qty, parent.partner_id)" attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="name" attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="casier" attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="product_uom_qty" string="Qty"  attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="product_uom" string="UoM" attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="price_unit" attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="discount" attrs="{'readonly':[('cr_uid','!=',%s)]}"/>
                                        <field name="price_subtotal"/>
                                        <newline/>
                                        <group colspan="2">
                                            <field name="to_invoice"/>
                                            <field name="invoiced"/>
                                        </group>
                                        <newline/>
                                        <field colspan="4" name="tax_id" domain="[('parent_id','=',False),('type_tax_use','&lt;&gt;','purchase')]" nolabel="1"  invisible="1"/>
                                        <field name="state"  invisible="1"/>
                                    </page>
                                    <page string="History" groups="base.group_extended">
                                        <field colspan="4" name="invoice_line_id"/>
                                    </page>

                                 </notebook>
                            </form>            
                            <tree string="Operations">                               
                                <field name="cr_uid" invisible="1"/>
                                <field name="product_id"/>
                                <field name="name"/>
                                <field name="casier"/>
                                <field name="product_uom_qty" string="Qty"/>
                                <field name="product_uom" string="UoM"/>
                                <field name="price_unit"/>
                                <field name="tax_id" invisible="1"/>
                                <field name="discount"/>
                                <field name="price_subtotal"/>
                            </tree>
                        </field>
            """ % ((uid), (uid), (uid) ,(uid), (uid), (uid), (uid))
            u = etree.fromstring(unicode(u, 'utf8')) 
            for node in nodes:
                node.getparent().replace(node, u)
            xarch, xfields = self._view_look_dom_arch(cr, uid, root, view_id, context=context)
            res['arch'] = xarch
            res['fields'] = xfields    
            res['arch'] = etree.tostring(root)

        return res
        
    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context=None):

        res = {}
        cur_obj = self.pool.get('res.currency')

        for repair in self.browse(cr, uid, ids, context=context):
            res[repair.id] = 0.0
            for line in repair.operations:
                res[repair.id] += line.price_subtotal
            for line in repair.fees_lines:
                res[repair.id] += line.price_subtotal
            cur = repair.pricelist_id.currency_id
            res[repair.id] = cur_obj.round(cr, uid, cur, res[repair.id])
        return res

    def _amount_tax(self, cr, uid, ids, field_name, arg, context=None):

        res = {}
        #return {}.fromkeys(ids, 0)
        cur_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for repair in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = repair.pricelist_id.currency_id
            for line in repair.operations:
                #manage prices with tax included use compute_all instead of compute
                if line.to_invoice:
                    tax_calculate = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit*(1-(line.discount/100)), line.product_uom_qty, repair.partner_invoice_id.id, line.product_id, repair.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            for line in repair.fees_lines:
                if line.to_invoice:
                    tax_calculate = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit*(1-(line.discount/100)), line.product_uom_qty, repair.partner_invoice_id.id, line.product_id, repair.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            res[repair.id] = cur_obj.round(cr, uid, cur, val)
        return res

    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates total amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        untax = self._amount_untaxed(cr, uid, ids, field_name, arg, context=context)
        tax = self._amount_tax(cr, uid, ids, field_name, arg, context=context)
        cur_obj = self.pool.get('res.currency')
        for id in ids:
            repair = self.browse(cr, uid, id, context=context)
            cur = repair.pricelist_id.currency_id
            res[id] = cur_obj.round(cr, uid, cur, untax.get(id, 0.0) + tax.get(id, 0.0))
        return res

    def _get_default_address(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids, context=context):
            adr_id = False
            if data.partner_id:
                adr_id = partner_obj.address_get(cr, uid, [data.partner_id.id], ['default'])['default']
            res[data.id] = adr_id
        return res

    def _get_lines(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('mrp.repair.line').browse(cr, uid, ids, context=context):
            result[line.repair_id.id] = True
        return result.keys()   

    def unlink(self, cr, uid, ids, context=None):
        raise osv.except_osv(_('Invalid action !'), _('Vous n\'avez pas le droit de supprimer cet Ordre De Reparation!'))        
    
    _columns = {
        'name': fields.char('Repair Reference', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True),
        'partner_id' : fields.many2one('res.partner', 'Partner', select=True, help='This field allow you to choose the parner that will be invoiced and delivered'),
        'vehicule': fields.many2one('mrp.car','Vehicule', domain="[('partner_id','=',partner_id)]"),
        'marque': fields.char('Marque',size=24),
        'is_devis': fields.boolean('Devis'),
        'modele': fields.char('Modele',size=24),
        'matricule': fields.char('Matricule',size=24),
        'chassis': fields.char('Chassis',size=24),
        'telephone': fields.char('Telephone',size=24),        
        'kilometrage': fields.char('Kilometrage',size=24),
        'mec': fields.date('Mise en circulation'),        
        'address_id': fields.many2one('res.partner.address', 'Delivery Address', domain="[('partner_id','=',partner_id)]"),
        'default_address_id': fields.function(_get_default_address, type="many2one", relation="res.partner.address"),
        'create_date2': fields.datetime('Date'),
        'symptomes_ids': fields.one2many('car.symptomes', 'repair_id', 'Symptomes'),
        'state': fields.selection([
            ('draft','Quotation'),
            ('confirmed','Confirmed'),
            ('ready','Ready to Repair'),
            ('under_repair','Under Repair'),
            ('2binvoiced','To be Invoiced'),
            ('invoice_except','Invoice Exception'),
            ('done','Done'),
            ('cancel','Cancel'),
            ('avoir','Avoir')
            ], 'State', readonly=True,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed repair order. \
            \n* The \'Confirmed\' state is used when a user confirms the repair order. \
            \n* The \'Ready to Repair\' state is used to start to repairing, user can start repairing only after repair order is confirmed. \
            \n* The \'To be Invoiced\' state is used to generate the invoice before or after repairing done. \
            \n* The \'Done\' state is set when repairing is completed.\
            \n* The \'Cancelled\' state is used when user cancel repair order.'),
        'operations' : fields.one2many('mrp.repair.line', 'repair_id', 'Operation Lines', readonly=True, states={'draft':[('readonly', False)]}),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', help='The pricelist comes from the selected partner, by default.'),
        'partner_invoice_id':fields.many2one('res.partner.address', 'Invoicing Address',  domain="[('partner_id','=',partner_id)]"),
        'invoice_method':fields.selection([
            ("none","No Invoice"),
            ("b4repair","Before Repair"),
            ("after_repair","After Repair")
           ], "Invoice Method",
            select=True, required=True, states={'draft':[('readonly',False)]}, readonly=True, help='This field allow you to change the workflow of the repair order. If value selected is different from \'No Invoice\', it also allow you to select the pricelist and invoicing address.'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Picking',readonly=True),
        'fees_lines': fields.one2many('mrp.repair.fee', 'repair_id', 'Fees Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'quotation_notes': fields.text('Symptomes'),        
        'company_id': fields.many2one('res.company', 'Company'),
        'invoiced': fields.boolean('Invoiced', readonly=True),
        'repaired': fields.boolean('Repaired', readonly=True),
        'amount_untaxed': fields.function(_amount_untaxed, string='Untaxed Amount',
            store={
                'mrp.repair': (lambda self, cr, uid, ids, c={}: ids, ['operations'], 10),
                'mrp.repair.line': (_get_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
            }),
        'amount_tax': fields.function(_amount_tax, string='TVA',
            store={
                'mrp.repair': (lambda self, cr, uid, ids, c={}: ids, ['operations'], 10),
                'mrp.repair.line': (_get_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
            }),
        'amount_total': fields.function(_amount_total, string='Total',
            store={
                'mrp.repair': (lambda self, cr, uid, ids, c={}: ids, ['operations'], 10),
                'mrp.repair.line': (_get_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
            }),
    }
    
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "Order Reference must be unique"),
    ]
    
    _defaults = {
        'create_date2':  lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'mrp.repair'),
        'invoice_method': 'after_repair',
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.repair', context=context),
        'pricelist_id': lambda self, cr, uid,context : self.pool.get('product.pricelist').search(cr, uid, [('type','=','sale')])[0]
    }
        
    def copy(self, cr, uid, ids, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'repaired':False,
            'invoiced':False,
            'invoice_id': False,
            'picking_id': False,
            'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.repair'),
        })
        return super(mrp_repair, self).copy(cr, uid, ids, default, context)

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def onchange_partner_id(self, cr, uid, ids, part):
        
        part_obj = self.pool.get('res.partner')
        pricelist_obj = self.pool.get('product.pricelist')
        if not part:
            return {'value': {
                        'address_id': False,
                        'partner_invoice_id': False,
                        'pricelist_id': pricelist_obj.search(cr, uid, [('type','=','sale')])[0]
                    }
            }
        addr = part_obj.address_get(cr, uid, [part], ['delivery', 'invoice', 'default'])
        partner = part_obj.browse(cr, uid, part)
        pricelist = partner.property_product_pricelist and partner.property_product_pricelist.id or False
        return {'value': {
                    'partner_invoice_id': addr['invoice'],
                    'pricelist_id': pricelist,
                    'telephone': partner.phone
                }
        }
        
    def onchange_vehicule(self, cr, uid, ids, car):
        
        car_obj = self.pool.get('mrp.car')       
        vehicule = car_obj.browse(cr, uid, car)        
        return {'value': {
                    'chassis': vehicule.chassis,
                    'marque': vehicule.marque.name,
                    'modele': vehicule.modele.name,
                    'kilometrage': vehicule.kilometrage,
                    'matricule': vehicule.matricule,                    
                    'mec': vehicule.mec
                }
        }
        
    def action_confirm(self, cr, uid, ids, *args):
        """ Repair order state is set to 'To be invoiced' when invoice method
        is 'Before repair' else state becomes 'Confirmed'.
        @param *arg: Arguments
        @return: True
        """
        mrp_line_obj = self.pool.get('mrp.repair.line')
        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'state': 'confirmed'})
            if not o.operations:
                raise osv.except_osv(_('Error !'),_('You cannot confirm a repair order which has no line.'))
            mrp_line_obj.write(cr, uid, [l.id for l in o.operations], {'state': 'confirmed'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels repair order.
        @return: True
        """                       
        for repair in self.browse(cr, uid, ids, context=context):
            if repair.state == "under_repair":
                for line in repair.operations:
                    if line.product_id.type  in ('product', 'consu'):
                            self.pool.get('product.product').write(cr, uid, [line.product_id.id], {'quantite_in_atelier': line.product_id.quantite_in_atelier-line.product_uom_qty})
        mrp_line_obj = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids, context=context):
            mrp_line_obj.write(cr, uid, [l.id for l in repair.operations], {'state': 'draft'}, context=context)
        self.write(cr,uid,ids,{'state':'draft'})     
        wf_service = netsvc.LocalService("workflow")
        for _id in ids:            
            wf_service.trg_delete(uid, 'mrp.repair', _id, cr)
            wf_service.trg_create(uid, 'mrp.repair', _id, cr)   
        return True
    
    def is_magasinier(self, cr, uid, ids, context=None):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        group_names = []
        for grp in user.groups_id:
            group_names.append(grp.name)
        if ("Magasinier" in group_names) :
            return True    
        return False
    
    def wkf_invoice_create(self, cr, uid, ids, *args):
        return self.action_invoice_create(cr, uid, ids)
    
    def _sale_order_margin(self, cr, uid, ids, context=None):
        margin = 0
        for repair in self.browse(cr, uid, ids, context=context):
            for line in repair.operations:                
                if line.product_id:
                    if line.product_id.standard_price:
                        margin = margin + round((line.price_unit*line.product_uom_qty*(100.0-line.discount)/100.0) -(line.product_id.standard_price*line.product_uom_qty), 2)
                    else:
                        margin = margin + round((line.price_unit*line.product_uom_qty*(100.0-line.discount)/100.0) -(line.product_id.standard_price*line.product_uom_qty), 2)
     
        return margin
    
    def action_invoice_create(self, cr, uid, ids, group=False, context=None):
        """ Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        
        margin = self._sale_order_margin(cr, uid, ids)
        sale_order_obj = self.pool.get('sale.order')
        sale_order_line_obj = self.pool.get('sale.order.line')
        repair_line_obj = self.pool.get('mrp.repair.line')

        repair = self.browse(cr, uid, ids[0], context=context)           
                             
        self.write(cr, uid, repair.id, {'invoiced': True, 'state': 'done'})
        if not repair.partner_id.property_account_receivable:
            raise osv.except_osv(_('Error !'), _('No account defined for partner "%s".') % repair.partner_id.name )
        account_id = repair.partner_id.property_account_receivable.id
        sale_order = {
                      'state': 'draft',
                      'shipped': False,
                      'invoice_ids': [],
                      'picking_ids': [],
                      'date_confirm': False,
                      'name': repair.name, #+ "-" + str(random.randrange(0, 9)),
                      'origin':repair.name,
                      'account_id': account_id,
                      'partner_id': repair.partner_id.id,
                      'partner_invoice_id': repair.partner_invoice_id.id,
                      'partner_order_id': repair.partner_invoice_id.id, 
                      'partner_shipping_id': repair.partner_invoice_id.id,                                                   
                      'fiscal_position': repair.partner_id.property_account_position.id,
                      'pricelist_id': repair.pricelist_id.currency_id.id,
                      'margin': margin,
                      'company_id': repair.company_id.id
                }
        sale_order_id = sale_order_obj.create(cr, uid, sale_order)

        for operation in repair.operations:
            if group:
                name = repair.name + '-' + operation.name
            else:
                name = operation.name

            if operation.product_id.property_account_income:
                account_id = operation.product_id.property_account_income.id
            elif operation.product_id.categ_id.property_account_income_categ:
                account_id = operation.product_id.categ_id.property_account_income_categ.id
            else:
                raise osv.except_osv(_('Error !'), _('No account defined for product "%s".') % operation.product_id.name )                   

            sale_order_line_obj.create(cr, uid, {                                                                               
                'tax_id': [(6,0,[x.id for x in operation.tax_id])],
                'name': name,                                                                               
                'order_id': sale_order_id,
                'product_uos_qty': operation.product_uom.id,
                'product_uom_qty': operation.product_uom_qty,
                'price_unit': operation.price_unit,
                'purchase_price': operation.product_id.standard_price,
                'discount': operation.discount or 0,
                'product_id': operation.product_id and operation.product_id.id or False,
            })
            repair_line_obj.write(cr, uid, [operation.id], {'invoiced': True})
    
        return True
    
    def action_repair_ready(self, cr, uid, ids, context=None):
        """ Writes repair order state to 'Ready'
        @return: True
        """
        for repair in self.browse(cr, uid, ids, context=context):
            self.pool.get('mrp.repair.line').write(cr, uid, [l.id for
                    l in repair.operations], {'state': 'confirmed'}, context=context)
            self.write(cr, uid, [repair.id], {'state': 'ready'})         
        return True

    def action_repair_start(self, cr, uid, ids, context=None):
        """ Writes repair order state to 'Under Repair'
        @return: True
        """
        for repair in self.browse(cr, uid, ids, context=context):
            if repair.state == "confirmed":
                for line in repair.operations:
                    if line.product_id.type  in ('product', 'consu'):
                            self.pool.get('product.product').write(cr, uid, [line.product_id.id], {'quantite_in_atelier': line.product_id.quantite_in_atelier+line.product_uom_qty})
                                
        repair_line = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids, context=context):
            repair_line.write(cr, uid, [l.id for
                    l in repair.operations], {'state': 'confirmed'}, context=context)
            repair.write({'state': 'under_repair'})
          
        return True    

    def action_repair_end(self, cr, uid, ids, context=None):
        """ Writes repair order state to 'To be invoiced' if invoice method is
        After repair else state is set to 'Ready'.
        @return: True
        """
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.operations:
                if line.product_id.type  in ('product', 'consu'):
                    self.pool.get('product.product').write(cr, uid, [line.product_id.id], {'quantite_in_atelier': line.product_id.quantite_in_atelier-line.product_uom_qty})
            val = {}
            val['repaired'] = True
            val['state'] = '2binvoiced'
            self.write(cr, uid, [order.id], val)
            
        return True

mrp_repair()


class ProductChangeMixin(object):
    def product_id_change(self, cr, uid, ids, pricelist, product, uom=False,
                          product_uom_qty=0, partner_id=False):
        """ On change of product it sets product quantity, tax account, name,
        uom of product, unit price and price subtotal.
        @param pricelist: Pricelist of current record.
        @param product: Changed id of product.
        @param uom: UoM of current record.
        @param product_uom_qty: Quantity of current record.
        @param partner_id: Partner of current record.
        @return: Dictionary of values and warning message.
        """
        result = {}
        warning = {}

        if not product_uom_qty:
            product_uom_qty = 1
        result['product_uom_qty'] = product_uom_qty

        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            if partner_id:
                partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
                result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, product_obj.taxes_id)

            result['name'] = product_obj.partner_ref
            result['casier'] = product_obj.casier
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id or False
            if not pricelist:
                warning = {
                    'title':'No Pricelist !',
                    'message':
                        'You have to select a pricelist in the Repair form !\n'
                        'Please set one before choosing a product.'
                }
            else:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                            product, product_uom_qty, partner_id, {'uom': uom,})[pricelist]

                if price is False:
                    warning = {
                        'title':'No valid pricelist line found !',
                        'message':
                            "Couldn't find a pricelist line matching this product and quantity.\n"
                            "You have to change either the product, the quantity or the pricelist."
                    }
                else:
                    result.update({'price_unit': price, 'price_subtotal': price*product_uom_qty})

        return {'value': result, 'warning': warning}


class mrp_repair_line(osv.osv, ProductChangeMixin):
    _name = 'mrp.repair.line'
    _description = 'Repair Line'
    _order = "product_uom desc"
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default: default = {}
        default.update( {'invoice_line_id': False, 'move_id': False, 'invoiced': False, 'state': 'draft'})
        return super(mrp_repair_line, self).copy_data(cr, uid, id, default, context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        cur_obj=self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.to_invoice and line.price_unit * line.product_uom_qty * (1 - (line.discount or 0.0) /100.0) or 0
            cur = line.repair_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
       
    _columns = {
        'discount': fields.float('Discount (%)', digits=(16,2)),
        'cr_uid' : fields.integer('Cr Uid',required=True),        
        'name' : fields.char('Description',size=64,required=True),
        'casier' : fields.char('Casier',size=64),
        'repair_id': fields.many2one('mrp.repair', 'Repair Order Reference',ondelete='cascade', select=True),
        'type': fields.selection([('add','Add'),('remove','Remove')],'Type'),
        'to_invoice': fields.boolean('To Invoice', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok','=',True)], required=True),
        'invoiced': fields.boolean('Invoiced',readonly=True),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal',digits_compute= dp.get_precision('Sale Price')),
        'tax_id': fields.many2many('account.tax', 'repair_operation_line_tax', 'repair_operation_line_id', 'tax_id', 'Taxes'),
        'product_uom_qty': fields.float('Quantity (UoM)', digits=(16,2), required=True),
        'product_uom': fields.many2one('product.uom', 'Product UoM', required=True),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line', readonly=True),
        'location_id': fields.many2one('stock.location', 'Source Location', select=True),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', select=True),
        'move_id': fields.many2one('stock.move', 'Inventory Move', readonly=True),
        'state': fields.selection([
                    ('draft','Draft'),
                    ('confirmed','Confirmed'),
                    ('done','Done'),
                    ('cancel','Canceled')], 'State', required=True, readonly=True,
                    help=' * The \'Draft\' state is set automatically as draft when repair order in draft state. \
                        \n* The \'Confirmed\' state is set automatically as confirm when repair order in confirm state. \
                        \n* The \'Done\' state is set automatically when repair order is completed.\
                        \n* The \'Cancelled\' state is set automatically when user cancel repair order.'),
    }
    _defaults = {
     'state': 'draft',
     'product_uom_qty':  1,
     'location_id': 12,
     'location_dest_id': 11,
     'to_invoice': True,
     'type': 'add',
     'cr_uid': lambda self,cr,uid,c: uid,
    }
    
    def unlink(self, cr, uid, ids, context=None):
        repair_line = self.browse(cr, uid, ids[0], context=context)
        if repair_line.cr_uid != uid:
            raise osv.except_osv(_('Invalid action !'), _('Vous n\'avez pas le droit de supprimer cette ligne! "%s" ') % (repair_line.product_id.default_code))
        osv.osv.unlink(self, cr, uid, ids, context=context)
        return True
        
    def _quantity_exists_in_warehouse(self, cr, uid, ids, context=None):
        repair_line = self.browse(cr, uid, ids[0], context=context)
        if repair_line.product_id.type  in ('product', 'consu') and repair_line.product_uom_qty > repair_line.product_id.virtual_available and repair_line.state !="draft":
            similar_products = repair_line.product_id.similar_products
            x = ""
            for product in similar_products:
                if repair_line.product_uom_qty <= product.product_id.virtual_available:
                    x += product.product_id.default_code+","  
            if x != ""  :      
                raise osv.except_osv(_('Warning !'), _('The quantity of product "%s" does not exist in warehouse. You may want use the following references "%s"') % (repair_line.product_id.default_code, x))
            else :      
                raise osv.except_osv(_('Warning !'), _('The quantity of product "%s" does not exist in warehouse.') % (repair_line.product_id.default_code))            
            return False
        return True
    
    _constraints = [
#        (_quantity_exists_in_warehouse,'Error: The quantity does not exist in warehouse.', ['product_uom_qty']),
    ]
    
mrp_repair_line()

class mrp_repair_fee(osv.osv, ProductChangeMixin):
    _name = 'mrp.repair.fee'
    _description = 'Repair Fees Line'

    def copy_data(self, cr, uid, ids, default=None, context=None):
        if not default: default = {}
        default.update({'invoice_line_id': False, 'invoiced': False})
        return super(mrp_repair_fee, self).copy_data(cr, uid, ids, default, context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.to_invoice and line.price_unit * line.product_uom_qty * (1 - (line.discount or 0.0) /100.0) or 0            
            cur = line.repair_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    _columns = {
        'repair_id': fields.many2one('mrp.repair', 'Repair Order Reference', required=True, ondelete='cascade', select=True),
        'name': fields.char('Description', size=64, select=True,required=True),
        'product_id': fields.many2one('product.product', 'Product'),
        'discount': fields.float('Discount (%)', digits=(16,2)),
        'product_uom_qty': fields.float('Quantity', digits=(16,2), required=True),
        'price_unit': fields.float('Unit Price', required=True),
        'product_uom': fields.many2one('product.uom', 'Product UoM', required=True),
        'price_subtotal': fields.function(_amount_line, string='Subtotal',digits_compute= dp.get_precision('Sale Price')),
        'tax_id': fields.many2many('account.tax', 'repair_fee_line_tax', 'repair_fee_line_id', 'tax_id', 'Taxes'),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line', readonly=True),
        'to_invoice': fields.boolean('To Invoice'),
        'invoiced': fields.boolean('Invoiced',readonly=True),
    }
    _defaults = {
        'to_invoice': lambda *a: True,
    }

mrp_repair_fee()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
