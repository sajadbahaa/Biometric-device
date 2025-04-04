from odoo import models, fields, api,_
from odoo.exceptions import UserError
import  requests
import base64
import json
import pandas as pd
from .EndPointApi import APIEndpoints

class Configuration(models.Model):
    _name = 'config_device'  # Name of the model
    _description = 'Device Configuration'  # Description of the model

    # Fields for the device name and serial number
    name = fields.Char(string="Device Name", required=True)
    serial_number = fields.Char(string="Serial Number",default="ZYRL12098271" ,required=True)
    api_url=  fields.Char(string="Api url",default="http://172.18.18.85:8080/api/")
    # employee_id = fields.Many2many('inherit_emp', string="Employee",
    #                                ondelete='cascade', store=True)
    device_status = fields.Boolean('status',default=True)

    @api.constrains('name', 'serial_number')
    def _check_unique_device(self):
        for record in self:
            existing_device = self.env['config_device'].search([
                '|',  # OR condition
                ('name', '=', record.name),
                ('serial_number', '=', record.serial_number),
                ('id', '!=', record.id)  # Ignore current record in case of update
            ])
            if existing_device:
                raise UserError("A device with the same name or serial number already exists!")



    def is_a_master(self):
        if self.device_status:
            return True
        else:
            raise UserError(_("you can not choose device not master"))




