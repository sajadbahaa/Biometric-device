from email.policy import default

import logging

from datetime import datetime

from odoo import models, fields,api,_
from .EndPointApi import APIEndpoints
from odoo.exceptions import UserError
from .mode import Modes
import aiohttp
import asyncio
import base64
import  requests
import time
import threading
import concurrent.futures

_logger = logging.getLogger(__name__)
class InheritEmp(models.Model):
    _name = 'inherit_emp'
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'
    employee_id = fields.Many2one('hr.employee', string="Employee",ondelete='cascade',store=True)
    finger_print_id = fields.Integer(related='employee_id.finger_print_id', string="Finger Print ID",store=True,readonly=True,)
    finger_data = fields.Text(related='employee_id.finger_data',store=True,readonly=True)
    face_data = fields.Text(related='employee_id.face_data',store=True,readonly=True)
    password = fields.Char(related='employee_id.password',store=True,readonly=True)
    card_id = fields.Char(related='employee_id.card_id',store=True,readonly=True)
    image = fields.Binary(related='employee_id.image_1920',store=True,readonly=True)
    # devices = fields.One2one('config_device',domain=[('device_status', '=', True)])
    #
    is_register = fields.Boolean(store=True,default= False)

    device_id = fields.Many2one('config_device', readonly=False, string="Device",domain=[('device_status', '=', True)],store=True)
    many_devices = fields.Many2many('config_device', string="Other Devices :",
                                   ondelete='cascade', store=True)


    def _validation(self,backupnum):
        if backupnum==50 and self.image:
            return self.face_data
        elif backupnum ==0 and self.finger_data:
            return  self.finger_data
        else:
            return "FP_DATA_BASE64"
    def get_all_log(self,backupnum,serial_number,api_url,record_value):
        emp_info = []
        employee_data = {
            'enrollid': self.finger_print_id,
            'name': self.employee_id.name,
            'backupnum': backupnum,
            'admin': 0,
            'record': record_value

            #  "FP_DATA_BASE64" Assuming you have the fingerprint data in some format
            }
        emp_info.append(employee_data)

        if self._send_to_device(serial_number, api_url, employee_data)!=400:
            emp_info = []
            return True
        else:
            emp_info = []
            return False

    def _send_to_device(self,serial_number,api_url, employee_data_batch):
        try:
            payload = {
                "sn": serial_number,
                "userInfo": employee_data_batch  # Sending a list of employee data for bulk registration
            }


            response = requests.post(f"{api_url}{APIEndpoints.SET_USER_INFO.value}", json=payload)
            log_message = {
                "status_code": response.status_code,
                "body": response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
            }

            _logger.info(log_message)  # ✅ Logs to the Odoo server logs


            if response.status_code == 200:
                _logger.info("Response Status Code: %s", response.status_code)
                _logger.info("Response Content: %s", response.text)
                print(response.content)
                return log_message

            else:
                return 400
        except Exception as e:
            print(f"Unexpected Error: {e}")  # Debugging output
            raise UserError(_("An unexpected error occurred: %s") % str(e))

    @api.model
    def create(self, vals):
        # Check if a device is available with device_status=True
        device = self.env['config_device'].search([('device_status', '=', True)], limit=1)
        if device:
            vals['device_id'] = device.id  # Automatically set device_id if a device is found
        return super(InheritEmp, self).create(vals)

    @api.onchange('device_id')
    def _onchange_device_id(self):
        if self.device_id:
            # Update all employees with this device_id to the new one
            self.env['inherit_emp'].search([('device_id', '=', self.device_id.id)]).write(
                {'device_id': self.device_id.id})

    def device_add_finger(self):
        mode = self._validation_employee(0,self.device_id.serial_number)
        print(mode)
        if mode is None:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'wrong!',
                    'message': 'this an employee not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'danger',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }
        messages = []  # List to store messages for all devices

        for d in self.many_devices:
            if self.get_all_log(0, d.serial_number, d.api_url, self._validation(0)):
                print(d.name)
                print(d.serial_number)
                print(d.api_url)
                print("===============")
                messages.append({
                    'title': 'Success!',
                    'message': f'finger data added successfully on {d.name} ({d.serial_number})!',
                    'type': 'success'
                })
            else:
                messages.append({
                    'title': 'Failed!',
                    'message': f'Error occurred on {d.name} ({d.serial_number})!',
                    'type': 'danger'
                })

        # If multiple notifications are needed, you may need a custom frontend approach
        if messages:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Operation Complete!',
                    'message': '\n'.join([msg['message'] for msg in messages]),  # Join all messages
                    'sticky': False,
                    'type': 'success' if all(msg['type'] == 'success' for msg in messages) else 'warning',
                }
            }
        else:
            raise UserError("choose device")

    async def add_employee_to_device_async(self, backupnum):
        name_method = APIEndpoints.Add_User_info.value
        _logger.info(f"Using API Method: {name_method}")

        payload = {
            "sn": self.device_id.serial_number,
            "userInfo": {
                'enrollid': self.finger_print_id,
                'name': self.employee_id.name,
                'backupnum': backupnum,
                'admin': 0, }}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.device_id.api_url}{name_method}", json=payload,
                                        timeout=aiohttp.ClientTimeout(total=50)) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        record_data = response_json.get('data', {}).get('record', '')

                        if backupnum == 0:
                            self._update(False, record_data)  # Update fingerprint data
                        else:
                            self._update(record_data, False)  # Update face data

                        _logger.info(f"Record data updated: {record_data}")
                        self.check_is_register()
                    else:
                        error_msg = await response.text()
                        raise UserError(_("Failed to register employee on the device! Response: %s") % error_msg)


        except Exception as e:
            _logger.error(f"Unexpected Error: {e}")
            raise UserError(_("An unexpected error occurred: %s") % str(e))

    async def get_all_log_v2(self, backupnum, serial_number, api_url, record_value):
        emp_info = []
        employee_data = {
            'enrollid': self.finger_print_id,
            'name': self.employee_id.name,
            'backupnum': backupnum,
            'admin': 0,
            'record': record_value
        }
        emp_info.append(employee_data)
        status_code = await self._send_to_device_async(serial_number, api_url, employee_data)
        if status_code != 400:
            emp_info = []
            return True
        else:
            emp_info = []
            return False

    async def _send_to_device_async(self, serial_number, api_url, employee_data_batch):
        payload = {
            "sn": serial_number,
            "userInfo": employee_data_batch}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{api_url}{APIEndpoints.SET_USER_INFO.value}", json=payload,
                                        timeout=10) as response:
                    status_code = response.status
                    body = await response.text()
                    log_message = {
                        "status_code": status_code,
                        "body": body}
                    _logger.info(log_message)

                    # ✅ Logs to Odoo server logs
                    if status_code == 200:
                        _logger.info("Response Status Code: %s", status_code)
                        _logger.info("Response Content: %s", body)
                        return status_code

                    else:
                        return 400
            except Exception as e:
                _logger.error(f"Unexpected Error: {e}")
                raise UserError(_("An unexpected error occurred: %s") % str(e))

    def device_add_face(self):
        mode = self._validation_employee(50,self.device_id.serial_number)
        print(mode)
        if mode is None:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'wrong!',
                    'message': 'this an employee not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'danger',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }
        messages = []
        for d in self.many_devices:

            if self.get_all_log(50, d.serial_number, d.api_url, self._validation(50)):
                print(d.name)
                print(d.serial_number)
                print(d.api_url)
                print("===============")
                messages.append({
                    'title': 'Success!',
                    'message': f'face data added successfully on {d.name} ({d.serial_number})!',
                    'type': 'success'
                })
            else:
                messages.append({
                    'title': 'Failed!',
                    'message': f'Error occurred on {d.name} ({d.serial_number})!',
                    'type': 'danger'
                })

            # If multiple notifications are needed, you may need a custom frontend approach
        if messages:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Operation Complete!',
                    'message': '\n'.join([msg['message'] for msg in messages]),  # Join all messages
                    'sticky': False,
                    'type': 'success' if all(msg['type'] == 'success' for msg in messages) else 'warning',
                }
            }
        else:
            raise UserError("choose device")





    def device_add_card(self):
        for d in self.many_devices:
            print(d.name)
            print(d.serial_number)
            print("add card data")
            print("===============")

    def device_add_password(self):
        for d in self.many_devices:
            print(d.name)
            print(d.serial_number)
            print("add password data")
            print("===============")











    @api.onchange('finger_data')
    def _onchange_image(self):
        self.employee_id.finger_data = self.finger_data
            # Update the image_1920 field in the related hr.employee record




    def check_add_one_time_face_data(self):
        return False if self.face_data else True


    def check_adding_one_time_finger_print(self):
        return False if self.finger_data else True

    def get_object_shift(self, day_today):
        return self.env['resource.calendar.attendance'].search([
            ('calendar_id', '=', self.employee_id.resource_calendar_id.id),
            ('dayofweek', '=', day_today)
        ], limit=1)



    def Finger_Print(self):
        if self.device_id.is_a_master():
            self.add_employee_to_device(0)




    def Face_Data(self):
        if self.device_id.is_a_master():
            self.add_employee_to_device(50)
            print("added successfully")


        # if self.check_add_one_time_face_data():
        #     self.add_employee_to_device(50)
        #     print("added successfully")
        #
        # else:
        #     print("you are already have it")

    def Send(self):
        print("Send")

    def check_is_register(self):
        if not self.is_register:
            self.write({'is_register': True})
            return True
        else:
            return False

    def _update(self,face_data,finger_data):
        if face_data:
            self.employee_id.write({'face_data': face_data})
            self.employee_id.write({'image_1920': face_data})
            return True
        elif finger_data:
            self.employee_id.write({'finger_data': finger_data})
            return True
        else:
            return False
    # ad
    def add_employee_to_device(self,backupnum):
        # APIEndpoints.SET_USER_INFO
        name_method = APIEndpoints.Add_User_info.value

        print(name_method)

        if backupnum ==0:

            payload = {
                "sn": self.device_id.serial_number,
                "userInfo": {
                    'enrollid': self.finger_print_id,
                    'name': self.employee_id.name,
                    'backupnum': backupnum,
                    'admin': 0,
                    # 'record': "FP_DATA_BASE64"
                }
            }
            try:
                response = requests.post(f"{self.device_id.api_url}{name_method}", json=payload, timeout=(20, 60))
                if response.status_code == 200:
                    response_json = response.json()  # Convert the response content to JSON

                    finger_data = response_json.get('data', {}).get('record', '')  # Use the safe get method

                    # Update the finger_data field with the value of 'record'
                    # self.employee_id.write({'finger_data': finger_data})
                    self._update(False,finger_data)

                    print(f"Fingerprint data updated: {finger_data}")

                    # Extract the value of 'record' from the response
                    print(response.content)
                    self.check_is_register()
                    # self.write({'is_register': True})

                else:
                    raise UserError(_("Failed to register employee on the device! Response: %s") % response.content)
            except Exception as e:
                print(f"Unexpected Error: {e}")  # Debugging output
                raise UserError(_("An unexpected error occurred: %s") % str(e))
        else:
            payload = {
                "sn": self.device_id.serial_number,
                "userInfo": {
                    'enrollid': self.finger_print_id,
                    'name': self.employee_id.name,
                    'backupnum': backupnum,
                    'admin': 0,
                    # 'record': "FP_DATA_BASE64"
                }
            }
            try:
                response = requests.post(f"{self.device_id.api_url}{name_method}", json=payload, timeout=(10, 50))
                if response.status_code == 200:
                    response_json = response.json()  # Convert the response content to JSON

                    face_data = response_json.get('data', {}).get('record', '')  # Use the safe get method

                    self._update(face_data,False)

                    print(f"Fingerprint data updated: {face_data}")

                    # Extract the value of 'record' from the response
                    print(response.content)
                    self.check_is_register()

                    # self.write({'is_register': True})

                else:
                    raise UserError(_("Failed to register employee on the device! Response: %s") % response.content)
            except Exception as e:
                print(f"Unexpected Error: {e}")  # Debugging output
                raise UserError(_("An unexpected error occurred: %s") % str(e))

    def _message_not_found(self):
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'wrong!',
                    'message': 'this an employee not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'danger',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }
    def delete_emp_from_device(self):
        messages=[]
        for device in self.many_devices:
            print(device.serial_number)
            self.delete_finger_data(0,device.serial_number)
            self.delete_face_data(50,device.serial_number)
            finger_response = self.delete_finger_data(0, device.serial_number)
            if finger_response and 'params' in finger_response:
                messages.append(finger_response['params']['message'])

            # Collect messages from delete_face_data
            face_response = self.delete_face_data(50, device.serial_number)
            if face_response and 'params' in face_response:
                messages.append(face_response['params']['message'])

            # Create a combined message
        final_message = "deleted successfully" if messages else "No actions were performed."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Operation Completed!',
                'message': final_message,
                'sticky': False,
                'type': 'success',
            }
        }



    def delete_finger_data(self,backup=0,sn=''):
        mode = self._validation_employee(0,sn if sn!='' else self.device_id.serial_number)
        print(mode)
        if mode is None:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'wrong!',
                    'message': 'this an employee not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'danger',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }

        if mode:

            self._delete_employee_to_device(backup,sn if sn!='' else self.device_id.serial_number)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': 'finger data deleted successfully!',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'success',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }

        elif not mode:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error!',
                    'message': 'finger data not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'warning',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }

    def _validation_employee(self,backupnum,sn):
        data = self._check_employee_exist_in_device(backupnum,sn)
        if data ==Modes.finger_or_face_data_exist.value:
            return True
        elif data==Modes.without_finger_face.value:
            return False
        else:
            return None


    def delete_face_data(self,backup=50,sn=''):
        mode = self._validation_employee(backup,sn if sn!='' else self.device_id.serial_number)
        print(mode)
        if mode is None:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'wrong!',
                    'message': 'this an employee not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'danger',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }


        if mode:
            self._delete_employee_to_device(backup,sn if sn!='' else self.device_id.serial_number)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': 'face data deleted successfully!',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'success',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }
        elif not mode:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error!',
                    'message': 'face data not found',
                    'sticky': False,  # Set True if you want it to stay longer
                    'type': 'warning',  # Can be 'success', 'warning', 'danger', 'info'
                }
            }



        #     if self._delete_employee_to_device(50):
        #         return {
        #             'type': 'ir.actions.client',
        #             'tag': 'display_notification',
        #             'params': {
        #                 'title': 'Success!',
        #                 'message': 'face data deleted successfully!',
        #                 'sticky': False,  # Set True if you want it to stay longer
        #                 'type': 'success',  # Can be 'success', 'warning', 'danger', 'info'
        #             }
        #         }
        # elif  not self._validation_employee(50):
        #     raise  UserError("you dont have face data")
        # else:
        #     raise UserError("this an employee does exist in device")



    def _delete_employee_to_device(self, backup_num,sn):

        # APIEndpoints.SET_USER_INFO
        name_method = APIEndpoints.Delete_User_info.value
        print(name_method)
        # self.device_id.serial_number
        payload = {
            "sn": sn,
            'enrollid': self.finger_print_id,
            'backupnum': backup_num,
            # 'record': "FP_DATA_BASE64"
        }

        try:
            response = requests.post(f"{self.device_id.api_url}{name_method}", json=payload, timeout=(10, 50))
            if response.status_code == 200:
                print("deleted successfully")
                return True
            else:
                raise UserError(_("Failed to delete employee on the device! Response: %s") % response.content)
        except Exception as e:
                print(f"Unexpected Error: {e}")  # Debugging output
                raise UserError(_("An unexpected error occurred: %s") % str(e))

    def _check_employee_exist_in_device(self, backup_num,sn):
        name_method = APIEndpoints.Get_user_info.value  # API endpoint
        print(name_method)
        # self.device_id.serial_number
        payload = {
            "sn": sn,
            "enrollid": self.finger_print_id,
            "backupnum": backup_num,
        }

        try:
            response = requests.post(f"{self.device_id.api_url}{name_method}", json=payload, timeout=(10, 50))

            if response.status_code == 200:
                data = response.json()  # Convert response to JSON

                # Extract name and result
                employee_name = data.get("data", {}).get("name", "Unknown")
                result = data.get("data", {}).get("result", False)
                if employee_name!="Unknown" and result:
                    print("data exist")
                    print(f"Employee Name: {employee_name}, Exists: {result}")
                    return Modes.finger_or_face_data_exist.value
                elif employee_name!="Unknown":
                    return Modes.without_finger_face.value
                else:
                    return Modes.no_data.value
            else:
                print(f"Failed to check employee: {response.content}")
                return None  # Or handle differently if needed

        except requests.exceptions.Timeout:
            print("Request timed out!")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        except Exception as e:
            print(f"Unexpected Error: {e}")

        return None









