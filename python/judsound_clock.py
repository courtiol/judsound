#!/usr/bin/python3

import time

class Clock:
    "Define the class which handles the alarm-clock"

    def __init__(self, player_system, file_to_alarms, vol_diff_hours = 1, night_day_h = 8, day_night_h = 20):
       """Initialize the clock

       Keyword arguments:
        player_system -- an object of class Player
        file_to_alarms -- a string specifying the file (including its paths) where alarms are written and read
        vol_diff_hours -- an integer specifying how much more than the baseline volume to speak the hours (default = 3)
        night_day_h -- an integer specifying at what time the day period starts
        day_night_h -- an integer specifying at what time the night period starts
       """

       self.extra_volume_hours = vol_diff_hours
       self.player_system = player_system
       self.file_to_alarms = file_to_alarms
       self.alarm = [0, 0, 0, 0] # a given alarm being set
       self.alarms = [] # the list of alarms
       self.night_day_h = night_day_h
       self.day_night_h = day_night_h

    @staticmethod
    def time():
        hours = time.strftime("%H", time.localtime())
        minutes = time.strftime("%M", time.localtime())
        return [hours, minutes]

    def is_day(self):
        "Figure out if it is currently the day or the night"
        time = self.time()
        if int(time[0]) >=  self.night_day_h and int(time[0]) < self.day_night_h:
            return True
        return False

    @staticmethod
    def convert_hhmm_to_hm(time):
        return [f"{time[0]}{time[1]}", f"{time[2]}{time[3]}"]

    def read_alarms(self):
        "Read the alarms from the text file"
        with open(self.file_to_alarms, "r") as file:
            self.alarms = []
            for line in file:
                digits = [int(digit) for digit in line.strip()]
                assert len(digits) == 4, f"Size mismatch: { len(digits) } characters instead of 4"
                self.alarms.append(digits)

    def write_alarms(self):
        "Write the alarms into the text file"
        self.alarms.sort() # sort the alarms
        with open(self.file_to_alarms, "w") as file:
            for alarm in self.alarms:
                file.writelines(self.convert_hhmm_to_hm(time=alarm))
                file.write("\n")
            file.truncate()

    def delete_alarms(self):
        "Delete all alarms from the text file"
        with open(self.file_to_alarms, "w"):
            pass # does nothing but erase content of file since in write mode

    def speak(self, vol, time_to_read = None):
        "Tell either current time or alarm time"
        if time_to_read is None:
            time_to_read = self.time()
            prefix = "tell current time"
        else:
            time_to_read = self.convert_hhmm_to_hm(time=time_to_read)
            prefix = "tell alarm pre-set"
        hours = time_to_read[0]
        minutes = time_to_read[1]

        print(f"{prefix} ({hours}:{minutes})")
        
        self.player_system.play_sound(track_name=hours, vol=vol+self.extra_volume_hours)
        if minutes < "10":
            self.player_system.play_sound(track_name="00", vol=vol)
        self.player_system.play_sound(track_name=minutes, vol=vol)

    def reset_soft(self, vol):
        "Reset alarm currently being prepared"
        self.alarm = [0, 0, 0, 0]
        if vol > 0:
            self.player_system.play_sound(track_name="alarm_not_set", vol=vol)

    def reset_hard(self, vol):
        "Reset all alarms"
        self.reset_soft(vol = 0)
        self.delete_alarms()
        self.player_system.play_sound(track_name="alarms_deleted", vol=vol)

    def check_unregistered_alarm(self, vol):
        "Check if the alarm has been preset properly (return False if not)"
        if self.alarm[0] == 2 and self.alarm[1] > 3: # handle error in input
            self.player_system.play_sound(track_name="alarm_not_set", vol=vol)
            return False
        self.player_system.play_sound(track_name="alarm_preset_at", vol=vol)
        self.speak(vol=vol, time_to_read=self.alarm)
        return True

    def register_alarm(self, vol):
        print("saving alarm to file")
        if self.alarm not in self.alarms: # prevent duplicates
            self.alarms.append(self.alarm) # add alarm to in-memory list
        self.write_alarms() # update text file
        self.player_system.play_sound(track_name="alarm_set", vol=vol)

    def list_alarms(self, vol, update = True):
        if update:
            self.read_alarms()
        if self.alarms:
            self.player_system.play_sound(track_name="alarms_list", vol=vol)
            for alarm in self.alarms:
                self.speak(vol = vol, time_to_read=alarm)
        self.player_system.play_sound(track_name="alarm_validation", vol=vol,
                                      wait_till_completion = False)
        # TODO implement sound for else

    def ring_alarm(self, vol, update = True):
        if update:
            self.read_alarms()
        now = self.time()
        #print(f"checking if an alarm is set for current time ({now[0]}:{now[1]})")
        new_alarms = []
        for alarm in self.alarms:
            target = self.convert_hhmm_to_hm(alarm)
            if target == now:
                print("ALARM RINGING!")
                self.player_system.play_sound(track_name="start", vol=vol)
            else:
                new_alarms.append(alarm) # only keep alarms that did not trigger (used alarms are discarded)
        self.alarms = new_alarms # update in memory alarms
        self.write_alarms() # update text file
