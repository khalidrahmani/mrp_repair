
from osv import fields, osv

class code_marque(osv.osv):
    
    _name = 'code.marque'
    _description = "Code Marque"
    _order = "name"
    _columns = {
        'name': fields.char("Code Marque", size=64),
    }
    
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The Name must be unique"),
    ]
    
code_marque()

class product_product(osv.osv):

    _name = 'product.product'    
    _inherit = 'product.product'    
    _description = 'Product'
    _order = 'product_tmpl_id,casier'
            
    _columns = {
        'default_code': fields.char('Reference',size=24, required=True),                
        'code_marque': fields.many2one('code.marque','Code Marque'),
        'marque': fields.many2one('car.marque','Marque'),
        'modele': fields.many2one('car.modele','Modele',domain="[('marque_id','=',marque)]"),
        'matricule' : fields.char('Matricule', size=64),
        'casier' : fields.char('Casier', size=64),
        'casier2' : fields.char('Casier2', size=64),        
        'kilometrage' : fields.char('Kilometrage', size=64),
        'similar_products' : fields.one2many('similar.product.line', 'product_id_ref', 'Similar Products'),                
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        args.append(['create_uid','=',uid])      
        return super(product_product, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def _check_defaultcode_and_variants(self, cr, uid, ids):
        for session in self.browse(cr, uid, ids):
            res = self.search(cr, uid, [ ('default_code','=',session.default_code),
                                         ('variants','=',session.variants)
                                       ])
            # Result will contain the current session, we remove it here.
            res.remove( session.id )
            if len(res):
                # If we have any results left
                # we have duplicate entries
                return False
        return True
    
    _constraints = [(_check_defaultcode_and_variants,
                    'Reference has to be unique.',
                    ['default_code','variants'])
                   ]
  
    _sql_constraints = [ ('default_code_uniq', 'unique (default_code, variants)', """Reference doit etre unique."""), ]

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}

        product = self.read(cr, uid, id, ['default_code'], context=context)
        if not default:
            default = {}
        default = default.copy()
        default['default_code'] = product['default_code'] + ' (copy)'

        return super(product_product, self).copy(cr=cr, uid=uid, id=id, default=default, context=context) 
                          
product_product()


class similar_product_line(osv.osv):
    _name = 'similar.product.line'        
    _description = 'similar product line'    
    
    _columns = {
        'product_id_ref': fields.many2one('product.product', 'Product Ref',ondelete='cascade', select=True),                
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok','=',True)], required=True),                
    }
                        
similar_product_line()    