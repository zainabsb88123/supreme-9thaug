from odoo import models, fields, api,tools, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil import relativedelta
from datetime import datetime,timedelta
import datetime
import time
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import Warning


class product_detail_line(models.Model):
    _name="product.detail.line"    
    
    prod_name= fields.Many2one('product.template','Product')
    purchase_date = fields.Date('Purchase Date')
    warranty_date =fields.Date('Warranty')
    related_work_order = fields.Char('Related Work Order')
    res_ids= fields.Many2one('res.partner')
    
    @api.onchange('purchase_date')
    def onchange_purchase_date(self):
      
        if self.purchase_date:
            w_date = self.purchase_date
            product = self.prod_name
            if product:
                current_date = datetime.datetime.now()
                j = datetime.datetime.strptime(w_date, '%Y-%m-%d')
                date_diff = (current_date - j).days
                if date_diff < 0:                        
                    return {
                        'warning': {'title': 'Error!', 'message': 'Purchase Date cannot be greater than current date.'},
                        'value': {
                         'purchase_date': None,
                         'flat': None,
                        } 
                    }
            else:
                return {
                        'warning': {'title': 'Error!', 'message': 'Please Enter the Product Name before Purchase Date'},
                        'value': {
                         'purchase_date': None,
                         'flat': None,
                        } 
                    }  

    @api.onchange('warranty_date')
    def onchange_warranty_date(self):
        if self.warranty_date:
            warranty_date = self.warranty_date
            purchase_date = self.purchase_date
            print'============purchase_date============',purchase_date
            if purchase_date:
                from_dt = datetime.datetime.strptime(purchase_date, '%Y-%m-%d')
                to_dt = datetime.datetime.strptime(warranty_date, '%Y-%m-%d')
                timedelta = from_dt - to_dt
                diff_day = timedelta.days
                if diff_day > 0:
                    return {
                        'warning': {'title': 'Error!', 'message': 'Warranty Date should be greater than purchase date.'},
                        'value': {
                         'warranty_date': None,
                         'flat': None,
                        } 
                    }
            else:
                return {
                        'warning': {'title': 'Error!', 'message': 'Please enter purchase date before warranty date.'},
                        'value': {
                         'warranty_date': None,
                         'flat': None,
                        } 
                    }
                                    
    @api.multi
    def create_work_order(self):
        act_window = self.pool.get('ir.actions.act_window')
        record = self.res_ids
        name = record.name
        add = record.street
        add2 = record.street2
        city = record.city
        state = record.state_id.name
        current_date = datetime.datetime.now()
        zip = record.zip
        email = record.email
        mob = record.mobile
        country = record.country_id.name
        ress = self.prod_name
	if not ress:
            raise UserError(_('Please fill Product Name before creating a WorkOrder.'))
        model = ress.model_ids
        serial = ress.serial_no
        pur_date = self.purchase_date
        w_date = self.warranty_date
        
        vals = {'name':record.id,'address':add,'street2':add2,'city':city,'zip':zip,'email':email,'mobile':mob,
        'purschase_date':pur_date,'model_no':model,'serial_no':serial,'warranty_date':w_date,
        'state_ids':state,'country':country,'product_ids':ress.id,'rec_date':current_date}

        work_obj = self.env['work.order']
        work_orders = work_obj.create(vals)

        if self._context.get('open_invoices', False):
            return self.action_view_worder(work_orders)
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def action_view_worder(self,work_orders_ids):
        work_order_ids = work_orders_ids
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('service_logic.action_work_order_create_service')
        list_view_id = imd.xmlid_to_res_id('service_logic.view_work_order_tree')
        form_view_id = imd.xmlid_to_res_id('service_logic.view_work_order_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form'],[list_view_id, 'tree']], 
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if work_order_ids:
            result['res_id'] = work_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
class work_order_documents(models.Model):
    _name = "work.order.documents"
    
    name = fields.Char('Name')
    attach_files = fields.Binary('Attach Files')
    file_name = fields.Char('File Name')
    expire_date = fields.Date('Expire Date')
    part_ids = fields.Many2one('res.partner')
    
class res_partner(models.Model):
    _inherit="res.partner"
   
    
    @api.multi
    def _get_order(self):       
        for order in self:
            work_order_ids = order            
            order.update({
                'work_order_ids': work_order_ids.ids
            })
                  
    prod_id = fields.One2many('product.detail.line','res_ids',string="Product")
    document_id = fields.One2many('work.order.documents','part_ids',string="Documents")
    work_order_ids = fields.Many2many("work.order", string='Works', compute="_get_order",copy=False)    

    @api.model
    def create(self,  vals):
#	if vals['email'] == False:
#            raise UserError(_('Enter the Email Address.'))
#        if vals.get('mobile'):
#            exis_mobile_id = self.search([('mobile','=', vals['mobile'])])
#            if exis_mobile_id:
#                raise UserError(_('Mobile Number should be Unique.'))               
#        if vals.get('email'):
#            exis_data_id = self.search( [('email','=', vals['email'])])
#            if exis_data_id:
#                raise UserError(_('This Email Already Exists.'))
        return super(res_partner ,self).create( vals)

    @api.multi
    def write(self,  vals):        
#        if vals.get('email'):
#            exis_data_id = self.search( [('email','=', vals['email'])])
#            if exis_data_id:
#                raise UserError(_('This Email Already Exists.'))
        return super(res_partner ,self).write(vals)

