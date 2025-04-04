from odoo import models, fields,api

class Fingerprint(models.Model):
    _name = 'finger_print_device'  # Name of the model
    _description = 'Finger print Device'  # Description of the model
    # Fields for the device name and serial number
    name = fields.Char(string="Finger Print")

