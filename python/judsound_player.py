#!/usr/bin/python3

import os
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

        print("Creation of VLC instance")
        instance_vlc = vlc.Instance()

        print("Creation of VLC Player")
        self.player = instance_vlc.media_player_new()

        # fetching music tracks and adding them to the player
        path_music = os.path.normpath(path_music)
        files_in_path_music = sorted(os.listdir(path_music)) # extract and sort files 
                                                             # (since max # should be < 10,
                                                             # simple sorting should work)
        self.tracks_files = [file for file in files_in_path_music if file.endswith('mp3') or file.endswith('wav')]

        tracks_paths = [path_music + '/' + s 
                          for s in self.tracks_files] # add path to file names

        print("Adding tracks to VLC instance")     
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

        print("Play music")
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
            print("pause or resume playing track from where it was")
            was_playing = self.player.is_playing()
            self.player.pause()
            time.sleep(0.2) # pause otherwise next step does not detect change
            if not was_playing and not self.player.is_playing():
                print("start replaying track from beginning")
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

        print("Play sound")
        file = self.tracks_dictionary[track_name]
        print(f"play sound {file}")
        self.update_volume(vol) # note that volume is not reset after but it should not be a problem
        self.player.set_media(self.tracks[self.tracks_files.index(file)])
        self.player.play()
        if wait_till_completion:
            self.wait_done()
        else:
            time.sleep(0.5)

    def wait_done(self):
        time.sleep(0.2)
        while self.player.is_playing():
            time.sleep(0.2)

    def update_volume(self, vol, verbose = True):
        "Update the volume of the player"
        if verbose:
            print(f"update volume to {vol}")
        self.player.audio_set_volume(vol)

    def stop(self):
        "Stop the player"
        print("stop playing track")
        self.player.stop()
