"""
Apparatus class

- Listens to the device in the same room for when to turn on/off
- Thats all
- E.g,  if the apparatus is a 'heater', it will turn on when the room's Device
        has been triggered and wants the room to heat up. This will cause the  
        rooms 'affected_stat' (temp in this case) to change by the 'change_amount'.

Valid 'change_type' : "set_to", "increase_by", "decrease_by"
"""

class Apparatus:
    def __init__(self, room_id, apparatus_type, affected_stat, change_type, change_amount):
        self.id = room_id + "@" + apparatus_type
        self.apparatus_type = apparatus_type
        self.affected_stat = affected_stat
        self.change_type = change_type
        self.change_amount = change_amount
        self.on = False

        # Todo, implement 'listen' functionality


    