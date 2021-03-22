#!/usr/bin/python3

import gpiozero
import time
#import signal # no longer needed since loop for alarm
import judsound_player
import judsound_clock

class Box:
    """Define class which handle the physical box

    Keyword arguments:
    gpio_push_buttons -- an array of integers specifying the GPIO pin numbers to which the push buttons are connected
    gpio_button_rotary_push -- an integer specifying the GPIO pin number to which the push button from the rotary encoder is connected
    gpio_button_rotary_CLK -- an integer specifying the GPIO pin number to which the CLK output from the rotary encoder is connected
    gpio_button_rotary_DT -- an integer specifying the GPIO pin number to which the DT output from the rotary encoder is connected
    path_music_sound -- a string specifying the path to the directory where the audio files for the playlist are stored
    path_system_sound -- a string specifying the path to the directory where the audio files for clock and system sounds are stored
    file_to_alarms -- a string specifying the file (including its paths) where alarms are written and read
    possible_modes -- an array of strings specifying the possible mode for the player (default = ["player_night"])
    vol_ini -- an integer specifying the baseline volume (default = 30)
    vol_step -- an integer specifying by how much the volume changes when the rotary encoder clicks once (default = 1)
    vol_max -- an integer specifying the maximum volume allowed (to protect the speaker; default = 100)
    vol_startup -- an integer specifying the volume of the startup announcement (default = 50)
    vol_alarm -- an integer specifying the volume of the alarm (default = 50)
    hold_time -- an integer specifying the duration (in seconds) for which the press of a push button triggers a holding behaviour (default = 1) 
    vol_diff_hours -- an integer specifying how much more than the baseline volume to speak the hours (default = 3)
    pause_h_m -- a float specifying the time in seconds between the reading of the hours and that of the minutes (default = 0.7)
    pause_0m_m -- a float specifying the time in seconds between the reading of the 0 minute and the single digit minutes (default = 0.4)
    tracks_system -- a dictionary for system sounds other than hours and minutes
    """

    def __init__(self,
                 gpio_push_buttons, gpio_button_rotary_push, gpio_button_rotary_CLK, gpio_button_rotary_DT,
                 path_music_sound, path_system_sound, file_to_alarms,
                 possible_modes = ["player_night", "alarm"],
                 vol_ini = 30, vol_step = 1, vol_max = 100, vol_startup = 50, vol_alarm = 50,
                 hold_time = 1,
                 vol_diff_hours = 3, pause_h_m = 0.5, pause_0m_m = 0.4,
                 tracks_system = {
                    "start": None,
                    "alarm": None,
                    "alarm_validation": None,
                    "player_night": None,
                    "alarm_preset_at": None,
                    "alarm_set_at": None,
                    "alarm_not_set": None,
                    "alarm_validation3": None,
                    "alarms_list": None,
                    "alarms_deleted": None}):
        "Initialize the box"
        self.mode_list = possible_modes
        self.mode_current = possible_modes[0]
        
        for m in range(60):
            key = f'{m:02d}'
            tracks_system[key] = key + '.mp3' # add minutes/hours to dictionary
        print("loaded dictionary for system sounds:")
        print(tracks_system)
        
        self.player_system = judsound_player.Player(path_music=path_system_sound, tracks_dictionary=tracks_system)
        self.player_system.play_sound(track_name="start", vol=vol_startup)
        self.player_music = judsound_player.Player(path_music=path_music_sound)
        self.volume_current = vol_ini
        self.volume_step = vol_step
        self.volume_max = vol_max
        self.clock = judsound_clock.Clock(player_system=self.player_system,
                                          file_to_alarms=file_to_alarms,
                                          vol_diff_hours=vol_diff_hours,
                                          pause_h_m=pause_h_m, pause_0m_m=pause_0m_m)
        
        # setting the mapping for all physical inputs
        gpiozero.Button.was_held = False
        self.push_buttons = [gpiozero.Button(btn) for btn in gpio_push_buttons]
        self.button_rotary_push = gpiozero.Button(gpio_button_rotary_push)
        self.button_rotary_CLK = gpiozero.Button(gpio_button_rotary_CLK)
        self.button_rotary_DT = gpiozero.Button(gpio_button_rotary_DT)
    
        # adjust settings for the rotary encoder
        self.button_rotary_push.when_pressed = self.push_mode_button
        self.button_rotary_CLK.when_pressed = self.change_volume

        # adjust settings for the push buttons
        self.hold_time = hold_time
        for btn_index, btn in enumerate(self.push_buttons):
            btn.when_pressed = lambda i = btn_index: self.push_top_button(button_index=i) 
            # note: i = btn_index is required for lambda to work using the right scope (specific to using for loops)
            # (i.e. don't pass argument(s) directly to push_top_button call)

        # alarm
        while(True):
            self.clock.ring_alarm(vol=vol_alarm)
            time.sleep(60)
        
        # wait until user action
        #signal.pause() # no longer needed since loop for alarm

    def push_top_button(self, button_index):
        "Decide what to do when a push button is pressed"

        btn = self.push_buttons[button_index]
        if self.mode_current == "player_night":
            while btn.is_pressed:
                if btn.active_time > self.hold_time:
                    print(f"button {button_index} was held")
                    self.player_music.stop()
                    return
            print(f"button {button_index} was pressed")
            self.player_music.play_music(track_index=button_index, vol=self.volume_current)

        elif self.mode_current == "alarm":
            while btn.is_pressed:
                if btn.active_time > self.hold_time:
                    if self.clock.check_unregistered_alarm(vol=self.volume_current):
                        self.change_mode(mode="alarm_validation")
                    else:
                        self.change_mode(mode="alarm")
                    return
            self.clock.alarm[button_index] = (self.clock.alarm[button_index] + 1) % [3, 10, 6, 10][button_index]
            # TODO: constrain max to 23:59, not 29:59
            print(f"alarm value updated to {self.clock.alarm}")
        elif self.mode_current == "alarm_validation":
            while btn.is_pressed:
                if btn.active_time > self.hold_time:
                    # register and quit
                    self.clock.register_alarm(vol=self.volume_current)
                    self.change_mode(mode="player_night")
                    return
            # cancel and return to player
            if button_index == 0:
                self.clock.reset_soft(vol=self.volume_current)
                self.change_mode(mode="player_night")
            # return to preset
            if button_index == 1:
                self.clock.reset_soft(vol=self.volume_current)
                self.change_mode(mode="alarm")
            # list all alarms
            if button_index == 2:
                self.clock.list_alarms(vol=self.volume_current)
            # cancel all alarms
            if button_index == 3:
                self.clock.reset_hard(vol=self.volume_current)
                self.change_mode(mode="player_night")

    def change_mode(self, mode):
        if mode == "alarm":
            self.clock.reset_soft(vol=0)
        elif mode not in ["alarm_validation", "player_night"]:
            raise ValueError('Unknown mode: '+mode)
        self.player_music.player.stop()
        self.mode_current = mode
        self.player_system.play_sound(track_name=mode,
                                      vol=self.volume_current,
                                      wait_till_completion=False)
        print(self.mode_current)

    def push_mode_button(self):
        "Change the mode to the next one"
        while self.button_rotary_push.is_pressed:
            if self.button_rotary_push.active_time > self.hold_time:
                print(f"button mode was active for more than {self.hold_time} sec")
                if self.mode_current == "alarm_validation": # as this is a submode, it has no index
                    self.mode_current = "alarm"
                i = self.mode_list.index(self.mode_current)
                i = i + 1 if i + 1 < len(self.mode_list) else 0
                self.change_mode(mode=self.mode_list[i])
                return
        self.clock.speak(vol = self.volume_current)

    def change_volume(self):
        "Change the volume of all players"
        #print(f"CLK = {self.button_rotary_CLK.value} DT = {self.button_rotary_DT.value}")
        add_volume = self.volume_step if self.button_rotary_DT.value == 0 else - self.volume_step
        self.volume_current = max(min(self.volume_current+add_volume, self.volume_max), 0)
        self.player_music.update_volume(vol=self.volume_current)
        self.player_system.update_volume(vol=self.volume_current, verbose=False)
