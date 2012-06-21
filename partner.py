
from osv import fields, osv

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    _defaults = {
        'ref': lambda obj, cr, uid, context:  obj.pool.get('ir.sequence').get(cr, uid, 'res.fournisseur') if context.get('default_customer') == False else  obj.pool.get('ir.sequence').get(cr, uid, 'res.client'),     
    }
    _columns = {
        'voitures_ids' : fields.one2many('mrp.car', 'partner_id', 'Voitures'),   
    }    
    _sql_constraints = [
        ('uniq_ref', 'unique(ref)', "The Reference must be unique"),
    ]
    
res_partner()

