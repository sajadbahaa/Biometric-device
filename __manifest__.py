# -*- coding: utf-8 -*-
{
    'name': "AI Biometric Device",

    'summary': """
       This module enables seamless integration between Odoo and AI-powered biometric devices.""",

    'description': """
        The AI Biometric Device Connector Module provides a robust solution for integrating AI-driven biometric devices with Odoo.
         It facilitates real-time data synchronization,
         including user authentication, attendance tracking,
         and access control. This module enhances security,
         improves workforce management,
         and automates biometric data processing,
         ensuring a seamless user experience within the Odoo ecosystem.

        Key Features:
        - Supports fingerprint and facial recognition for attendance tracking.
        - Real-time synchronization with biometric devices.
        - Accurate time logging for employees.
        - Employee management through Odoo interface.
        - Device configuration and management directly from Odoo.

        This module is ideal for businesses looking to streamline their attendance tracking processes, ensuring data 
        accuracy and reducing the risk of time fraud. The system is user-friendly and can be easily customized to suit 
        the specific needs of your organization.
        
    """,

    'author': "Magic Quantum Technologies",
    'company':'Magic Quantum Technologies',
    # 'website': "https://www.yourcompany.com",
    'maintainer': 'Magic Quantum Technologies',
    'website': 'https://www.magic-quantum.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/hr_employee_form_inherie_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',],


}
# /home/mqt/odoo/odoo/odoo-custom-addons/ai_Finger_Print_module/assests