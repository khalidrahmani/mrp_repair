
from osv import fields,osv
import netsvc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _
import decimal_precision as dp
from lxml import etree

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

class mrp_car(osv.osv):
    
    _name = 'mrp.car'
    _description = "Voitures"
    
    def _car_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for car in self.browse(cr, uid, ids, context=context):            
            res[car.id] = car.marque.name + " " +car.modele.name + " " +car.chassis
        return res        
        
    _columns = {
        'name': fields.function(_car_name, string='Name', readonly=True),                
        'marque': fields.many2one('car.marque','Marque'),
        'modele': fields.many2one('car.modele','Modele',domain="[('marque_id','=',marque)]"),
        'matricule': fields.char('Matricule',size=24),
        'chassis': fields.char('Chassis',size=24),
        'kilometrage': fields.char('Kilometrage',size=24),
        'mec': fields.date('Mise en circulation'),        
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),        
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The Name must be unique"),
    ]
        
mrp_car()

class mrp_repair(osv.osv):
    _name = 'mrp.repair'
    _description = 'Repair Order'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}       
        res = super(mrp_repair, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        x = "%(rrr)d"
        assert False, x
        doc = etree.XML(res['arch'])
        #active_model = context.get('active_model')
  
#            record_id = context and context.get('active_id', False) or False
#            assert record_id, (context)      
#        if not record_id or (active_model and active_model != 'mrp.repair'):
#            return res
        
        #repair_order = self.pool.get('mrp.repair').browse(cr, uid, record_id, context=context)
        
        if view_type == 'form' :         
            res['arch'] = """ <form string="Repairs order">
                <group col="6" colspan="4">
                    <field name="name" readonly="1"/>
                    <field name="partner_id" on_change="onchange_partner_id(partner_id)"/>       
                    <field name="vehicule" on_change="onchange_vehicule(vehicule)"/>
                    <field name="marque"/>   
                    <field name="modele"/>
                    <field name="matricule"/>
                    <field name="kilometrage"/>
                    <field name="chassis"/>
                    <field name="mec"/>
                    <newline/>                                 
                    <field name="telephone"/>
                    <field name="create_date2"/>
                    <newline/>
                    <field name="repaired"/>
                    <field name="invoiced"/>  
                </group>
                <notebook colspan="4">
                    <page string="Operations" groups="mrp_repair.group_magasinier,mrp_repair.group_atelier">
                        <field colspan="4" mode="tree" name="operations" nolabel="1" widget="one2many_list">
                            <tree string="Operations" editable="bottom">                               
                                <field name="cr_uid" invisible="1"/>
                                <field name="product_id" on_change="product_id_change(parent.pricelist_id,product_id,product_uom,product_uom_qty, parent.partner_id)" attrs="{'readonly':[('cr_uid','!=','%s')]}"/>
                                <field name="name" attrs="{'readonly':[('cr_uid','!=','%s')]}"/>
                                <field name="casier" attrs="{'readonly':[('cr_uid','!=','%s')]}"/>
                                <field name="product_uom_qty" string="Qty" attrs="{'readonly':[('cr_uid','!=','%s')]}"/>
                                <field name="product_uom" string="UoM" attrs="{'readonly':[('cr_uid','!=','%s')]}"/>
                                <field name="price_unit" attrs="{'readonly':[('cr_uid','!=','%s')]}"/>
                                <field name="tax_id" invisible="1"/>
                                <field name="price_subtotal"/>
                            </tree>
                        </field>
                        <newline/>
                        <group col="7" colspan="4">
                            <field name="amount_untaxed" sum="Untaxed amount"/>
                            <field name="amount_tax"/>
                            <field name="amount_total" sum="Total amount"/>
                            <button name="button_dummy" states="draft" string="Compute" type="object" icon="terp-stock_format-scientific"/>
                        </group>
                        """ % (str(uid), str(uid), str(uid), str(uid), str(uid), str(uid))
                        
            res['arch'] += """ <separator string="" colspan="4"/>
                        <group col="13" colspan="4">
                            <field name="state"/>
                            <button name="%(action_cancel_repair)d" states="2binvoiced,under_repair" string="Modifier la Reparation" type="action" icon="gtk-stop"/>
                            <button name="%(action_cancel_repair)d" states="invoice_except" string="Modifier la Reparation" type="action" icon="gtk-stop"/>
                            <button name="action_cancel_draft" states="cancel" string="Set to Draft" type="object" icon="gtk-convert"/>
                            <button name="repair_confirm" states="draft" string="Confirm Repair" icon="terp-camera_test"/>
                            <button name="repair_ready" states="confirmed" string="Start Repair" icon="terp-gtk-jump-to-ltr"/>
                            <button name="action_repair_start" states="ready" string="Start Repair" icon="terp-gtk-jump-to-ltr"/>
                            <button name="action_repair_end" states="under_repair" string="End Repair" icon="terp-dialog-close"/>
                            <button name="invoice_recreate" states="invoice_except" string="Recreate Invoice" icon="terp-dolar"/>
                            <button name="invoice_corrected" states="invoice_except" string="Invoice Corrected" icon="terp-emblem-important"/>
                            <button name="action_invoice_create" states="2binvoiced" string="Make Invoice" icon="terp-dolar"/>
                        </group>
                    </page>
                    <page string="Invoicing">
                        <field name="invoice_method" colspan="4"  readonly="1"/>
                        <field name="pricelist_id" readonly="1"/>
                        <field name="partner_invoice_id" />                        
                    </page>
                    <page string="Symptomes">
                        <field name="symptomes_ids" colspan="4" nolabel="1">
                            <tree string="Symptomes" editable="bottom">
                                <field name="name"/>
                            </tree>
                        </field>
                    </page>
                </notebook>
            </form> """ 
            
            doc = etree.fromstring(res['arch'].encode('utf8'))
            xarch, xfields = self._view_look_dom_arch(cr, uid, doc, view_id, context=context)
            res['arch'] = xarch
            res['fields'] = xfields
            res['arch'] = etree.tostring(doc)
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
                    tax_calculate = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit, line.product_uom_qty, repair.partner_invoice_id.id, line.product_id, repair.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            for line in repair.fees_lines:
                if line.to_invoice:
                    tax_calculate = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit, line.product_uom_qty, repair.partner_invoice_id.id, line.product_id, repair.partner_id)
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
    
    _columns = {
        'name': fields.char('Repair Reference',size=24, required=True),
        'partner_id' : fields.many2one('res.partner', 'Partner', select=True, help='This field allow you to choose the parner that will be invoiced and delivered'),
        'vehicule': fields.many2one('mrp.car','Vehicule',domain="[('partner_id','=',partner_id)]"),
        'marque': fields.char('Marque',size=24),
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
            ('cancel','Cancel')
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

    _defaults = {
        'create_date2': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'mrp.repair'),
        'invoice_method': 'after_repair',
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.repair', context=context),
        'pricelist_id': lambda self, cr, uid,context : self.pool.get('product.pricelist').search(cr, uid, [('type','=','sale')])[0]
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The Name must be unique"),
    ]
    
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
        
    def action_cancel_draft(self, cr, uid, ids, *args):
        """ Cancels repair order when it is in 'Draft' state.
        @param *arg: Arguments
        @return: True
        """
        if not len(ids):
            return False
        mrp_line_obj = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids):
            mrp_line_obj.write(cr, uid, [l.id for l in repair.operations], {'state': 'draft'})
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_create(uid, 'mrp.repair', id, cr)
        return True

    def action_confirm(self, cr, uid, ids, *args):
        """ Repair order state is set to 'To be invoiced' when invoice method
        is 'Before repair' else state becomes 'Confirmed'.
        @param *arg: Arguments
        @return: True
        """
        mrp_line_obj = self.pool.get('mrp.repair.line')
        for o in self.browse(cr, uid, ids):
            if (o.invoice_method == 'b4repair'):
                self.write(cr, uid, [o.id], {'state': '2binvoiced'})
            else:
                self.write(cr, uid, [o.id], {'state': 'confirmed'})
                if not o.operations:
                    raise osv.except_osv(_('Error !'),_('You cannot confirm a repair order which has no line.'))
                mrp_line_obj.write(cr, uid, [l.id for l in o.operations], {'state': 'confirmed'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels repair order.
        @return: True
        """
        mrp_line_obj = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids, context=context):
            mrp_line_obj.write(cr, uid, [l.id for l in repair.operations], {'state': 'cancel'}, context=context)
        self.write(cr,uid,ids,{'state':'cancel'})        
#        if self.is_magasinier(cr, uid, ids, context):
        move_obj = self.pool.get('stock.move')
        repair_line_obj = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids, context=context):
            for move in repair.operations:
                if move.product_id.type  in ('product', 'consu'):
                    move_id = move_obj.create(cr, uid, {
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'product_qty': move.product_uom_qty,
                        'product_uom': move.product_uom.id,
                        'address_id': repair.address_id and repair.address_id.id or False,
                        'location_id': move.location_dest_id.id,
                        'location_dest_id': move.location_id.id,
                        'tracking_id': False,
                        'state': 'done',
                    })
                    repair_line_obj.write(cr, uid, [move.id], {'move_id': move_id, 'state': 'done'}, context=context)        
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

    def action_invoice_create(self, cr, uid, ids, group=False, context=None):
        """ Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        res = {}
        invoices_group = {}
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_obj = self.pool.get('account.invoice')
        repair_line_obj = self.pool.get('mrp.repair.line')
        repair_fee_obj = self.pool.get('mrp.repair.fee')
        for repair in self.browse(cr, uid, ids, context=context):
            res[repair.id] = False
            if repair.state in ('draft','cancel') or repair.invoice_id:
                continue
            if not (repair.partner_id.id and repair.partner_invoice_id.id):
                raise osv.except_osv(_('No partner !'),_('You have to select a Partner Invoice Address in the repair form !'))
            comment = repair.quotation_notes
            if (repair.invoice_method != 'none'):
                if group and repair.partner_invoice_id.id in invoices_group:
                    inv_id = invoices_group[repair.partner_invoice_id.id]
                    invoice = inv_obj.browse(cr, uid, inv_id)
                    invoice_vals = {
                        'name': invoice.name +', '+repair.name,
                        'origin': invoice.origin+', '+repair.name,
                        'comment':(comment and (invoice.comment and invoice.comment+"\n"+comment or comment)) or (invoice.comment and invoice.comment or ''),
                    }
                    inv_obj.write(cr, uid, [inv_id], invoice_vals, context=context)
                else:
                    if not repair.partner_id.property_account_receivable:
                        raise osv.except_osv(_('Error !'), _('No account defined for partner "%s".') % repair.partner_id.name )
                    account_id = repair.partner_id.property_account_receivable.id
                    inv = {
                        'name': repair.name,
                        'origin':repair.name,
                        'type': 'out_invoice',
                        'account_id': account_id,
                        'partner_id': repair.partner_id.id,
                        'address_invoice_id': repair.partner_invoice_id.id,
                        'currency_id': repair.pricelist_id.currency_id.id,
                        'comment': repair.quotation_notes,
                        'fiscal_position': repair.partner_id.property_account_position.id
                    }
                    inv_id = inv_obj.create(cr, uid, inv)
                    invoices_group[repair.partner_invoice_id.id] = inv_id
                self.write(cr, uid, repair.id, {'invoiced': True, 'invoice_id': inv_id})

                for operation in repair.operations:
                    if operation.to_invoice == True:
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

                        invoice_line_id = inv_line_obj.create(cr, uid, {
                            'invoice_id': inv_id,
                            'name': name,
                            'origin': repair.name,
                            'account_id': account_id,
                            'quantity': operation.product_uom_qty,
                            'invoice_line_tax_id': [(6,0,[x.id for x in operation.tax_id])],
                            'uos_id': operation.product_uom.id,
                            'price_unit': operation.price_unit,
                            'price_subtotal': operation.product_uom_qty*operation.price_unit,
                            'product_id': operation.product_id and operation.product_id.id or False
                        })
                        repair_line_obj.write(cr, uid, [operation.id], {'invoiced': True, 'invoice_line_id': invoice_line_id})
                for fee in repair.fees_lines:
                    if fee.to_invoice == True:
                        if group:
                            name = repair.name + '-' + fee.name
                        else:
                            name = fee.name
                        if not fee.product_id:
                            raise osv.except_osv(_('Warning !'), _('No product defined on Fees!'))

                        if fee.product_id.property_account_income:
                            account_id = fee.product_id.property_account_income.id
                        elif fee.product_id.categ_id.property_account_income_categ:
                            account_id = fee.product_id.categ_id.property_account_income_categ.id
                        else:
                            raise osv.except_osv(_('Error !'), _('No account defined for product "%s".') % fee.product_id.name)

                        invoice_fee_id = inv_line_obj.create(cr, uid, {
                            'invoice_id': inv_id,
                            'name': name,
                            'origin': repair.name,
                            'account_id': account_id,
                            'quantity': fee.product_uom_qty,
                            'invoice_line_tax_id': [(6,0,[x.id for x in fee.tax_id])],
                            'uos_id': fee.product_uom.id,
                            'product_id': fee.product_id and fee.product_id.id or False,
                            'price_unit': fee.price_unit,
                            'price_subtotal': fee.product_uom_qty*fee.price_unit
                        })
                        repair_fee_obj.write(cr, uid, [fee.id], {'invoiced': True, 'invoice_line_id': invoice_fee_id})
                res[repair.id] = inv_id
        return res

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
        repair_line = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids, context=context):
            repair_line.write(cr, uid, [l.id for
                    l in repair.operations], {'state': 'confirmed'}, context=context)
            repair.write({'state': 'under_repair'})
#        if self.is_magasinier(cr, uid, ids, context):    
        move_obj = self.pool.get('stock.move')
        repair_line_obj = self.pool.get('mrp.repair.line')
        for repair in self.browse(cr, uid, ids, context=context):
            for move in repair.operations:
                if move.product_id.type  in ('product', 'consu'):
                    move_id = move_obj.create(cr, uid, {
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'product_qty': move.product_uom_qty,
                        'product_uom': move.product_uom.id,
                        'address_id': repair.address_id and repair.address_id.id or False,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'tracking_id': False,
                        'state': 'done',
                    })
                    repair_line_obj.write(cr, uid, [move.id], {'move_id': move_id, 'state': 'done'}, context=context)              
        return True

    def action_repair_end(self, cr, uid, ids, context=None):
        """ Writes repair order state to 'To be invoiced' if invoice method is
        After repair else state is set to 'Ready'.
        @return: True
        """
        for order in self.browse(cr, uid, ids, context=context):
            val = {}
            val['repaired'] = True
            if (not order.invoiced and order.invoice_method=='after_repair'):
                val['state'] = '2binvoiced'
            elif (not order.invoiced and order.invoice_method=='b4repair'):
                val['state'] = 'ready'
            else:
                pass
            self.write(cr, uid, [order.id], val)
        return True

    def wkf_repair_done(self, cr, uid, ids, *args):
        self.action_repair_done(cr, uid, ids)
        return True

    def action_repair_done(self, cr, uid, ids, context=None):
        """ Creates stock move and picking for repair order.
        @return: Picking ids.
        """
        res = {}
        for repair in self.browse(cr, uid, ids, context=context):         
            self.write(cr, uid, [repair.id], {'state': 'done'})
        return res


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
    _order = "product_id"
    
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
            res[line.id] = line.to_invoice and line.price_unit * line.product_uom_qty or 0
            cur = line.repair_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
       
    _columns = {
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
        if repair_line.product_id.type  in ('product', 'consu') and repair_line.product_uom_qty > repair_line.product_id.virtual_available :
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
        (_quantity_exists_in_warehouse,'Error: The quantity does not exist in warehouse.', ['product_uom_qty']),
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
            res[line.id] = line.to_invoice and line.price_unit * line.product_uom_qty or 0
            cur = line.repair_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    _columns = {
        'repair_id': fields.many2one('mrp.repair', 'Repair Order Reference', required=True, ondelete='cascade', select=True),
        'name': fields.char('Description', size=64, select=True,required=True),
        'product_id': fields.many2one('product.product', 'Product'),
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
