#!/usr/bin/python3

import gpiozero
import signal
import os
import re
import vlc
import time


class Player:
    "Define class which handles the music (VLC) player"

    def __init__(self, path_music):
        """Initialize a VLC player

        Keyword arguments:
        path_music -- a string specifying the path to the directory where the audio files are stored 
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
            print("Start playing new track")
            self.player.play()
        else:
            # case correct track already playing -> we pause or resume
            print("Pause or resume playing track")
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

    def play_sound(self, track_name, vol):
        """Play an audio file fully with no pause/resume/stop possible

        This is the function called to speak the time and produce other system sound

        Keyword arguments:
        track_name -- a string indicating the file name of the audio file to play
        vol -- an integer specifying the volume used to play the music
        """

        self.player.set_media(self.tracks[self.tracks_files.index(track_name)])
        self.player.play()
        self.update_volume(vol) # note that volume is not reset after but it should not be a problem

    def update_volume(self, vol, to_print = True):
        "Update the volume of the player"
        if to_print:
            print("Update volume to " + str(vol))
        self.player.audio_set_volume(vol)

    def stop(self):
        "Stop the player"
        print("Stop playing track")
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
       self.alarm = [0, 0, 0, 0]

    def time(self):
        hours = time.strftime("%H", time.localtime())
        minutes = time.strftime("%M", time.localtime())
        return [hours, minutes]

    def convert_hhmm_to_hm(self, time_to_convert):
        return [str(time_to_convert[0]) + str(time_to_convert[1]), str(time_to_convert[2]) + str(time_to_convert[3])]

    def speak(self, vol, time_to_read = None):
        if time_to_read is None:
            time_to_read = self.time()
            prefix = "It is "
        else:
            time_to_read = self.convert_hhmm_to_hm(time_to_convert = time_to_read)
            prefix = "Alarm pre-set at "
        hours = time_to_read[0]
        minutes = time_to_read[1]
        print(prefix + hours + " " + minutes)
        self.player_system.play_sound(track_name = hours + ".mp3",
                                      vol = vol + self.extra_volume_hours)
        time.sleep(self.pause_h_m)
        if minutes < "10":
            self.player_system.play_sound(track_name = "00.mp3",
                                          vol = vol)
            time.sleep(self.pause_0m_m)
        self.player_system.play_sound(minutes + ".mp3", vol = vol)

    def set_alarm(self, add):
        self.alarm = [x + y for x, y in zip(self.alarm, add)] # add element per element
        if self.alarm[0] > 2:
            self.alarm[0] = 0
        if self.alarm[1] > 9:
            self.alarm[1] = 0
        if self.alarm[2] > 5:
            self.alarm[2] = 0
        if self.alarm[3] > 9:
            self.alarm[3] = 0
        print("alarm value updated to " + str(self.alarm))

    def reset_soft(self, vol):
        self.alarm = [0, 0, 0, 0]
        if vol > 0:
            self.player_system.play_sound(track_name = "alarm_not_set.wav", vol = vol)
            time.sleep(3)

    def reset_hard(self, vol):
        self.reset_soft(vol = 0)
        file = open(self.file_to_alarms, "w") # erase content of file
        file.close()
        self.player_system.play_sound(track_name = "alarms_deleted.wav", vol = vol)
        time.sleep(3)

    def check_unregistered_alarm(self, vol):
        self.player_system.play_sound(track_name = "alarm_preset_at.wav", vol = vol)
        time.sleep(3)
        self.speak(vol = vol, time_to_read = self.alarm)
        time.sleep(3)

    def register_alarm(self, vol):
        print("saving alarm to file")
        file = open(self.file_to_alarms, "a")
        file.writelines(self.convert_hhmm_to_hm(time_to_convert = self.alarm))
        file.write("\n")
        file.close()
        self.player_system.play_sound(track_name = "alarm_set_at.wav", vol = vol)
        time.sleep(3)
        self.speak(vol = vol, time_to_read = self.alarm)
        time.sleep(3)

    def list_alarms(self, vol):
        file = open(self.file_to_alarms, "r")
        alarm_text = file.readlines()
        alarms = [[alarm_text[i][0], alarm_text[i][1], alarm_text[i][2], alarm_text[i][3]] for i in range(len(alarm_text))]
        print("alarms read as:", alarm_text)
        if alarms != []:
            self.player_system.play_sound(track_name = "alarms_list.wav", vol = vol)
            time.sleep(2)
            for alarm in alarms:
                self.speak(vol = vol, time_to_read = alarm)
                time.sleep(2)
        file.close()
        self.player_system.play_sound(track_name = "alarm_validation.mp3", vol = vol)
        time.sleep(1)

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
    hold_time -- an integer specifying the duration (in seconds) for which the press of a push button triggers a holding behaviour (default = 1) 
    vol_diff_hours -- an integer specifying how much more than the baseline volume to speak the hours (default = 3)
    pause_h_m -- a float specifying the time in seconds between the reading of the hours and that of the minutes (default = 0.7)
    pause_0m_m -- a float specifying the time in seconds between the reading of the 0 minute and the single digit minutes (default = 0.4)
    """

    def __init__(self,
                 gpio_push_buttons, gpio_button_rotary_push, gpio_button_rotary_CLK, gpio_button_rotary_DT,
                 path_music_sound, path_system_sound, file_to_alarms,
                 possible_modes = ["player_night", "alarm"],
                 vol_ini = 30, vol_step = 1, vol_max = 100, vol_startup = 50,
                 hold_time = 1,
                 vol_diff_hours = 3, pause_h_m = 0.7, pause_0m_m = 0.4):
        "Initialize the box"
        self.mode_list = possible_modes
        self.mode_current = possible_modes[0]
        self.player_system = Player(path_music = path_system_sound)
        self.player_system.play_sound(track_name = "start.wav", vol = vol_startup)
        self.player_music = Player(path_music = path_music_sound)
        self.volume_current = vol_ini
        self.volume_step = vol_step
        self.volume_max = vol_max
        self.clock = Clock(player_system = self.player_system,
                           file_to_alarms = file_to_alarms,
                           vol_diff_hours = vol_diff_hours,
                           pause_h_m = pause_h_m, pause_0m_m = pause_0m_m)
        
        # setting the mapping for all physical inputs
        gpiozero.Button.was_held = False
        self.push_buttons = [gpiozero.Button(btn) for btn in gpio_push_buttons]
        self.button_rotary_push = gpiozero.Button(gpio_button_rotary_push)
        self.button_rotary_CLK = gpiozero.Button(gpio_button_rotary_CLK)
        self.button_rotary_DT = gpiozero.Button(gpio_button_rotary_DT)
    
        # adjust settings for the rotary encoder
        self.button_rotary_push.hold_time = hold_time
        self.button_rotary_push.when_held = self.held
        self.button_rotary_push.when_released = self.push_mode_button
        self.button_rotary_CLK.when_pressed = self.change_volume

        # adjust settings for the push buttons
        for btn_index, btn in enumerate(self.push_buttons):
            btn.hold_time = hold_time
            btn.when_held = self.held
            btn.when_released = lambda i = btn_index: self.push_top_button(button_index = i) 
            # note: i = btn_index is required for lambda to work using the right scope (specific to using for loops)
            # (i.e. don't pass argument(s) directly to push_top_button call)

        # wait until user action
        signal.pause()

    def held(self, button):
        "Set holding status"
        button.was_held = True

    def push_top_button(self, button_index):
        "Decide what to do when a push button is pressed"

        btn = self.push_buttons[button_index]
        if self.mode_current == "player_night":
            if btn.was_held:
                print("button " + str(button_index) + " was held")
                self.player_music.stop()
                btn.was_held = False
            else:
                print("button " + str(button_index) + " was pressed")
                self.player_music.play_music(track_index = button_index, vol = self.volume_current)
        elif self.mode_current == "alarm":
            if btn.was_held:
                self.clock.check_unregistered_alarm(vol = self.volume_current)
                self.change_mode(mode = "alarm_validation")
                btn.was_held = False
            else:
                if button_index == 0:
                    self.clock.set_alarm(add = [1, 0, 0, 0])
                elif button_index == 1:
                    self.clock.set_alarm(add = [0, 1, 0, 0])
                elif button_index == 2:
                    self.clock.set_alarm(add = [0, 0, 1, 0])
                elif button_index == 3:
                    self.clock.set_alarm(add = [0, 0, 0, 1])
        elif self.mode_current == "alarm_validation":
            if btn.was_held:
                # register and quit
                self.clock.register_alarm(vol = self.volume_current)
                self.change_mode(mode = "player_night")
                btn.was_held = False
            else:
                # cancel and return to player
                if button_index == 0:
                    self.clock.reset_soft(vol = self.volume_current)
                    self.change_mode(mode = "player_night")
                # return to preset
                if button_index == 1:
                    self.clock.reset_soft(vol = self.volume_current)
                    self.change_mode(mode = "alarm")
                # list all alarms
                if button_index == 2:
                    self.clock.list_alarms(vol = self.volume_current)
                # cancel all alarms
                if button_index == 3:
                    self.clock.reset_hard(vol = self.volume_current)
                    self.change_mode(mode = "player_night")

    def change_mode(self, mode):
        if mode == "alarm":
            self.mode_current = "alarm"
            self.clock.reset_soft(vol = 0)
            self.player_system.play_sound(track_name = "alarm_mode.wav", vol = self.volume_current)
        elif mode == "alarm_validation":
            self.mode_current = "alarm_validation"
            self.player_system.play_sound(track_name = "alarm_validation.mp3", vol = self.volume_current)
        elif mode == "player_night":
            self.mode_current = "player_night"
            self.player_system.play_sound(track_name = "player_night_mode.wav", vol = self.volume_current)
        print(self.mode_current)

    def push_mode_button(self):
        "Change the mode to the next one"
        if self.button_rotary_push.was_held:
            print("button mode was held")
            i = self.mode_list.index(self.mode_current)
            i = i + 1 if i + 1 < len(self.mode_list) else 0
            self.change_mode(mode = self.mode_list[i])
            self.button_rotary_push.was_held = False
        else:
            self.clock.speak(vol = self.volume_current)

    def change_volume(self):
        "Change the volume of all players"
        #print("CLK = " + str(self.button_rotary_CLK.value) + " DT = " + str(self.button_rotary_DT.value))
        add_volume = self.volume_step if self.button_rotary_DT.value == 0 else - self.volume_step
        self.volume_current = max(min(self.volume_current + add_volume, self.volume_max), 0)
        self.player_music.update_volume(vol = self.volume_current)
        self.player_system.update_volume(vol = self.volume_current, to_print = False)


## RUNNING THE PROGRAM

Box(gpio_push_buttons = [11, 10, 22, 9],
    gpio_button_rotary_push = 25, gpio_button_rotary_CLK = 7, gpio_button_rotary_DT = 8,
    path_music_sound = "/home/pi/playlist_night",
    path_system_sound = "/home/pi/playlist_system",
    file_to_alarms = "/home/pi/judsound_alarms",
    possible_modes = ["player_night", "alarm"],
    vol_ini = 20, vol_step = 1, vol_max = 100, vol_startup = 20,
    hold_time = 1, vol_diff_hours = 3, pause_h_m = 0.7, pause_0m_m = 0.4)
