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
        "initialize a VLC player"
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

    def play_music(self, tracknumber, vol):
        "Play an audio file based on its number (i.e. after a push button has been pressed), and handle pause/resume/stop"
        track_index = tracknumber - 1
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

    def play_sound(self, trackname, vol):
        "Play an audio file fully (for clock and system sound), no pause/resume/stop possible"
        track_index = self.tracks_files.index(trackname)
        self.player.set_media(self.tracks[track_index])
        self.player.play()
        self.update_volume(vol) # note that volume is not reset after but it should not be a problem

    def update_volume(self, vol):
        "Update the volume of the player"
        print("Update volume to " + str(vol))
        self.player.audio_set_volume(vol)

    def stop(self):
        "Stop the player"
        print("Stop playing track")
        self.player.stop()


class Clock:
    "Read the time out load"

    def __init__(self, player_system, vol_diff_hours = 3,
                 pause_h_m = 0.7, pause_m_m = 0.4):
       "Initialize the clock"
       self.extra_volume_hours = vol_diff_hours
       self.player_system = player_system
       self.pause_h_m = pause_h_m
       self.pause_m_m = pause_m_m

    def speak(self, volume):
        hours = time.strftime("%H", time.localtime())
        minutes = time.strftime("%M", time.localtime())
        print("It is " + hours + " " + minutes)
        self.player_system.play_sound(trackname = hours + ".mp3",
                                          vol = volume + self.extra_volume_hours)
        time.sleep(self.pause_h_m)
        if minutes < "10":
            self.player_system.play_sound(trackname = "00.mp3",
                                              vol = volume)
            time.sleep(self.pause_m_m)
        self.player_system.play_sound(minutes + ".mp3", vol = volume)


class Box:
    "Define class which handle the physical box"

    def __init__(self,
                 gpio_button_1, gpio_button_2, gpio_button_3, gpio_button_4,
                 gpio_button_rotary_push, gpio_button_rotary_CLK, gpio_button_rotary_DT,
                 path_music_sound, path_system_sound,
                 possible_modes = ["player_night"],
                 vol_ini = 30, vol_step = 1, vol_max = 100, vol_startup = 50,
                 hold_time = 1,
                 vol_diff_hours = 3, pause_h_m = 0.7, pause_m_m = 0.4):
        "Initialize the box"
        self.mode_list = possible_modes
        self.mode_current = possible_modes[0]
        self.player_system = Player(path_music = path_system_sound)
        self.player_system.play_sound(trackname = "start.wav", vol = vol_startup)
        self.player_music = Player(path_music = path_music_sound)
        self.volume_current = vol_ini
        self.volume_step = vol_step
        self.volume_max = vol_max
        self.clock = Clock(player_system = self.player_system,
                           vol_diff_hours = vol_diff_hours,
                           pause_h_m = pause_h_m, pause_m_m = pause_m_m)
        
        # setting the mapping for all physical inputs
        gpiozero.Button.was_held = False
        self.button_1 = gpiozero.Button(gpio_button_1)
        self.button_2 = gpiozero.Button(gpio_button_2)
        self.button_3 = gpiozero.Button(gpio_button_3)
        self.button_4 = gpiozero.Button(gpio_button_4)
        self.button_rotary_push = gpiozero.Button(gpio_button_rotary_push)
        self.button_rotary_CLK = gpiozero.Button(gpio_button_rotary_CLK)
        self.button_rotary_DT = gpiozero.Button(gpio_button_rotary_DT)
    
        # setting holding time for push buttons
        self.button_1.hold_time = hold_time
        self.button_2.hold_time = hold_time
        self.button_3.hold_time = hold_time
        self.button_4.hold_time = hold_time
        self.button_rotary_push.hold_time = hold_time

    def run(self):
        "Run the box"

        # reset holding status anytime a button is held
        self.button_1.when_held = self.held
        self.button_2.when_held = self.held
        self.button_3.when_held = self.held
        self.button_4.when_held = self.held
        self.button_rotary_push.when_held = self.held

        # trigger action when button is released
        self.button_1.when_released = lambda x = 1: self.push_top_button(self.button_1, button_number = x)
        self.button_2.when_released = lambda x = 2: self.push_top_button(self.button_2, button_number = x)
        self.button_3.when_released = lambda x = 3: self.push_top_button(self.button_3, button_number = x)
        self.button_4.when_released = lambda x = 4: self.push_top_button(self.button_4, button_number = x)
        self.button_rotary_push.when_released = self.push_mode_button

        # trigger action when button is pressed
        self.button_rotary_CLK.when_pressed = self.increase_volume
        self.button_rotary_DT.when_pressed = self.decrease_volume

        # otherwise, wait
        signal.pause()

    def held(self, button):
        "Set holding status"
        button.was_held = True

    def push_top_button(self, button, button_number):
        "Decide what to do when a push button is pressed"

        if self.mode_current == "player_night":
            if (button.was_held):
                print("button " + str(button_number) + " was held")
                self.player_music.stop()
                button.was_held = False
            else:
                print("button " + str(button_number) + " was pressed")
                self.player_music.play_music(tracknumber = button_number, vol = self.volume_current)

    def push_mode_button(self):
        "Change the mode to the next one"
        if (self.button_rotary_push.was_held):
                print("button mode was held")
                i = self.mode_list.index(self.mode_current)
                i += 1 if i + 1 < len(self.mode_list) else 0
                self.mode_current = self.mode_list[i]
                print(self.mode_current)
                self.button_rotary_push.was_held = False
        else:
                self.clock.speak(volume = self.volume_current)

    def increase_volume(self):
        "Increase volume by one step"
        if self.button_rotary_CLK.value == 1 and self.button_rotary_DT.value == 0:
            self.volume_current = min(self.volume_current + self.volume_step, self.volume_max)
            self.player_music.update_volume(self.volume_current)
            self.player_system.update_volume(self.volume_current)

    def decrease_volume(self):
        "Decrease volume by one step"
        if self.button_rotary_CLK.value == 0 and self.button_rotary_DT.value == 1:
            self.volume_current = max(self.volume_current - self.volume_step, 0)
            self.player_music.update_volume(self.volume_current)
            self.player_system.update_volume(self.volume_current)


## RUNNING THE PROGRAM

box = Box(gpio_button_1 = 11, gpio_button_2 = 10, gpio_button_3 = 22, gpio_button_4 = 9,
          gpio_button_rotary_push = 25, gpio_button_rotary_CLK = 7, gpio_button_rotary_DT = 8,
          path_music_sound = "/home/pi/playlist_night",
          path_system_sound = "/home/pi/playlist_system",
          possible_modes = ["player_night"],
          vol_ini = 20, vol_step = 1, vol_max = 100, vol_startup = 50,
          hold_time = 1, vol_diff_hours = 3, pause_h_m = 0.7, pause_m_m = 0.4)

box.run()