class part_details(models.Model):
    _name = 'part.details'
    
    part_replaced_id = fields.Many2one('work.order','Part Replaced Id')
    part_replaced_name = fields.Many2one('product.template','Product Name',domain="[('isParts', '=', True)]")
    part_replaced_description = fields.Text('Part Description')
    part_replaced_qty = fields.Float('Qty')
    part_replaced_num = fields.Char('Part Replaced No.')

    @api.multi
    @api.onchange('part_replaced_name')
    def onchange_part_replaced_name(self):
        res = {}
        name = self.part_replaced_name.name
        desc = self.part_replaced_name.description_sale
        if desc:
            name += '\n' + self.part_replaced_name.description_sale
        res= {'value':{'part_replaced_description':name}}
        return res

class accessories_table(models.Model):    
    _name = 'accessories.table'
    
    name = fields.Char('Name')
    access = fields.Many2many('work.order',id1='accessories',id2='accesso',string='Access')
    
class work_order(models.Model):
    _name = "work.order"
    _order = "job_no desc"
    _rec_name = "job_no"
    
    @api.multi
    def _get_sale_order(self):       
        for order in self:
            sale_order_ids = order                                    
            order.update({
                'sale_order_ids': sale_order_ids.ids
            })
            
    @api.multi
    def _get_warranty_status(self):
        record = self.warranty_date
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        if record >= current_date:
            self.check_warranty = "yes"
        else:
            self.check_warranty = "no"
    def _compute_sale_order_count_work(self):
        res={}
        record = self.name
        print'===================record===================',record
	
        job = self.job_no
        print'=========job==========',job
	
        
        print'===================record===================',record
        sale_id = self.env['sale.order'].search([('job_no','=',job)])
        print'================sale_id=============',sale_id
        

        sale_count =0
        for i in sale_id:
            sale_count+=1
            print "====sale_count=========",sale_count
        self.sale_order_count_work = sale_count
        print'==============ssssssssssssss=================',self.sale_order_count_work
        res[self.id] = self.sale_order_count_work
      
        return res
        
            
    def _compute_purchase_order_count_work(self):
        res={}
        record = self.job_no
        print'===================record===================',record
        purchase_id = self.env['purchase.order'].search([('job_no_pur','=',record)])
        print'================purchase_id=============',purchase_id
        
        purchase_count =0
        for i in purchase_id:
            purchase_count+=1
            print "====purchase_count=========",purchase_count
        self.purchase_order_count_work = purchase_count
        print'==============ssssssssssssss=================',self.purchase_order_count_work
        res[self.id] = self.purchase_order_count_work
      
        return res
            
    
    name= fields.Many2one('res.partner','Name')
    address=fields.Char('Address')
    email=fields.Char('Email ID')
    mobile=fields.Char('Mobile',size=10)
    rec_date=fields.Date('Received Date')
    purschase_date=fields.Date('Purchase Date')
    send_to_supreme_asc_date=fields.Date('Send To Supreme ASC Date')
    supreme_receive_from_asc_date=fields.Date('Supreme Receive From ASC Date')
    asc_job_no=fields.Integer('ASC Job No')
    brand=fields.Char('Brand')
    model_no=fields.Char('Model No')
    serial_no=fields.Char('Serial No')
    warranty_date=fields.Date('Warranty Status')
    check_warranty = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Warranty",compute="_get_warranty_status")
    in_warranty = fields.Boolean('In Warranty')
    out_warranty = fields.Boolean('Out Warranty')
    service_required=fields.Text('Service Required/Symptoms(Customers)')
    actual_symptoms=fields.Text('Actual Symptoms')
    repair_description=fields.Text('Repair Description')
    engg_name=fields.Many2one('hr.employee','Engineer Name')
    repair_date=fields.Date('Repair Date')
    customer_comment=fields.Text('Customers Comments')
    no_box_pack=fields.Boolean('No Box')
    tear_box_pack=fields.Boolean('Tear Box')
    good_box_pack=fields.Boolean('Good Box')
    surface_of_packing=fields.Selection([('no_box','No Box'),('tear_box','Tear Box'),('good_box','Good Box')],string="Surface Of Packing")
    surface_of_set=fields.Selection([('no_box','No Box'),('tear_box','Tear Box'),('good_box','Good Box')],string="Surface Of set")
    no_box_set=fields.Boolean('No Box')
    tear_box_set=fields.Boolean('Tear Box')
    good_box_set=fields.Boolean('Good Box')
    accessories = fields.Many2many('accessories.table',id1='accessory_id',id2='accessories',string="Accessories")
    others=fields.Char('Others')
    street2 = fields.Char('Street2')
    city=fields.Char('City')
    state_ids=fields.Char('State')
    country = fields.Char('Country')
    zip=fields.Char('Zip')
    job_no=fields.Char('Job No',readonly=True)    
    part_replaced=fields.Many2one('product.template',string='Part Replaced Name')    
    check_part = fields.Selection([('yes','Yes'),('no','No')],string='Part Replaced',readonly=False,default='no')    
    is_no = fields.Boolean(string="No", default=False)
    product_ids = fields.Many2one('product.template','Product Name')
    sale_order_ids = fields.Many2many("sale.order", string='Sales', compute="_get_order",copy=False)
    document_received = fields.Boolean('Documents Received')
    part_details = fields.One2many('part.details','part_replaced_id','Part Details')
    approved_by = fields.Many2one('res.users','Approved By')
    check_approve = fields.Boolean('Check Approve')
    stages = fields.Selection([('open','Open'),('work_in_progress','Work In Progress'),('spare_requested','Spare Requested'),('complete','Complete'),('close','Close')],string="Stages",default="open")
    sale_order_count_work = fields.Integer(compute='_compute_sale_order_count_work', string='# of Sales Order')
    sale_order_work_ids = fields.One2many('sale.order', 'partner_id', 'Sales Order')
    purchase_order_count_work = fields.Integer(compute='_compute_purchase_order_count_work', string="Purchase Order")
    purchase_order_work_ids = fields.One2many('purchase.order','partner_id','Purchase Order')
    user_id = fields.Many2one('res.users',"Signed In",default= lambda self: self.env.uid,)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    manager_id = fields.Many2one('res.users',string="Manager")
    receiptionist_id = fields.Many2one('res.users', string="Receiptionist")
    store_id = fields.Many2one('res.users', string="Store Operation")
    backend_id = fields.Many2one('res.users',string="Backend Operation")


    
    @api.model
    def create(self, vals):
	if vals['name'] == False:
            raise UserError(_('Enter the Customer Name.'))
        if vals.get('job_no','/')=='/':
            vals['job_no'] = self.env['ir.sequence'].next_by_code('work.order') or '/'  
	
                              
        return super(work_order, self).create(vals)
    
    @api.onchange('mobile')
    def onchange_mobile(self):
        if not self.mobile:
            return {}
        if not self.mobile.isdigit():
            raise UserError(_('Please enter a valid Mobile No.'))
        return {}
 

            
    @api.onchange('check_part')
    def onchange_check_part(self):
        self.is_no = (self.check_part == 'no')            
        
    @api.multi
    @api.onchange('name')
    def onchange_work_order_name(self):
        res= {}
        if self.name:
            rec = self.name
            partner_obj= self.env['res.partner']            
            res= {'value':{'address':rec.street,'street2':rec.street2,'city':rec.city,
            'state_ids':rec.state_id.name,'zip':rec.zip,'email':rec.email,'mobile':rec.mobile,
            'product_ids':rec.prod_id.prod_name.id,
            'model_no':rec.prod_id.prod_name.model_ids,'serial_no':rec.prod_id.prod_name.serial_no,
            'warranty_date':rec.prod_id.warranty_date,'purschase_date':rec.prod_id.purchase_date}}

        return res
    
    @api.multi
    @api.onchange('product_ids')
    def onchange_product_name(self):
        res = {}
        if self.product_ids:
            rec = self.product_ids                        
            res = {'value':{'model_no':rec.model_ids,'serial_no':rec.serial_no}}        
        return res

    @api.multi
    @api.onchange('approved_by')
    def onchange_approved_by(self):
        res = {}
        if self.approved_by:
            rec = self.approved_by                        
            res = {'value':{'manager_id':rec.id}}        
        return res
    
    @api.multi
    def create_work_order_purchase_order(self,):
	self.stages = "spare_requested"                
        act_window = self.pool.get('ir.actions.act_window')        
        record=self.name
	if not record:
	    raise UserError(_('Please fill The Customer Name.'))
	store = self.store_id.login
	if not store:
	    raise UserError(_('Please Fill the Store Operation Name.'))
        email = self.manager_id.login
	if not email:
	    raise UserError(_('Please Fill the Manager Name.'))
	job_num = self.job_no
        print'-------'
        pr_id = self.product_ids        
        part_repl = self.part_details
        print'========part_repl========',part_repl
        if not part_repl:
            raise UserError(_('Please fill Product Name before creating a Purchase Order.'))
        current_date = datetime.datetime.now()
        purchase_order_vals_list = []
	name = ''
        qqtty = ''
        for part in part_repl:
            repl = part.part_replaced_name
            print'---------',part.part_replaced_name.id
	    if not repl:
		raise UserError(_('Please Fill The Product Name in Part Replaced Details Table'))
            name+= part.part_replaced_name.name+','+' '
            desc_sale = part.part_replaced_name.description_sale
            if desc_sale:
                name += '\n' + part.part_replaced_name.description_sale
            desc= name
            qty= part.part_replaced_qty
            quantity = str(qty)
            print'=============quantity=============',quantity
            qqtty+= quantity+','+' '
            if not repl:
                raise UserError(_('Please fill Product Name before creating a Purchase Order.'))
            if not desc:
                raise UserError(_('Please fill Product Description before creating a Purchase Order.'))
            print'llllllllll',repl        
            vals = (0,0,{
                    'product_id': repl.id,
                    'name':desc,
                    'product_qty':qty,
                    'product_uom' : part.part_replaced_name.uom_id.id,
                    'date_planned':current_date,
                    'price_unit':0.0
                })
            purchase_order_vals_list.append(vals)           
        purchase_obj = self.env['purchase.order']
        
	partner_id = self.env['res.partner'].search([('name','=','Administrator')])
        purchase_orders = purchase_obj.create({'job_no_pur':job_num,'company_check_pur': True,'partner_id':partner_id.id,'order_line':purchase_order_vals_list})
	email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])

        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Create Purchase Order')])
        replaced_data= temp.body_html.replace('${object.partner_name}',record.name)
        replaced_data_one= replaced_data.replace('${object.job_no}',job_num)
        replaced_data_two= replaced_data_one.replace('${object.part}',name)
        
        replaced_data_three= replaced_data_two.replace('${object.quantity}',qqtty)
        msg = ir_mail_server.build_email(
            email_from=user,
            email_to=[store,email,"zainabsb88@gmail.com"],
            subject="",
            body=replaced_data_three,
            body_alternative=replaced_data_three,
            #reply_to=[data.email_from],              
            object_id=1,
            subtype='html',
            )
        res = ir_mail_server.send_email(msg,mail_server_id=2) 
        
        return self.action_view_purchaseorder(purchase_orders)                            
        return {'type': 'ir.actions.act_window_close'}   
    
    @api.multi
    def action_view_purchaseorder(self,purchase_orders):
        purchase_order_ids = purchase_orders        
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('service_logic.action_purchase_order_form')
        list_view_id = imd.xmlid_to_res_id('purchase.purchase_order_tree')
        form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form'],[list_view_id, 'tree']], 
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if purchase_order_ids:
            result['res_id'] = purchase_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def create_work_order_sale_order(self,):                
	
        act_window = self.pool.get('ir.actions.act_window')        
        record=self.name
	if not record:
	    raise UserError(_('Please Fill the Customer Name.'))
	store = self.store_id.login
	if not store:
	    raise UserError(_('Please fill the Store Operation Name.'))
	approve = self.approved_by
	manager = self.manager_id
        email = self.manager_id.login
	if not email:
	    raise UserError(_('Please Fill the Manager Name.'))
        current_date = datetime.datetime.now()        
        job = self.job_no
        pr_id = self.product_ids
        part_check = self.check_part        
        service = self.service_required
        check_warr = self.check_warranty      
	sale_id = self.env['sale.order'].search([('job_no','=',job)])
        if sale_id:
            raise UserError(_('There already exists a sale order for this work order'))
        sale_order_obj = self.env['sale.order']
        partner_id = self.env['res.partner'].search([('id','=',1)])        
        part_repl = self.part_details
        print'========part_repl========',part_repl        
        sale_order_vals_list = []
        prod_id = self.env['product.template'].search([('name','=','Service')])
        if part_check == 'no':
            if check_warr == 'yes': 
                vals_lines = {
                        'product_id': prod_id.id,
                }
                vals = {
                'job_no':job,'partner_id':record.id,'repair_product':pr_id.id,'approve_by_mgr':manager.id,'order_line':[(0, 0, vals_lines)],
                'partner_invoice_id':partner_id.id,'state':'sale','confirmation_date':current_date
                }
	
		
                sale_orders = sale_order_obj.create(vals)
		print'======================================',sale_orders
		
        if part_check == 'no':
            if check_warr == 'no':  
                vals_lines = {
                        'product_id': prod_id.id,
                }
                vals = {
                'job_no':job,'partner_id':record.id,'repair_product':pr_id.id,'approve_by_mgr':manager.id,'order_line':[(0, 0, vals_lines)],
                'state':'sale','confirmation_date':current_date
                }
                sale_orders = sale_order_obj.create(vals)
 
               # sale_orders = sale_order_obj.create({'job_no':job,'partner_id':record.id,
              # 'state':'sale','confirmation_date':current_date,'order_line':vals})        
