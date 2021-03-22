#!/usr/bin/python3

import gpiozero
#import signal # no longer needed since loop for alarm
import os
import re
import vlc
import time


class Player:
    "Define class which handles the music (VLC) player"

    def __init__(self, path_music, tracks_dictionary = None):
        """Initialize a VLC player

        Keyword arguments:
        path_music -- a string specifying the path to the directory where the audio files are stored 
        tracks_dictionary -- a dictionary for the system sounds
        """

        instance_vlc = vlc.Instance()
        self.player = instance_vlc.media_player_new()

        # fetching music tracks and adding them to the player
        path_music = os.path.normpath(path_music)
        files_in_path_music = sorted(os.listdir(path_music)) # extract and sort files 
                                                             # (since max # should be < 10,
                                                             # simple sorting should work)
        self.tracks_files = list(filter(
                                lambda x: re.search('.*mp3$|.*wav$', x),
                                files_in_path_music
                            )) # only keep file starting with number and ending with mp3 or wav
        tracks_paths = [path_music + '/' + s 
                          for s in self.tracks_files] # add path to file names
        self.tracks = [instance_vlc.media_new(tracks_paths[i]) 
                          for i in range(len(tracks_paths))] # register all tracks to VLC 
                                                             # (although only 4 are accessible 
                                                             # via the top push buttons)
        self.tracks_dictionary = tracks_dictionary

    def play_music(self, track_index, vol):
        """Play an audio file based on its number and handle pause/resume/stop
        
        This is the function called when a push button has been pressed (in playlist mode).

        Keyword arguments:
        track_index -- an integer specifying the number of the track to play
        vol -- an integer specifying the volume used to play the music
        """

        if self.player.get_media() is None or os.path.basename(
                self.player.get_media().get_mrl()) != self.tracks_files[track_index]:
            # case no track playing or other track playing 
            # -> we start playing the good track
            self.player.stop()
            self.player.set_media(self.tracks[track_index])
            print("start playing new track")
            self.player.play()
        else:
            # case correct track already playing -> we pause or resume
            print("pause or resume playing track")
            was_playing = self.player.is_playing()
            self.player.pause()
            if not was_playing and not self.player.is_playing():
                # case no resume possible since track had never started 
                # -> play
                self.player.stop() # in case the same track had previously 
                                   # played till end, it needs to be stopped 
                                   # before playing
                self.player.play()
        self.update_volume(vol)

    def play_sound(self, track_name, vol, wait_till_completion = True):
        """Play an audio file fully with no pause/resume/stop possible

        This is the function called to speak the time and produce other system sound

        Keyword arguments:
        track_name -- a string indicating which audio file to play (as defined in self.tracks_dictionary)
        vol -- an integer specifying the volume used to play the music
        wait_till_completion -- a boolean indicating whether or not to wait till the sound has fully played
        """

        file = self.tracks_dictionary[track_name]
        self.player.set_media(self.tracks[self.tracks_files.index(file)])
        self.player.play()
        self.update_volume(vol) # note that volume is not reset after but it should not be a problem
        if wait_till_completion:
            self.wait_done()
        else:
            time.sleep(0.1)

    def wait_done(self):
        time.sleep(0.1)
        while self.player.is_playing():
            time.sleep(0.1)

    def update_volume(self, vol, verbose = True):
        "Update the volume of the player"
        if verbose:
            print(f"update volume to {vol}")
        self.player.audio_set_volume(vol)

    def stop(self):
        "Stop the player"
        print("stop playing track")
        self.player.stop()