class Employee(models.Model):
    _inherit = 'hr.employee'# Name of the model
    finger_print_id = fields.Integer(readonly=False,default=0)
    # device_id = fields.Many2one('config_device',required=False)
    finger_data = fields.Text()
    face_data = fields.Text()
    password = fields.Char()
    card_id = fields.Char(string="Card ID")

    # @api.model
    #     def create(self, values):
    #         # Check if 'finger_print_id' is missing or False (0, None, or empty)
    #         if not values.get('finger_print_id'):
    #             # Check if any employee has no fingerprint ID (is False)
    #             has_empty_fingerprint = self.search([('finger_print_id', '=', False)], limit=1)
    #
    #             if has_empty_fingerprint:
    #                 values['finger_print_id'] = 1  # Assign 1 if any record has no fingerprint
    #             else:
    #                 # Otherwise, find the max existing fingerprint ID and increment
    #                 last_employee = self.search([('finger_print_id', '>', 0)], order="finger_print_id desc", limit=1)
    #                 values['finger_print_id'] = (last_employee.finger_print_id + 1) if last_employee else 1
    #
    #         # Create the employee record
    #         new_employee = super(Employee, self).create(values)
    #
    #         # Create a corresponding record in 'inherit_emp'
    #         self.env['inherit_emp'].create({
    #             'employee_id': new_employee.id,
    #         })
    #
    #         return new_employee

    @api.model
    def create(self, values):
        # If 'finger_print_id' is missing or explicitly set to 0, treat it as empty
        if not values.get('finger_print_id') or values['finger_print_id'] == 0:
            # Check if any employee has no fingerprint ID (False or 0)
            has_empty_fingerprint = self.search(['|', ('finger_print_id', '=', False), ('finger_print_id', '=', 0)],
                                                limit=1)

            if has_empty_fingerprint:
                values['finger_print_id'] = 1  # Assign 1 if a record has no fingerprint
            else:
                # Otherwise, find the max existing fingerprint ID and increment
                last_employee = self.search([('finger_print_id', '>', 0)], order="finger_print_id desc", limit=1)
                values['finger_print_id'] = (last_employee.finger_print_id + 1) if last_employee else 1

        # Create the employee record
        new_employee = super(Employee, self).create(values)

        # Create a corresponding record in 'inherit_emp'
        self.env['inherit_emp'].create({
            'employee_id': new_employee.id,
        })

        return new_employee
