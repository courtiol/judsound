## Getting the system ready

### Installation of the OS using desktop computer

The official doc is this one: https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system

On a desktop computer running Ubuntu, I first installed rpi-imager:

```
sudo apt install rpi-imager
```

Then I ran this software:

```
rpi-imager
```

I clicked on "Choose Device", then selected Raspberry Pi OS (other) and then Raspberry Pi OS Lite (32-bits).

Note that the Pi Zero does not support 64 bits OS.

I then selected the correct storage ("Choose Storage").

Note that my computer did not read the micro-sd card in its native reader, so I put the card in a sd card and the sd card in a USB adapter.

Before clicking on "Write", I clicked on the little gear to set all the following options:
- hostname = pi
- enable SSH with public key authentification
- set username and passwd
- configure wireless LAN

Then I clicked on "Write" to write the image of the OS on the micro-SD card.


### Setting the systemd service

Once the Python script is done and works, it needs to be ran with systemd automatically after boot.

Any solution I read failed (due to difficulties related to pulseaudio and rights).

What has worked for me was an adaptation from https://github.com/torfsen/python-systemd-tutorial.

The idea is to write a service unit (see file `judsound.service` in this repo).

This file points to the python code and define where to right console outputs (although I am not sure that this works since I see instead console outputs in journalctl; see below).

Instead of using system-wide systemd service, I used the user one; i.e. I created a sim link to the service file in a newly created folder `.config/systemd/user/`.

Then, do

```
systemctl --user enable judsound.service
systemctl --user start judsound.service
```

Since this is handled by the systemd of the user (pi), the user needs to be automatically active after reboot.
This can simply be done by calling:

```
sudo loginctl enable-linger $USER
```

### Upgrading the OS

Rule #1: never jump releases.
I tried once and it broke sudo and I could not do anything but formatting...

## Troubleshooting

### Service management

To check the status of the systemd servive, just do:

```
systemctl --u status judsound.service
```

Note the `-u` is required because it is a user-level service.

To restart the service, just do:

```
systemctl --u restart judsound.service
```

### Log inspection

To check the log of the judsound system, simply do:

```
journalctl | grep python
```

No need for sudo since we are dealing with a user-level service.

It should report all the `print()` calls from python.

The following can also be useful:

```
dmesg
```