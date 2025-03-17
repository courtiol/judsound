#!/usr/bin/python3

import time
import warnings
import judsound_box

## PRELUDE

print('*** Starting Judsound ***')
warnings.filterwarnings('default', category = DeprecationWarning) # to show deprecation warnings in console

time.sleep(10) # give some time for ALSA service to start (10s should be OK)

file_path = '/home/pi/judsound_alarms'
try:
    open(file_path, 'x')
except FileExistsError:
    print(f"The file {file_path} already exists.")

## RUNNING THE PROGRAM

judsound_box.Box(
    gpio_push_buttons = [11, 10, 22, 9],
    gpio_button_rotary_push = 25,
    gpio_button_rotary_CLK = 7,
    gpio_button_rotary_DT = 8,
    gpio_button_rotary_max_steps = 20, #half of the effective number of steps
    path_music_night = "/home/pi/playlist_night",
    path_music_day = "/home/pi/playlist_day",
    path_system_sound = "/home/pi/playlist_system",
    file_to_alarms = "/home/pi/judsound_alarms",
    possible_modes = ["player_night", "alarm", "player_day"],
    vol_min = 10,
    vol_max = 50,
    vol_music_day = 30,
    vol_music_night = 15,
    vol_system_day = 35,
    vol_system_night = 25,
    vol_startup_msg = 50,
    vol_alarm = 50,
    vol_diff_hours = 1,
    hold_time = 1,
    night_day_h = 6,
    day_night_h = 22,
    tracks_system = {# welcome sound
                     "start": "start.wav",
                     # changing mode
                     "alarm": "alarm_mode.mp3",
                     "player_night": "player_night_mode.wav",
                     "player_day": "player_day_mode.wav",
                     # setting alarm
                     "alarm_sound": "start.wav",
                     "alarm_preset_at":"alarm_preset_at.wav",
                     "alarm_set":"alarm_set.mp3",
                     "alarm_not_set": "alarm_not_set.wav",
                     "alarm_setting": "alarm_setting.mp3",
                     "alarm_none": "alarm_none.wav",
                     "alarm_validation": "alarm_validation.mp3",
                     "alarms_list": "alarms_list.wav",
                     "alarms_deleted":"alarms_deleted.wav",
                     # volume feedback sound
                     "volume":"water-droplet-2-165634_short.wav"})