#        if not part_repl:
#            raise UserError(_('Please fill Product Name before creating a Sale Order.')) 
        if part_check == 'yes':
            if check_warr == 'yes':
		if not part_repl:
	                raise UserError(_('Please fill Product Name before creating a Sale Order.'))
                for part in part_repl:
                    repl = part.part_replaced_name.id
		    print'================repl====================',repl
		    if not repl:
			raise UserError(_('Please fill The Product Name in Part Replaced Detail Table'))
		    
                    name = part.part_replaced_name.name
		    print'---------------name-------------',name
		    
                    desc_sale = part.part_replaced_name.description_sale
                    if desc_sale:
                        name += '\n' + part.part_replaced_name.description_sale
                    desc= name
                    qty = part.part_replaced_qty
                    print'oooooooooo',part_repl
                    vals = (0,0,{
                        'product_id': repl,                    
                        'product_uom_qty':qty,                                        
                        'price_unit':0.0
                    })
		    print'==================vals====================',vals
		                          
                    sale_order_vals_list.append(vals)           
                sale_orders = sale_order_obj.create({'job_no':job,'partner_id':record.id,'approve_by_mgr':manager.id,'repair_product':pr_id.id,
                'partner_invoice_id':partner_id.id,'state':'sale','confirmation_date':current_date,
                'order_line':sale_order_vals_list})
		ab = sale_orders.write({'order_line':[(0, 0, {'product_id': prod_id.id})]}) 
        if part_check == 'yes':
            if check_warr == 'no':
		if not part_repl:
	                raise UserError(_('Please fill Product Name before creating a Sale Order.'))
                for part in part_repl:
                    repl = part.part_replaced_name.id
		    if not repl:
			raise UserError(_('Please Fill the Product Name in Part Replaced Detail Table'))
                    name = part.part_replaced_name.name
                    price = part.part_replaced_name.standard_price
                    desc_sale = part.part_replaced_name.description_sale
                    if desc_sale:
                        name += '\n' + part.part_replaced_name.description_sale
                    desc= name
                    qty = part.part_replaced_qty
                    vals = (0,0,{
                        'product_id': repl,                    
                        'product_uom_qty':qty,                                        
                        'price_unit':price
                    })                      
                    sale_order_vals_list.append(vals)                           
                sale_orders = sale_order_obj.create({'job_no':job,'partner_id':record.id,'state':'sale','approve_by_mgr':manager.id,
                'confirmation_date':current_date,'order_line':sale_order_vals_list})
		ab=sale_orders.write({'order_line':[(0, 0, {'product_id': prod_id.id})]})
	email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])

        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Create Sale Order')])
        replaced_data= temp.body_html.replace('${object.partner_name}',record.name)
        replaced_data_one= replaced_data.replace('${object.job_no}',job)
        msg = ir_mail_server.build_email(
            email_from=user,
            email_to=[store,email,'zainabsb88@gmail.com'],
            subject="",
            body=replaced_data_one,
            body_alternative=replaced_data_one,
            #reply_to=[data.email_from],              
            object_id=1,
            subtype='html',
            )
        res = ir_mail_server.send_email(msg,mail_server_id=2)       
