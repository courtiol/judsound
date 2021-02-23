# Main Python script for the project

This is the main script of the project.

It is automatically launched as the pi boots to handle playing various musics based on the user inputs.


## Main libraries

### vlc

I used the python library `vlc` to control the playing of the music tracks.

This library comes with tons of dependencies but it is simple to use and allows certain behavior I take (or planning to take) advantage on:

- it can play a wide variety of audio formats (provided that the right dependencies are installed)

- you can easily control the volume of each track independently (e.g. could be useful for having alarm louder)

- you can pause, restart, stop music tracks

- you can create several players

Perhaps more lightweight audio python libraries exist.


### gpiozero

I used the python library `gpiozero` to detect inputs from the user.

This library is simple and very well documented.

It can handle push buttons out of the box.

To the day of this writing it did not support fully rotary encoders (used here as the volume button), but I was able to figure out how to tinker some code to do so with the help of the following explanation of how  rotary encoders communicate: https://blog.sharedove.com/adisjugo/index.php/2020/05/10/using-ky-040-rotary-encoder-on-raspberry-pi-to-control-volume/ (contrary to what the author does there I did not rely on the library `GPIO`).


### signal

(to come)

## How to play music?

(to come)


## How to handle physical input?

(to come)

### Push buttons

(to come)

### Rotary encoder

(to come)

### Infra red transmitter

(to come)









