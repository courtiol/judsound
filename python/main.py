#!/usr/bin/python3

import gpiozero
import signal
import os
import re
import vlc
import time


class Mode:
    "Define class which keeps track of the current operating mode and allows for changing it"
    possible = ["player_night"]

    def __init__(self, i = 0):
        "Initialize the mode"
        self.current = self.possible[i]

    def change(self):
        "Change the mode to the next one"
        i = self.possible.index(self.current)
        if i + 1 < len(self.possible):
            i_next = i + 1
        else:
            i_next = 0
        self.current = self.possible[i_next]
        volume.reset() # when mode changes, we reset the volume -> good behavior?
        player.update_volume(volume.get())
        player.stop() # we stop whatever could have been playing
        print(self.current)

    def get(self):
        "Return current mode"
        return(self.current)


class Volume:
    "Define class which keeps track of the volume and allows for changing it"

    def __init__(self, vol_ini = 30, vol_step = 1, vol_max = 100):
        "Initialize the volume"
        self.volume_ini = vol_ini
        self.volume = vol_ini
        self.step = vol_step
        self.max = vol_max

    def increase(self):
        "Increase volume by one step"
        if rotary_CLK.value == 1 and rotary_DT.value == 0:
            if self.volume + self.step < self.max:
                volume_next = self.volume + self.step
            else:
                volume_next = self.max
            self.volume = volume_next
            player.update_volume(self.volume)
            player_system.update_volume(self.volume)
            print("volume increased to " + str(self.volume))

    def decrease(self):
        "Decrease volume by one step"
        if rotary_CLK.value == 0 and rotary_DT.value == 1:
            if self.volume - self.step > 0:
                volume_next = self.volume - self.step
            else:
                volume_next = 0
            self.volume = volume_next
            player.update_volume(self.volume)
            print("volume decreased to " + str(self.volume))

    def reset(self):
        "Reset volume to baseline"
        self.volume = self.volume_ini
        print("volume rest to " + str(self.volume))

    def get(self):
        "Return current volume"
        return(self.volume)


class Player:
    "Define class which handles the music (VLC) player"

    def __init__(self, path_music):
        "initialize a VLC player"
        instance_vlc = vlc.Instance()
        self.player = instance_vlc.media_player_new()
        self.player.audio_set_volume(volume.get())

        ## fetching music tracks and adding them to the player
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

    def play(self, track):
        "Updates the status of the player after a push button has been pressed"
        track_index = track - 1
        if self.player.get_media() == None or os.path.basename(
                self.player.get_media().get_mrl()) != self.tracks_files[track_index]:
            # case no track or other track playing 
            # -> we start playing the good track
            self.player.stop()
            self.player.set_media(self.tracks[track_index])
            self.player.audio_set_volume(volume.get())
            self.player.play()
        else:
            # case correct track already playing -> we pause or resume
            was_playing = self.player.is_playing()
            self.player.pause()
            if not was_playing and not self.player.is_playing():
                # case no resume possible since track had never started 
                # -> play
                self.player.stop() # in case the same track had previously 
                                   # played till end, it needs to be stopped 
                                   # before playing
                self.player.audio_set_volume(volume.get())
                self.player.play()

    def play_track(self, trackname):
        "Play specific audio file (for clock and system sound)"
        track_index = self.tracks_files.index(trackname)
        self.player.set_media(self.tracks[track_index])
        self.player.audio_set_volume(volume.get())
        self.player.play()

    def update_volume(self, volume):
        "Update the volume of the player"
        self.player.audio_set_volume(volume)

    def stop(self):
        "Stop the player"
        self.player.stop()


## Define actions for push buttons conditionally on the mode
def action_1():
    "This is a button-specific wrapper for one of the top push button"
    if mode.get() == "player_night":
        if (button_1.was_held):
            print("button 1 was held")
            player.stop()
            button_1.was_held = False
        else:
            print("button 1 was pressed")
            player.play(track = 1)

def action_2():
    "This is a button-specific wrapper for one of the top push button"
    if mode.get() == "player_night":
        if (button_2.was_held):
            print("button 2 was held")
            player.stop()
            button_2.was_held = False
        else:
            print("button 2 was pressed")
            player.play(track = 2)

def action_3():
    "This is a button-specific wrapper for one of the top push button"
    if mode.get() == "player_night":
        if (button_3.was_held):
            print("button 3 was held")
            player.stop()
            button_3.was_held = False
        else:
            print("button 3 was pressed")
            player.play(track = 3)

def action_4():
    "This is a button-specific wrapper for one of the top push button"
    if mode.get() == "player_night":
        if (button_4.was_held):
            print("button 4 was held")
            player.stop()
            button_4.was_held = False
        else:
            print("button 4 was pressed")
            player.play(track = 4)

def action_mode():
    "This is a button-specific wrapper for the mode button"
    if (button_mode.was_held):
            print("button mode was held")
            mode.change()
            button_mode.was_held = False
    else:
            clock()

def held(btn):
    "Check if button has been held or not"
    #print("button " + str(btn) + " held")
    btn.was_held = True

def clock():
    "Read the time out load"
    hours = time.strftime("%H", time.localtime())
    minutes = time.strftime("%M", time.localtime())
    print("It is " + hours + " " + minutes)
    player_system.play_track(hours + ".mp3")
    time.sleep(0.7)
    if minutes < "10":
        player_system.play_track("00.mp3")
        time.sleep(0.4)
    player_system.play_track(minutes + ".mp3")


## Setting the mapping for all physical inputs
gpiozero.Button.was_held = False

button_1 = gpiozero.Button(11)
button_2 = gpiozero.Button(10)
button_3 = gpiozero.Button(22)
button_4 = gpiozero.Button(9)
button_mode = gpiozero.Button(25) # push button from rotary encoder
rotary_CLK = gpiozero.Button(7)
rotary_DT = gpiozero.Button(8)

## Setting holding time for push buttons
button_1.hold_time = 1
button_2.hold_time = 1
button_3.hold_time = 1
button_4.hold_time = 1
button_mode.hold_time = 1

## Run program
volume = Volume()
mode = Mode()
player_system = Player(path_music = "/home/pi/playlist_system")
player_system.play_track("start.wav")
player = Player(path_music = "/home/pi/playlist_night")

rotary_CLK.when_pressed = volume.increase
rotary_DT.when_pressed = volume.decrease

button_1.when_held = held
button_2.when_held = held
button_3.when_held = held
button_4.when_held = held
button_mode.when_held = held

button_1.when_released = action_1
button_2.when_released = action_2
button_3.when_released = action_3
button_4.when_released = action_4
button_mode.when_released = action_mode

signal.pause()