#        sale_orders.write({'order_line':[(0, 0, {'product_id': prod_id.id})]})
        return self.action_view_saleorder(sale_orders)
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def action_view_saleorder(self,sale_orders):
        sale_order_ids = sale_orders        
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('service_logic.action_sale_order_form_new')
        list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form'],[list_view_id, 'tree']], 
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        if sale_order_ids:
            result['res_id'] = sale_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi    
    def approve(self):
        self.check_approve = True
        self.write({'document_received' : True,'stages': 'work_in_progress'})
        if not self.approved_by:
            raise UserError(_('It is still not approved.'))
        receiptionist = self.receiptionist_id.login
        if not receiptionist:
            raise UserError(_('Please fill the Receiptionist Name.'))
        job_num = self.job_no
        customer = self.name
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])
	cust = customer.name
        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Manager Send Approval to Receiptionist')])
	if not cust:
		raise UserError(_('Please fill the Customer Name.'))
	replaced_data= temp.body_html.replace('${object.partner_name}',customer.name)
        replaced_data_one= replaced_data.replace('${object.job_no}',job_num)
        msg = ir_mail_server.build_email(
            email_from=user,
            email_to=[receiptionist,'zainabsb88@gmail.com'],
            subject="",
            body=replaced_data_one,
            body_alternative=replaced_data_one,
            #reply_to=[data.email_from],              
            object_id=1,
            subtype='html',
            )
        res = ir_mail_server.send_email(msg,mail_server_id=2)    
        return
    
    @api.multi
    def request_approval(self):
        approve = self.approved_by
        email = self.approved_by.login
        
        if not approve:
           raise UserError(_('Please fill the Authorised Person Name.')) 
        if not email:
            raise UserError(_('Authorised Person Email Does Not Exist.'))
        usr = self.user_id
        print'=======usr=========',usr.name
	record = self.name
        partner = record.name
	if not partner:
		raise UserError(_('Please fill Customer Name.'))
        job = self.job_no
        print'--------------job----------------',job
        product = self.product_ids
        prod = product.name
	if not prod:
		raise UserError(_('Please fill Product Name.'))
        user_id = self.env['res.users'].search([('id','=',1)])
        print'=================partner_id===============',user_id.login
        
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user','=','erekta@outlook.com')])
        
