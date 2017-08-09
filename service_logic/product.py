from openerp import models, fields, api

class product_brand(models.Model):
    _name="product.brand"    
    
    name=fields.Char("Name")
    product_ids = fields.Many2one('product.template','Product')
    
class product_model(models.Model):
    _name="product.model"
    
    name=fields.Char('Name')
    brand_ids = fields.Many2one('product.brand','Brand')  
    
class part_part(models.Model):
    _name = 'part.part'
    
    product_part = fields.Many2one('product.template','Name',domain="[('isParts', '=', True)]")
    description = fields.Char('Description')
    quantity = fields.Float('Quantity')
    pro_ids = fields.Many2one('product.template','Product')    
    
class part_accessories(models.Model):
    _name = 'part.accessories'
    
    product_accessories = fields.Many2one('product.template','Name')
    description = fields.Char('Description')
    quantity = fields.Float('Quantity')
    productss_ids = fields.Many2one('product.template','Product')    
    
class product_template(models.Model):
    _inherit="product.template"
    
    brand_ids = fields.Many2one('product.brand','Brand',)
    model_ids = fields.Char('Model No')
    serial_no = fields.Char('Serial No')
    chassis_no = fields.Char('Chassis No')
    pick_up_unit = fields.Char('Pick Up Unit')
    core_unit = fields.Char('CD/DVD Core Unit')
    amp_ic = fields.Char('AMP IC')
    micom_ic = fields.Char('MICOM IC')
    regulator_ic = fields.Char('Regulator IC')
    tuner_amp_unit = fields.Char('Tuner AMP Unit')
    bt_module = fields.Char('BT Module')
    mechanism = fields.Char('Mechanism')
    cord_assy = fields.Char('Cord Assy')
    detach_grill = fields.Char('Detach Grill Assy')
    monitor_pcb = fields.Char('Monitor PCB')
    touch_panel = fields.Char('Touch Panel')
    lcd = fields.Char('LCD')
    keyboard_pcb = fields.Char('Keyboard PCB')
    if_unit = fields.Char('IP UNIT')
    dual_core = fields.Char('Dual Core Unit')
    sensor_unit = fields.Char('Sensor Unit')
    sd_card = fields.Char('SD Card')
    part_name = fields.Char('Part Name')
    part_no = fields.Char('Part No')
    twelve_line_up = fields.Char('2012 Line Up')
    thirteen_line_up = fields.Char('2013 Line Up')
    fourteen_line_up = fields.Char('2014 Line Up')
    fifteen_line_up = fields.Char('2015 Line UP')
    sixteen_line_up = fields.Char('2016 Line UP')
    seventeen_line_up = fields.Char('2017 Line UP')
    part_ids = fields.One2many('part.part','pro_ids',string="Part")
    accessories_ids = fields.One2many('part.accessories','productss_ids',string="Accessories")    
    
