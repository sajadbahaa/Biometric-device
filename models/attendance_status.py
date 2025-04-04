from enum import Enum

class Status(Enum):
    not_register = 1,
    new_check_in  =2
    update_check_out = 3
    complete_process =4
    already_check_in = 5
    prevent = 6