#        email = ir_mail_server.browse([('id','=',2)]).smtp_user
#        print'==========ir_mail_server============',ir_mail_server.smtp_user
        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','document_approve_by_authorised')])
	replaced_data= temp.body_html.replace('${object.partner_name}',record.name)
        replaced_data_one= replaced_data.replace('${object.job_no}',job)
        replaced_data_two= replaced_data_one.replace('${object.product}',product.name)
        replaced_data_three= replaced_data_two.replace('${object.sign_in}',usr.name)


        msg = ir_mail_server.build_email(
        email_from=user,
           email_to=[email,'zainabsb88@gmail.com'],
           subject="",
           body=replaced_data_three,
           body_alternative=replaced_data_three,
           #reply_to=[data.email_from],              
           object_id=1,
           subtype='html',
           )
        res = ir_mail_server.send_email(msg,mail_server_id=2)
    @api.multi    
    def accept_defective_parts(self):
        stock_picking = self.pool.get('stock.picking')
        act_window = self.pool.get('ir.actions.act_window')        
        record = self.name
        job = self.job_no
        add = self.address
        part_repl = self.part_details
        usr = self
        if not part_repl:
            raise UserError(_('Please fill Product Name before creating a Delivery Order.'))
        stock_id = self.env['stock.location'].search([('id', '=', 9)])
        company = self.company_id
        print'===================', company
        co = company.name
        comp = company.name + ": Receipts"
        print'0000000000000', comp
        locat = company.name + "/Stock"

        comp_id = self.env['res.company'].search([('name', '=', 'My Company')])
        print'--------', co
        ab = self.search([('company_id.name', '=', 'My Company')])
        if ab:

            sto_id = self.env['stock.location'].search([('id', '=', 15)])
        else:
            sto_id = self.env['stock.location'].search([('company_id.name', '=', co), ('usage', '=', 'internal')])
            print'mmmmmmmmmmmmm', sto_id

        stoc = self.env['stock.picking.type'].search([('warehouse_id.name', '=', company.name), ('name', '=', "Receipts")])
        print'=============stoc============', sto_id

        vals_list = []
        unit_id = self.env['product.uom'].search([('id', '=', 1)])
        print'============unit_id================', unit_id.id
        for my in part_repl:
            pro_name = my.part_replaced_name
            print'=========pro_name=========', pro_name

            qty = my.part_replaced_qty
            val_lines = (0, 0, {
                         'product_id': pro_name.id, 
                         'name':pro_name.id, 
                         'product_uom_qty':qty,
                         'product_uom':unit_id.id
                         })                      
            vals_list.append(val_lines)

        vals = {'partner_id':record.id, 'location_id':stock_id.id, 'picking_type_id':stoc.id,
        'location_dest_id':sto_id.id, 'origin': job,'customer_check': True,
        'move_lines':vals_list,}
        print'========vals=======', vals

        stock_picking_obj = self.env['stock.picking']
        stock_picking_orders = stock_picking_obj.create(vals)
        print "====stock_picking_orders=========", stock_picking_orders        

        if self._context.get('open_invoices', False):
            return self.action_view_accept_defective_parts(stock_picking_orders)
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def action_view_accept_defective_parts(self, stock_picking_orders):
               
        stock_picking_order_ids = stock_picking_orders
        print "========sale_order_idskk===========", stock_picking_order_ids
        
        print "========sale_order_idskk===========", stock_picking_order_ids.ids
        print "========sale_order_idskk===========", stock_picking_order_ids.ids
        
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('service_logic.action_stock_picking_service_form')
        list_view_id = imd.xmlid_to_res_id('stock.view_picking_tree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form'], [list_view_id, 'tree']], 
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        if stock_picking_order_ids:
            result['res_id'] = stock_picking_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def spare_replacement(self):
        record = self.name
	if not record:
	    raise UserError(_('Please Fill the Customer Name.'))
        job = self.job_no
        part_repl = self.part_details
	if not part_repl:
	    raise UserError(_('Please Fill the Part Replaced Details.'))
        backend = self.backend_id.login
        print'=======backend======',backend
	if not backend:
	    raise UserError(_('Please Fill The Backend Operation Name.'))
        
        store = self.store_id.login
	if not store:
	    raise UserError(_('Please Fill the Store Operation Name.'))
        email = self.manager_id.login
	if not email:
	    raise UserError(_('Please Fill the Manager  Name.'))
	name = ''
        qqtty = ''
        for part in part_repl:
                    repl = part.part_replaced_name.id
                    name+= part.part_replaced_name.name+','+' '
                    print'----------------------',name
                    
                    desc_sale = part.part_replaced_name.description_sale
                    if desc_sale:
                        name += '\n' + part.part_replaced_name.description_sale
                    desc= name
                    qty= part.part_replaced_qty
                    quantity = str(qty)
                    print'=============quantity=============',quantity
                    qqtty+= quantity+','+' '
		    
		    
        
                          
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])
       
        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Spare Replacement Notifies to Backend Operation')])
        replaced_data= temp.body_html.replace('${object.partner_name}',record.name)
        replaced_data_one= replaced_data.replace('${object.job_no}',job)
        replaced_data_two= replaced_data_one.replace('${object.part_replaced_name}',name)
        replaced_data_three= replaced_data_two.replace('${object.part_replaced_qty}',qqtty)
        msg = ir_mail_server.build_email(
                                         email_from=user,
                                         email_to=[backend,store,email,'zainabsb88@gmail.com'],
                                         subject="",
                                         body=replaced_data_three,
                                         body_alternative=replaced_data_three,
                                         #reply_to=[data.email_from],              
                                         object_id=1,
                                         subtype='html',
                                         )
        res = ir_mail_server.send_email(msg, mail_server_id=2)
    
    def complete_work_order(self):
        self.stages = "complete"
        receiptionist = self.receiptionist_id.login
	if not receiptionist:
	    raise UserError(_('Please Fill the Receiptionist Name.'))
        email = self.manager_id.login
	if  not email:
	    raise UserError(_('Please Fill the Manager Name.'))
        comment = self.customer_comment
	if not  comment:
	    raise UserError(_('Please Fill the Customer Comment.'))
        service = self.service_required
	description = self.repair_description
	if not description:
	    raise UserError(_('Please Fill the Repair Description.'))
        job = self.job_no
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])

        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Service Engg send reply to Receiptionist')])
        replaced_data= temp.body_html.replace('${object.job_no}',job)
        replaced_data_one= replaced_data.replace('${object.comment}',comment)
        replaced_data_two= replaced_data_one.replace('${object.description}',description)
