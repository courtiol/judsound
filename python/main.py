#!/usr/bin/python3

import judsound_box

## RUNNING THE PROGRAM

judsound_box.Box(gpio_push_buttons=[11, 10, 22, 9],
    gpio_button_rotary_push=25, gpio_button_rotary_CLK=7, gpio_button_rotary_DT=8,
    path_music_sound="/home/pi/playlist_night",
    path_system_sound="/home/pi/playlist_system",
    file_to_alarms="/home/pi/judsound_alarms",
    possible_modes=["player_night", "alarm"],
    vol_ini=20, vol_step=1, vol_max=100, vol_startup=20, vol_alarm=50,
    hold_time=1, vol_diff_hours=3, pause_h_m=0.5, pause_0m_m=0.4)
