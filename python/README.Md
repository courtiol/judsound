# Main Python script for the project

This is the main script of the project.

It is automatically launched, as the pi boots, to handle playing various musics based on the user inputs.


## Main libraries

### vlc

I used the python library [`vlc`](https://pypi.org/project/python-vlc/) to control the playing of the music tracks.
I knew VLC as a free software playing videos, but it turns out that it is based on a powerful C library (`LibVLC`), which can play music as well.
A major drawback is that the library comes with tons of dependencies, and I could not find any documentation of the python functions (perhaps because the library is only a wrapper the C library).

Yet, after looking at a some code on the net, I found it simple to use and rich in interesting behaviors I took (or will take) advantage on; such as:

- it can play a wide variety of audio formats (provided that the right dependencies are installed)

- you can easily control the volume of each track independently (e.g. could be useful for having alarm louder)

- you can pause, restart, stop music tracks

- you can create several players

Perhaps it would be a good idea to use a more lightweight audio python library, but failing to identify one, I am sticking for now to `vlc`.


### gpiozero

I also used the python library [`gpiozero`](https://github.com/gpiozero/gpiozero/) to detect inputs from the user.
This library is simpler than the alternative `GPIO`, very well [documented](https://gpiozero.readthedocs.io/en/stable/), and seems to cover the needs for this project.

It can handle push buttons out of the box.
It even allows for different behaviors if the button are kept pressed for a given duration or not.
To the day of this writing, it did not support fully rotary encoders (used here as the volume button), but I was able to figure out how to tinker some code to do so.
Explanations on how rotary encoders communicate certainly helped (see e.g. [here](https://blog.sharedove.com/adisjugo/index.php/2020/05/10/using-ky-040-rotary-encoder-on-raspberry-pi-to-control-volume/)).
There seem to be a [plan]((https://github.com/gpiozero/gpiozero/pull/482)) to add that support to `gpiozero`.


## Playing music?

I created a class `Player` to create VLC players. Using different players simplifies a bit the programming. For example, different usage mode (alarm, music...) can have their own player with dedicated music tracks. It also allows you to play several tracks simultaneously. For instance, I chose for now that the reading of the time happens without pausing the music (since my wife listens to guided mediation, it makes sense; over Hard Rock, probably not).

(more to come)


## How to handle physical inputs?

(to come)


### Push buttons

(to come)


### Rotary encoder

(to come)


### Infra red transmitter

(to come)