#        
        msg = ir_mail_server.build_email(
            email_from=user,
            email_to=[receiptionist,email,'zainabsb88@gmail.com'],
            subject="",
            body=replaced_data_two,
            body_alternative=replaced_data_two,
            #reply_to=[data.email_from],              
            object_id=1,
            subtype='html',
            )
        res = ir_mail_server.send_email(msg,mail_server_id=2)  
        
    def close_work_order(self):
        self.stages = "close"
        email = self.manager_id.login
	if not email:
	    raise UserError(_('Please Fill the Manager Name.'))
        job = self.job_no
        print'----------job---------',job
        
        account_id = self.env['account.invoice'].search([('job_no','=',job)])
        print'================purchase_id=============',account_id
        print'=======================account_id=======================',account_id.number
        invoice_number = account_id.number
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])

        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Close Work Order')])
        replaced_data= temp.body_html.replace('${object.job_no}',job)
        replaced_data_one= replaced_data.replace('${object.invoice_number}',invoice_number)
        print'============replaced_data_one============',replaced_data_one
        
        
        msg = ir_mail_server.build_email(
            email_from=user,
            email_to=[email,'zainabsb88@gmail.com'],
            subject="",
            body=replaced_data_one,
            body_alternative=replaced_data_one,
            #reply_to=[data.email_from],              
            object_id=1,
            subtype='html',
            )
        res = ir_mail_server.send_email(msg,mail_server_id=2)
    
    
    

    @api.multi
    def assign_work_order(self):
        engg = self.engg_name
        print'======engg========',engg
        email = engg.work_email
        store = self.store_id.login
	if not store:
            raise UserError(_('Please Fill the Store Operation Name.'))

        job = self.job_no
        email_mgnr = self.manager_id.login
	if not email_mgnr:
            raise UserError(_('Please Fill the Manager Name.'))

        comment = self.customer_comment
        description=self.repair_description
	
	       
	if not comment:
	    raise UserError(_('Please Fill the Customer Comment'))
	
	    	
 
