
from osv import fields,osv
import netsvc


class mrp_car(osv.osv):
    
    _name = 'mrp.car'
    _description = "Voitures"
    
    def _car_name(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        for car in self.browse(cr, uid, ids, context=context):            
            res[car.id] = (car.marque.name + " " +car.modele.name + " " +car.chassis) or ''
        return res        
        
    _columns = {
        'name': fields.function(_car_name, string='Name', size=64, type="char", store=True, select=True),        
        'marque': fields.many2one('car.marque','Marque', required=True),
        'modele': fields.many2one('car.modele','Modele',domain="[('marque_id','=',marque)]", required=True),
        'matricule': fields.char('Matricule',size=24, required=True),
        'chassis': fields.char('Chassis',size=24, required=True),
        'kilometrage': fields.char('Kilometrage',size=24),
        'mec': fields.date('Mise en circulation'),        
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),        
    }
    _sql_constraints = [
        ('uniq_chassis', 'unique(chassis)', "Le Chassis doit etre unique."),
    ]
        
mrp_car()

