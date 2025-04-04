from odoo import http
from odoo.http import request
import json
import pytz
from datetime import datetime

class FingerprintController(http.Controller):

    @http.route('/api/fingerprint_log', type='json', auth='public', methods=['POST'], csrf=False)
    def fingerprint_log(self):
        try:
            args = request.httprequest.data.decode()
            vals = json.loads(args)

            if vals and "record" in vals:
                sn_value = vals.get("sn")  # Device serial number
                records = vals["record"]

                # Create a list of attendance records to process in bulk
                attendance_log_data = []
                local_tz = pytz.timezone("Asia/Baghdad")

                for rec in records:
                    enroll_id = rec.get("enrollid")
                    time_value = rec.get("time")  # Received timestamp
                    event_value = rec.get("event")  # Event: 1=Check-in, 2=Check-out

                    # Convert Baghdad time to UTC
                    local_time = datetime.strptime(time_value, "%Y-%m-%d %H:%M:%S")
                    local_time = local_tz.localize(local_time)  # Apply Baghdad timezone
                    utc_time = local_time.astimezone(pytz.utc)  # Convert to UTC

                    attendance_log_data.append({
                        'enroll_id': enroll_id,
                        'sn_value': sn_value,
                        'utc_time': utc_time,
                        'event_value': event_value
                    })

                # Send all records in bulk to the model
                response = request.env["attendance_log"].sudo().create_attendance_logs(attendance_log_data)

                return request.make_json_response(response, status=200)

            return request.make_json_response({"status": "failed", "message": "No data received"}, status=400)

        except Exception as e:
            return request.make_json_response({"status": "error", "message": str(e)}, status=400)