#        if not email:
#            raise UserError(_('Authorised Person Email Does Not Exit.'))
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user','=','erekta@outlook.com')])
        
#       
        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name','=','Receiptionist Assign Work Order To Service Engg')])
        replaced_data= temp.body_html.replace('${object.job_no}',job)
        replaced_data_one= replaced_data.replace('${object.comment}',comment)
        
#        

        if email:
            msg = ir_mail_server.build_email(
            email_from=user,
               email_to=[email,email_mgnr,store,'zainabsb88@gmail.com'],
               subject="",
               body=replaced_data_one,
               body_alternative=replaced_data_one,
               #reply_to=[data.email_from],              
               object_id=1,
               subtype='html',
               )
            res = ir_mail_server.send_email(msg,mail_server_id=2)
        
    
class sale_order(models.Model):
    _inherit="sale.order"
 
    job_no = fields.Char('Job No',readonly=True)
    repair_product = fields.Many2one('product.template','Repair Product')
    re_prod = fields.Char('Product')
    approve_by_mgr = fields.Many2one('res.users','Manager')
    
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'repair_prod': self.repair_product.id,
	    'approve_by_mrg_acc':self.approve_by_mgr.id,
            'job_no':self.job_no,

            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id
        }
        return invoice_vals

    

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    order_id = fields.Many2one('sale.order', 'Related_order')
    repair_prod = fields.Many2one('product.template','Repair Product')
    product_re = fields.Char('Product')
    job_no = fields.Char('Job No')
    approve_by_mrg_acc = fields.Many2one('res.users','Manager')

class purchase_order(models.Model):
    _inherit="purchase.order"
    
    job_no_pur = fields.Char('Job No')
    company_check_pur = fields.Boolean('Company Check')


class res_company(models.Model):
    _inherit="res.company"

    @api.model
    def _get_custom_parent_company(self):
        custom_parent_id = self.env['res.company'].search([('id','=',1)])
        return custom_parent_id 


    custom_parent_id = fields.Many2one('res.company','Parent Company',default = _get_custom_parent_company,readonly=True)

#class res_users(models.Model):
#    _inherit="res.users"
# 
#    is_receiptionist = fields.Boolean('Receiptionist')


class sale_advance_payment_inv(models.TransientModel):
    _inherit="sale.advance.payment.inv"
    
    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        print "===============order===================",order
        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') % \
                    (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'repair_prod': order.repair_product.id,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'account_analytic_id': order.project_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
        })
        invoice.compute_taxes()
        return invoice
    
    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
	name = sale_orders.partner_id.name
	email = sale_orders.partner_id.email
        job = sale_orders.job_no
	manager = sale_orders.approve_by_mgr.login
        product = sale_orders.repair_product.name
        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                })
                self._create_invoice(order, so_line, amount)
        email_ids = []
        ir_mail_server = self.env['ir.mail_server'].search([('smtp_user', '=', 'erekta@outlook.com')])
        
    #       
        user = ir_mail_server.smtp_user
        temp = self.env['mail.template'].search([('name', '=', 'Create Invoice')])
#	replaced_data = temp.body_html.replace('${object.partner_name}', name)
        replaced_data= temp.body_html.replace('${object.job_no}',job)
        replaced_data_one= replaced_data.replace('${object.product}',product)     


        msg = ir_mail_server.build_email(
                                         email_from=user,
                                         email_to=[email,manager,'zainabsb88@gmail.com'],
                                         subject="",
                                         body=replaced_data_one,
                                         body_alternative=replaced_data_one,
                                         #reply_to=[data.email_from],              
                                         object_id=1,
                                         subtype='html',
                                         )
        res = ir_mail_server.send_email(msg, mail_server_id=2)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    company_check = fields.Boolean('Company Check')
    customer_check = fields.Boolean('Customer Check')
#    @api.multi
#    def update_lot(self):
#        print'-------------',self.origin
#        origin = self.origin
#        stock_picking = self.env['stock.picking'].search([('name', '=',origin )])
#        for line in stock_picking:
#            print'kkkkkkkkkk',line.pack_operation_product_ids
#            for rec in line.pack_operation_product_ids:
#                print
#        
#        for line in self.pack_operation_product_ids:
#            print'---mmmmmmmmmmmmmmm',line.pack_lot_ids
#            for pack in line.pack_lot_ids:
#                print'0000000000000',pack.lot_name
                
#            print'ppppppppp',self.pack_operation_product_ids.pack_lot_ids
        
