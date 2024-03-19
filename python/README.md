# Python code for the project

This is where I put the Python script for this project.

The script `main.py` is automatically launched when the pi boots.

The other scripts defined classes used by the main program.


## Dependencies

The entire project relies on no more than four libraries. On top of using very few functions from the mainstream libraries `time` (to handle time) and `os` (to handle file and directory paths), I chose to rely on [`vlc`](https://pypi.org/project/python-vlc/) and [`gpiozero`](https://github.com/gpiozero/gpiozero/). Here is why.

### vlc

I used the python library [`vlc`](https://pypi.org/project/python-vlc/) to control the playing of the music and sound tracks.
I knew VLC as a free software playing videos, but VLC can play music as well.
The software VLC is based on a powerful C library (`LibVLC`), which has been ported to Python.

A major drawback is that installing VLC (a requirement to access `LibVLC` and other tools needed to play media files) comes with tons of dependencies. I also could not find any documentation of the python functions (perhaps because the library is only a wrapper around the C library).

Yet, after looking at a some toy code on the net, I found it simple to use and rich in behaviors I could took advantage on; such as:

- it can play a wide variety of audio formats (provided that the right dependencies are installed)

- you can easily control the volume of each track independently (e.g. could be useful for having alarm louder)

- you can pause, restart, stop music tracks

- you can create several players

- you can extract information about the current state of the player (e.g. is it currently playing)

Perhaps it would be a good idea to use a more lightweight audio python library, but failing to identify one, I am sticking for now to `vlc`.


### gpiozero

I also used the python library [`gpiozero`](https://github.com/gpiozero/gpiozero/) to detect inputs from the user.
This library is simpler than the alternative `GPIO`, very well [documented](https://gpiozero.readthedocs.io/en/stable/), and seems to cover the needs for this project.

It can handle push buttons out of the box.
It even allows for different behaviors if the button are kept pressed for a given duration or not.
To the day of this writing, it did not support fully rotary encoders (used here as the volume button), but I was able to figure out how to tinker some code to do so.
Explanations on how rotary encoders communicate certainly helped (see e.g. [here](https://blog.sharedove.com/adisjugo/index.php/2020/05/10/using-ky-040-rotary-encoder-on-raspberry-pi-to-control-volume/)).
There seem to be a [plan]((https://github.com/gpiozero/gpiozero/pull/482)) to add that support to `gpiozero`.


## Custom classes

This is my first project using python and I got seduced enough by the ability to program classes easily that I decided to structure everything into classes.
I have thus defined three classes: `Player` (to play audio files), `Clock` (to tell the time and handle alarms) and `Box` (to handle how pressing or turning buttons influences the previous classes).

### Player

I created a class `Player` to create VLC players. These players are used to play audio files.  
Although a single player can certainly be used, I am actually using several players in this project.
For now, I chose to rely on two of them: one to play musics, and one to play system sounds (including the time).
Using several players allows you to play several tracks simultaneously.
For instance, I chose that the reading of the time happens without pausing the music (since my wife listens to guided mediation, it makes sense; over Hard Rock, probably not).

(more to come)

### Clock

(more to come)

### Box

(more to come)


## How to handle physical inputs?

(to come)


### Push buttons

(to come)


### Rotary encoder

(to come)


### Infra red transmitter

(to come)

