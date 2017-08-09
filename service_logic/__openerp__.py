{
    'name': 'Service.',
    'version': '1.1',
    'author': 'Logicious',
    'category': 'Sale and Accounting',
    'depends': ['sale', 'account','hr','base','purchase','mail','mro','inter_company_rules'],
    'description': """

========================================================================

    """,
    'data': [
            'res_partner_view.xml',
            'product_view.xml',
            'layouts.xml',
            'job_sheet_customer.xml',
            'delivery_challan.xml',
            'report.xml',
            'service_center.xml',
            'security/work_order.xml',
            'security/ir.model.access.csv',
            'work_order_sequence.xml',
#            'sale_workflow.xml',
],
    'installable': True,
    'auto_install': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