#        return
    @api.multi
    def send_to_customer(self):        
	
        partner_id = self.partner_id
        comp = self.company_id
        stock_id = self.env['stock.location'].search([('id', '=', 9)])
        stoc = self.env['stock.picking.type'].search([('warehouse_id.name', '=', comp.name), ('name', '=', "Delivery Orders")])
        prod = self.move_lines
        vals_list = []
        unit_id = self.env['product.uom'].search([('id', '=', 1)])

        company = self.company_id
        print'===================', company.name

        locat = company.name + "/Stock"
        comp_id = self.env['res.company'].search([('id', '=', 1)])
        ab = self.search([('company_id.name', '=', 'My Company')])

	print'kkkkkkkkkkkkkk', ab
	
        if ab:
	    
            sto_id = self.env['stock.location'].search([('id', '=', 15)])
        else:
	    
            sto_id = self.env['stock.location'].search([('company_id.name', '=', company.name), ('name', '=', 'Stock')])
            print'=============', sto_id
	    
        for my in prod:
            pro = my.product_id.id
            uom_qty = my.product_uom_qty    

            val_lines = (0, 0, {
                         'product_id': pro, 
                         'name':pro, 
                         'product_uom_qty':uom_qty,
                         'product_uom':unit_id.id
                         })                      
            vals_list.append(val_lines)

        vals = {
        'partner_id': partner_id.id,
        'location_id': sto_id.id,
        'picking_type_id': stoc.id,
        'location_dest_id': stock_id.id,
        'origin': self.name,
        'move_lines':vals_list,
	'customer_check' : True,
	'company_check' : True,
        }
        stock_picking_obj = self.env['stock.picking']
        stock_picking_orders = stock_picking_obj.create(vals)
        
        if self._context.get('open_invoices', False):
            return self.action_view_send_to_customer(stock_picking_orders)
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def action_view_send_to_customer(self, stock_picking_orders):
       
        stock_picking_order_ids = stock_picking_orders
        print "========sale_order_idskk===========", stock_picking_order_ids
        
        print "========sale_order_idskk===========", stock_picking_order_ids.ids
        print "========sale_order_idskk===========", stock_picking_order_ids.ids
        
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('service_logic.action_stock_picking_service_form')
        list_view_id = imd.xmlid_to_res_id('stock.view_picking_tree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form'], [list_view_id, 'tree']], 
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        if stock_picking_order_ids:
            result['res_id'] = stock_picking_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def send_to_company(self):        
        partner_id = self.partner_id
        print'==========', partner_id.name
        partner = self.env['res.partner'].search([('name', '=', 'Administrator')])
	source = partner.property_stock_supplier.id
        comp = self.company_id
        stck_id = self.env['stock.location'].search([('id', '=', 15)])
        print'pppppppppp', stck_id
        soce = self.env['stock.location'].search([('id', '=', 34)])
        stoc = self.env['stock.picking.type'].search([('warehouse_id.name', '=', comp.name), ('name', '=', "Delivery Orders")])
        prod = self.move_lines
        vals_list = []
        unit_id = self.env['product.uom'].search([('id', '=', 1)])

        pack_operation = self.pack_operation_product_ids
        company = self.company_id
        print'===================', company.name

        locat = company.name + "/Stock"
        comp_id = self.env['res.company'].search([('id', '=', 1)])
#        ab = self.search([('company_id.name', '=', 'My Company')])
#        if ab:
#            sto_id = self.env['stock.location'].search([('id', '=', 15)])
#        else:
        sto_id = self.env['stock.location'].search([('company_id.name', '=', company.name), ('name', '=', 'Stock')])
        print'=============', sto_id

        for my in prod:
            pro = my.product_id.id
            uom_qty = my.product_uom_qty    

            val_lines = (0, 0, {
                         'product_id': pro, 
                         'name':pro, 
                         'product_uom_qty':uom_qty,
                         'product_uom':unit_id.id
                         })                      
            vals_list.append(val_lines)

        vls = {
        'partner_id': partner.id,
        'location_id': sto_id.id,
        'picking_type_id': stoc.id,
        'location_dest_id': soce.id,
        'origin': self.name,
        'move_lines':vals_list,
	'company_check' : True,
	'customer_check' : True,
        }
        stock_picking_obj = self.env['stock.picking']
        stock_picking_order = stock_picking_obj.create(vls)
        print "====stock_picking_order=========", stock_picking_order
        
        if self._context.get('open_invoices', False):
            return self.action_view_send_to_company(stock_picking_order)
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def action_view_send_to_company(self, stock_picking_order):
       
        stock_picking_order_ids = stock_picking_order
        print "========sale_order_idskk===========", stock_picking_order_ids
        
        print "========sale_order_idskk===========", stock_picking_order_ids.ids
        print "========sale_order_idskk===========", stock_picking_order_ids.ids
        
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('service_logic.action_stock_picking_company_form')
        list_view_id = imd.xmlid_to_res_id('stock.view_picking_tree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form'], [list_view_id, 'tree']], 
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        if stock_picking_order_ids:
            result['res_id'] = stock_picking_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

class hr_employee(models.Model):
    _inherit="hr.employee"
   
     
    @api.model
    def create(self,  vals):
	if vals['work_email'] == False:
            raise UserError(_('Enter the Email Address.'))
                
        if vals.get('work_email'):
            exis_data_id = self.search( [('work_email','=', vals['work_email'])])
            if exis_data_id:
                raise UserError(_('This Email Already Exists.'))
        return super(hr_employee ,self).create( vals)
    
    @api.multi
    def write(self,  vals):        
        if vals.get('work_email'):
            exis_data_id = self.search( [('work_email','=', vals['work_email'])])
            if exis_data_id:
                raise UserError(_('This Email Already Exists.'))
        return super(hr_employee ,self).write(vals)
