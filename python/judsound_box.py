#!/usr/bin/python3

import gpiozero
from gpiozero.tools import scaled
import time
import judsound_player
import judsound_clock

class Box:
    """Define class which handle the physical box

    Keyword arguments:
    gpio_push_buttons -- an array of integers specifying the GPIO pin numbers to which the push buttons are connected
    gpio_button_rotary_push -- an integer specifying the GPIO pin number to which the push button from the rotary encoder is connected
    gpio_button_rotary_CLK -- an integer specifying the GPIO pin number to which the CLK output from the rotary encoder is connected
    gpio_button_rotary_DT -- an integer specifying the GPIO pin number to which the DT output from the rotary encoder is connected
    gpio_button_rotary_max_steps -- an integer specifying the number of steps for the rotary encoder
    path_music_night -- a string specifying the path to the directory where the audio files for the night playlist are stored
    path_music_day -- a string specifying the path to the directory where the audio files for the day playlist are stored
    path_system_sound -- a string specifying the path to the directory where the audio files for clock and system sounds are stored
    file_to_alarms -- a string specifying the file (including its paths) where alarms are written and read
    possible_modes -- an array of strings specifying the possible mode for the player (default = ["player_night", "alarm", "player_day"])
    vol_min -- an integer specifying the minimum volume allowed
    vol_max -- an integer specifying the maximum volume allowed
    vol_music_day -- an integer specifying the baseline volume for the day player
    vol_music_night -- an integer specifying the baseline volume for the night player
    vol_system_day -- an integer specifying the volume for the clock and other system sounds during (true) day (not day player)
    vol_system_night -- an integer specifying the volume for the clock and other system sounds during (true) night (not night player)
    vol_startup_msg -- an integer specifying the volume of the startup message
    vol_alarm -- an integer specifying the volume of the alarm
    vol_diff_hours -- an integer specifying how much more than the baseline volume to speak the hours
    hold_time -- an integer specifying the duration (in seconds) for which the press of a push button triggers a holding behaviour
    night_day_h -- an integer specifying at what time the day period starts
    day_night_h -- an integer specifying at what time the night period starts
    tracks_system -- a dictionary for system sounds other than hours and minutes
    """

    def __init__(self,
                 gpio_push_buttons,
                 gpio_button_rotary_push,
                 gpio_button_rotary_CLK,
                 gpio_button_rotary_DT,
                 gpio_button_rotary_max_steps,
                 path_music_night,
                 path_music_day,
                 path_system_sound,
                 file_to_alarms,
                 possible_modes = ["player_night", "alarm", "player_day"],
                 vol_min = 10,
                 vol_max = 40,
                 vol_music_day = 25,
                 vol_music_night = 20,
                 vol_system_day = 30,
                 vol_system_night = 25,
                 vol_startup_msg = 30,
                 vol_alarm = 50,
                 vol_diff_hours = 1,
                 hold_time = 2,
                 night_day_h = 6,
                 day_night_h = 22,
                 tracks_system = {
                    "start": None,
                    "alarm": None,
                    "player_night": None,
                    "player_day": None,
                    "alarm_preset_at": None,
                    "alarm_set": None,
                    "alarm_not_set": None,
                    "alarm_setting": None,
                    "alarm_none": None,
                    "alarm_validation": None,
                    "alarms_list": None,
                    "alarms_deleted": None,
                    "volume": None}):
        "Initialize the box"

        # setting volumes
        self.volume_min = vol_min
        self.volume_max = vol_max
        self.volume_music_day = vol_music_day
        self.volume_music_night = vol_music_night
        self.volume_system_day = vol_system_day
        self.volume_system_night = vol_system_night

        # setting the mapping for all physical inputs
        gpiozero.Button.was_held = False

        self.push_buttons = [gpiozero.Button(btn, bounce_time = 0.1) for btn in gpio_push_buttons]

        self.button_rotary_push = gpiozero.Button(
            gpio_button_rotary_push,
            bounce_time = 0.1)

        self.button_rotary_turn = gpiozero.RotaryEncoder(
            gpio_button_rotary_CLK,
            gpio_button_rotary_DT,
            bounce_time = 0.1,
            max_steps = gpio_button_rotary_max_steps)
        
        self.max_steps = gpio_button_rotary_max_steps

        # adjust settings for the rotary encoder
        self.button_rotary_push.when_pressed = self.push_mode_button
        self.button_rotary_turn.when_rotated = self.change_volume

        # adjust settings for the push buttons
        self.hold_time = hold_time

        for btn_index, btn in enumerate(self.push_buttons):
            btn.when_pressed = lambda i = btn_index: self.push_top_button(button_index = i) 
            # note: i = btn_index is required for lambda to work using the right scope (specific to using for loops)
            # (i.e. don't pass argument(s) directly to push_top_button call)

        # filling dictionary for system sounds
        for m in range(60):
            key = f'{m:02d}'
            tracks_system[key] = key + '.mp3' # add minutes/hours to dictionary
        print("loaded dictionary for system sounds:")
        print(tracks_system)

        # creating players (volume is set to day, waiting for clock to be created)
        self.player_system = judsound_player.Player(
            path_music = path_system_sound,
            tracks_dictionary = tracks_system,
            vol = vol_system_day)

        self.player_music_day = judsound_player.Player(
            path_music = path_music_day,
            vol = vol_music_day)
        
        self.player_music_night = judsound_player.Player(
            path_music = path_music_night,
            vol = vol_music_day)

        # setting clock (must happened before creating players)
        self.clock = judsound_clock.Clock(
            player_system = self.player_system,
            file_to_alarms = file_to_alarms,
            night_day_h = night_day_h,
            day_night_h = day_night_h,
            vol_alarm = vol_alarm,
            vol_diff_hours = vol_diff_hours)

        # adjusting initial volume for players now that clock is available
        self.player_system.change_volume(
            vol = self.select_volume(
                vol_day = vol_system_day,
                vol_night = vol_system_night))

        self.player_music_day.change_volume(
            vol = self.select_volume(
                vol_day = vol_music_day,
                vol_night = vol_music_night))

        self.player_music_night.change_volume(
            vol = self.select_volume(
                vol_day = vol_music_day,
                vol_night = vol_music_night))

        # adjusting initial step value for rotary encoder
        self.set_steps_rotary(vol = self.select_volume(
                vol_day = vol_system_day,
                vol_night = vol_system_night))


        # initialisation (note: if initialisation skipped, first time sound played do not work... not sure why)
        self.clock.speak(vol_override = 1) ## tell current time once for initialisation
        self.player_system.play_sound(track_name = "start", vol_override = 1)  ## tell start message once for initialisation
        
        # welcome message
        self.player_system.play_sound(track_name = "start",
                                      vol_override = vol_startup_msg)

        # setting current and fallback modes
        self.mode_list = possible_modes
        if self.clock.is_day():
            self.mode_fallback = "player_day" # fallback = mode when leaving the alarm mode
            self.mode_current = "player_day"    
        else:
            self.mode_fallback = "player_night"
            self.mode_current = "player_night"
        self.change_mode(mode = self.mode_current, speak = False)

        # main loop: running alarm and automatic mode change (which happens if not playing)
        while(True):
            self.clock.ring_alarm()
            if self.clock.is_day() and not self.player_music_day.player.is_playing() and not self.player_music_night.player.is_playing() and not self.player_system.player.is_playing():
                self.mode_fallback = "player_day"
                self.change_mode(mode = "player_day", speak = False)
                self.player_system.change_volume(vol = self.volume_system_day)
                self.player_music_day.change_volume(vol = self.volume_music_day)
                self.player_music_night.change_volume(vol = self.volume_music_day)
            elif not self.clock.is_day() and not self.player_music_day.player.is_playing() and not self.player_music_night.player.is_playing() and not self.player_system.player.is_playing():
                self.mode_fallback = "player_night"
                self.change_mode(mode = "player_night", speak = False)
                self.player_system.change_volume(vol = self.volume_system_night)
                self.player_music_day.change_volume(vol = self.volume_music_night)
                self.player_music_night.change_volume(vol = self.volume_music_night)
            time.sleep(60) # we check things every 60 secs


    def push_top_button(self, button_index):
        "Decide what to do when a push button is pressed"

        btn = self.push_buttons[button_index]
        if self.mode_current == "player_night":
            while btn.is_pressed:
                if btn.active_time > self.hold_time:
                    print(f"button {button_index} was held")
                    self.player_music_night.stop()
                    return
            print(f"button {button_index} was pressed")
            self.player_music_night.play_music(track_index = button_index)

        elif self.mode_current == "player_day":
            while btn.is_pressed:
                if btn.active_time > self.hold_time:
                    print(f"button {button_index} was held")
                    self.player_music_day.stop()
                    return
            print(f"button {button_index} was pressed")
            self.player_music_day.play_music(track_index = button_index)

        elif self.mode_current == "alarm":
            # go to alarm setting
            if button_index == 0:
                print(f"entering alarm setting")
                self.clock.reset_soft(speak = False)
                self.change_mode(mode = "alarm_setting")
            # list all alarms
            elif button_index == 1:
                print(f"listing alarms")
                self.clock.list_alarms()
                self.change_mode(mode = "alarm")
            # delete all alarms
            elif button_index == 2:
                print(f"deleting alarm")
                self.clock.reset_hard()
                self.change_mode(mode = "alarm")
            # quit and return to fallback mode
            elif button_index == 3:
                self.change_mode(mode = self.mode_fallback)

        elif self.mode_current == "alarm_setting":
            while btn.is_pressed:
                if btn.active_time > self.hold_time:
                    if self.clock.check_unregistered_alarm():
                        self.change_mode(mode = "alarm_validation")
                    else:
                        self.change_mode(mode = "alarm_setting")
                    return
            self.clock.alarm[button_index] = (self.clock.alarm[button_index] + 1) % [3, 10, 6, 10][button_index]
            # nb: that time is correct and not e.g. 26:30 is checked in Clock.check_unregistered_alarm()
            print(f"alarm value updated to {self.clock.alarm}")

        elif self.mode_current == "alarm_validation":
            # validate and return to fallback mode
            print(f"validate alarm")
            if button_index == 0:
                self.clock.register_alarm()
                self.change_mode(mode = self.mode_fallback)
            # redo
            elif button_index == 1:
                print(f"validate setting reset")
                self.clock.reset_soft()
                self.change_mode(mode = "alarm_setting")
            # listen again
            elif button_index == 2:
                print(f"recheck alarm")
                self.clock.speak(time_to_read = self.clock.alarm)
                self.change_mode(mode = "alarm_validation")
            # quit and return to fallback mode
            elif button_index == 3:
                print(f"quit alarm setting")
                self.change_mode(mode = self.mode_fallback)


    def change_mode(self, mode, speak = True, update_volume = False):
        if mode == "alarm":
            self.clock.reset_soft(speak = False)
        elif mode not in ["alarm_validation", "alarm_setting", "player_night", "player_day"]:
            raise ValueError('Unknown mode: '+mode)
        self.player_music_day.player.stop()
        self.player_music_night.player.stop()
        self.player_music_day.change_volume(
            vol = self.select_volume(
                vol_day = self.volume_music_day,
                vol_night = self.volume_music_night))
        self.player_music_night.change_volume(
            vol = self.select_volume(
                vol_day = self.volume_music_day,
                vol_night = self.volume_music_night))
        self.mode_current = mode
        if speak:
            self.player_system.play_sound(track_name = mode,
                                          wait_till_completion = False)
        print(self.mode_current)


    def push_mode_button(self):
        "Change the mode to the next one"
        while self.button_rotary_push.is_pressed:
            if self.button_rotary_push.active_time > self.hold_time:
                print(f"button mode was active for more than {self.hold_time} sec")
                if self.mode_current.startswith("alarm_"): # as alarm submodes have no index
                    self.mode_current = "alarm"
                i = self.mode_list.index(self.mode_current)
                i = i + 1 if i + 1 < len(self.mode_list) else 0
                self.change_mode(mode = self.mode_list[i])
                return
        self.clock.speak() ## tell current time


    @staticmethod
    def steps_to_volume(steps, vol_min, vol_max, max_steps):
        "Rescale steps such as those used in rotary encoder to volume scale"
        vol = int(vol_min+((vol_max-vol_min)*(max_steps+steps)/(2*max_steps)))
        return vol


    @staticmethod
    def volume_to_steps(vol, vol_min, vol_max, max_steps):
        "Rescale volume to the scale used by the steps of the rotary encoder"
        step = vol/(vol_max-vol_min)*2*max_steps - max_steps - vol_min
        return step


    def change_volume(self):
        "Update the volume"
        if self.clock.is_day():
            volume_system = self.volume_system_day
            volume_music = self.volume_music_day
        else:
            volume_system = self.volume_system_night
            volume_music = self.volume_music_night

        if not self.player_music_day.player.is_playing() and not self.player_music_night.player.is_playing():
            # update system volume when music is not playing 
                volume_system = self.steps_to_volume(
                    steps = self.button_rotary_turn.steps,
                    vol_min = self.volume_min,
                    vol_max = self.volume_max,
                    max_steps = self.max_steps)
                self.player_system.change_volume(vol = volume_system)
                if not self.player_system.player.is_playing():
                    # feedback for sound change when no sound is playing
                    self.player_system.play_sound(
                        track_name = "volume",
                        wait_till_completion = False,
                        sleep = 0.1)
        else:
            # update music volume as music is playing
            volume_music = self.steps_to_volume(
                steps = self.button_rotary_turn.steps,
                vol_min = self.volume_min,
                vol_max = self.volume_max,
                max_steps = self.max_steps)
            self.player_music_day.change_volume(vol = volume_music)
            self.player_music_night.change_volume(vol = volume_music)

        if self.clock.is_day():
            self.volume_system_day = volume_system
            self.volume_music_day = volume_music
        else:
            self.volume_system_night = volume_system
            self.volume_music_night = volume_music


    def select_volume(self, vol_day, vol_night):
        "Select volumes according to time of the day"
        if self.clock.is_day():
            return vol_day
        else:
            return vol_night


    def set_steps_rotary(self, vol):
        "Set the current step number of the rotary encoder when volume changes automatically"
        self.button_rotary_turn.steps = self.volume_to_steps(vol = vol,
                                                             vol_min = self.volume_min,
                                                             vol_max = self.volume_max,
                                                             max_steps = self.max_steps)



        