class Clock:
    "Define the class which handles the alarm-clock"

    def __init__(self, player_system, file_to_alarms, vol_diff_hours = 3,
                 pause_h_m = 0.7, pause_0m_m = 0.4):
       """Initialize the clock

       Keyword arguments:
        player_system -- an object of class Player
        file_to_alarms -- a string specifying the file (including its paths) where alarms are written and read
        vol_diff_hours -- an integer specifying how much more than the baseline volume to speak the hours (default = 3)
        pause_h_m -- a float specifying the time in seconds between the reading of the hours and that of the minutes (default = 0.7)
        pause_0m_m -- a float specifying the time in seconds between the reading of the 0 minute and the single digit minutes (default = 0.4)
       """

       self.extra_volume_hours = vol_diff_hours
       self.player_system = player_system
       self.file_to_alarms = file_to_alarms
       self.pause_h_m = pause_h_m
       self.pause_0m_m = pause_0m_m
       self.alarm = [0, 0, 0, 0] # a given alarm being set
       self.alarms = [] # the list of alarms

    def time(self):
        hours = time.strftime("%H", time.localtime())
        minutes = time.strftime("%M", time.localtime())
        return [hours, minutes]

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
        time.sleep(self.pause_h_m)
        if minutes < "10":
            self.player_system.play_sound(track_name="00", vol=vol)
            time.sleep(self.pause_0m_m)
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
        self.player_system.play_sound(track_name="alarms_deleted", vol=vol, wait_till_completion=False)

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
        self.player_system.play_sound(track_name="alarm_set_at", vol=vol)
        self.speak(vol=vol, time_to_read=self.alarm)

    def list_alarms(self, vol, update = True):
        if update:
            self.read_alarms()
        if self.alarms:
            self.player_system.play_sound(track_name="alarms_list", vol=vol)
            for alarm in self.alarms:
                self.speak(vol = vol, time_to_read=alarm)
        self.player_system.play_sound(track_name="alarm_validation", vol=vol)

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
    """

    def __init__(self,
                 gpio_push_buttons, gpio_button_rotary_push, gpio_button_rotary_CLK, gpio_button_rotary_DT,
                 path_music_sound, path_system_sound, file_to_alarms,
                 possible_modes = ["player_night", "alarm"],
                 vol_ini = 30, vol_step = 1, vol_max = 100, vol_startup = 50, vol_alarm = 50,
                 hold_time = 1,
                 vol_diff_hours = 3, pause_h_m = 0.5, pause_0m_m = 0.4):
        "Initialize the box"
        self.mode_list = possible_modes
        self.mode_current = possible_modes[0]
        
        tracks_system = {
            # welcome sound
            "start": "start.wav",
            # changing mode
            "alarm": "alarm_mode.wav",
            "alarm_validation": "alarm_validation.mp3",
            "player_night": "player_night_mode.wav",
            # setting alarm
            "alarm_preset_at":"alarm_preset_at.wav",
            "alarm_set_at":"alarm_set_at.wav",
            "alarm_not_set": "alarm_not_set.wav",
            "alarm_validation3": "alarm_validation.mp3",
            "alarms_list": "alarms_list.wav",
            "alarms_deleted":"alarms_deleted.wav"
        }
        for m in range(60):
            key = f'{m:02d}'
            tracks_system[key] = key + '.mp3' # add minutes/hours to dictionary
        print("loaded dictionary for system sounds:")
        print(tracks_system)
        
        self.player_system = Player(path_music=path_system_sound, tracks_dictionary=tracks_system)
        self.player_system.play_sound(track_name="start", vol=vol_startup)
        self.player_music = Player(path_music=path_music_sound)
        self.volume_current = vol_ini
        self.volume_step = vol_step
        self.volume_max = vol_max
        self.clock = Clock(player_system=self.player_system,
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


## RUNNING THE PROGRAM

Box(gpio_push_buttons=[11, 10, 22, 9],
    gpio_button_rotary_push=25, gpio_button_rotary_CLK=7, gpio_button_rotary_DT=8,
    path_music_sound="/home/pi/playlist_night",
    path_system_sound="/home/pi/playlist_system",
    file_to_alarms="/home/pi/judsound_alarms",
    possible_modes=["player_night", "alarm"],
    vol_ini=20, vol_step=1, vol_max=100, vol_startup=20, vol_alarm=50,
    hold_time=1, vol_diff_hours=3, pause_h_m=0.5, pause_0m_m=0.4)
