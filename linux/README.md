# Linux setup for the project

This is the folder where I put all the info related to everything soft related that is not part of the python code.


## Getting the system ready

### Installation of the OS using desktop computer

The official doc is this one: https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system

On a desktop computer Linux (Kubuntu), I first installed rpi-imager:

```
sudo apt install rpi-imager
```

Then I ran this software:

```
rpi-imager
```

I clicked on "CHOOSE OS", then selected Raspberry Pi OS (other) and then Raspberry Pi OS Lite (32-bits).

Note that the Pi Zero does not support 64 bits OS.

I then selected the correct storage ("CHOOSE STORAGE").

Note that my computer did not read the micro-sd card in its native reader, so I used an external card reader.

Before clicking on "WRITE", I clicked on the little gear to set the following options:
- enable SSH (I used with public key)
- set username and passwd
- configure wireless LAN
- set local setting
- do not eject media when finished

Notes: 
- I did not set the hostname (default is good)
- some of these settings did not seem to work as intended, but I show below how to fix the issues.

Then I clicked on "WRITE" to write the image of the OS on the micro-SD card.

I made sure to eject the micro-SD card properly.


### Activate Gadget mode

The so-called gadget mode allows one to SSH into the Pi directly using a USB cable, which is very convenient for setup as it makes it possible to copy paste code.

The setup used to be simple (https://howchoo.com/pi/raspberry-pi-gadget-mode), but with the latest release of the RPiOS based on Debian bookworm, this is no longer sufficient.
Nothing I tried worked, so I gave up setting that up before first run.


### Run the OS

I connected a screen and a keyboard to the Pi (required unless the gadget mode is working).

As I only have a single screen, I connected the HDMI cable to a HDMI video capture dongle, which generates a video flow I read in using Zoom (selecting USB Video as the camera).

I put the micro-SD card into the Pi and powered up the Pi.
In principle it should be possible to connect the Pi to the USB cable only to power it up, but in my case, there is too much gear, so I plug in the electric cable.

I logged in using the credential set above (this worked).


### General configuration (WIFI and SSH server)

I used the following to set a few things using a GUI:

```
sudo raspi-config
```

My WIFI was not working, as shown by the following which did not return anything:

```
hostname -I
```

So I used `raspi-config` to fix that (in menu **System Options**).

I also enabled the SSH server (using **Interface Options**), but perhaps that is no necessary if the step above during installation worked (I thought it did not hurt anyhow).

Then I rebooted and logged in.

I checked that the wifi was working.
Since it did, I connected via SSH into the Pi from my desktop computer using the IP shown using `hostname -I`:

```
ssh pi@192.168.X.Z
```

From this point on, I did not use the keyboard connected to the Pi.


### Remove bluetooth

Since I don't need bluetooth I removed it (it avoids various messages in the logs and perhaps save energy):

```
sudo apt-get purge bluez -y
sudo apt-get autoremove -y
```

Also I disabled it at the hardware level using:

```
sudo nano /boot/firmware/config.txt 

```

For this, I added:

```
# Disable Bluetooth
dtoverlay=disable-bt
```


### Restrict SSH connections

To secure the system, I made sure that log in can only use secure keys.

The installer had already dispatched my secure key, but otherwise I would have used the following to copy my secure key:

```
ssh-copy-id -i .ssh/id_rsa.pub pi@192.168.X.Z
```

Notes: 
- this should be run from the desktop computer, not from the Pi
- do not use `sudo`
- replace X and Z by their values provided by `hostname -I`

Then, I secured SSHD by making only local connections possible by creating a `sshd.config` file:

```
sudo nano /etc/sshd.config
```

I pasted the following (with the correct X value):

```
Match Address *,!192.168.X.0/24
AuthenticationMethods publickey
PasswordAuthentication no
PubkeyAuthentication yes
```


### Make IP static

To make the IP static, using a `dhcpcd.conf` file no longer works since Bookworm is now using NetworkManager.

Instead, I first did:

```
sudo nmcli -p connection show
```

This showed me the name of my network connection (my WiFis SSID).

Then, I ran the following after changing "MyBox" by the name of my network connection and 192.168.X.Z by the fixed IP adress I wanted to use and 192.168.X.ZZ for the gateway and network addresses I wanted to use (e.g. 192.168.X.254):

```
sudo nmcli c mod "MyBox" ipv4.addresses 192.168.X.Z/24 ipv4.method manual
sudo nmcli con mod "MyBox" ipv4.gateway 192.168.X.ZZ
sudo nmcli con mod "MyBox" ipv4.dns 192.168.X.ZZ
```

To update the IP of the Pi, I then did:

```
sudo nmcli c down "MyBox" && sudo nmcli c up "MyBox"
```

It broke the running SSH connection (expected), so I then reconnected using the new IP address.

For this, I created a SSH config profile mon my desktop computer to directly log into my Pi.

So I created a profile here:

```
nano .ssh/config
```

I pasted the following using the correct IP:

```
Host pi
  HostName 192.168.X.Z
  User pi
```

Then I try to connect using:

```
ssh pi
```

Note that as the profile was used before, I got an error message:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

I simply followed the instruction from the message (i.e. run `ssh-keygen -f ...`) and tried again.
It worked-


### Update everything

I tried to update everything:

```
sudo apt update
sudo apt upgrade
```

but in my case, the installer was fresh and no update existed.


## Settings specific to the project

### Set the Pi config file

I then configured the Pi for the project: 

```
sudo nano /boot/firmware/config.txt 

```

I commented the following to inactivate onboard audio:

```
# Enable audio (loads snd_bcm2835) (removed by ALEX)
# dtparam=audio=on
```

I also added:

```
# enable sound card (introduced by ALEX)
dtoverlay=hifiberry-dac
force_eeprom_read=0

# enable power on / off from GPIO (introduced by ALEX).
dtoverlay=gpio-shutdown

# enable debuging message in dmsg (introduced by ALEX)
dtdebug=1
```

I saved, exited, rebooted and logged in again.


### Copy the Python code of the project

In the file explorer on my desktop computer, I connected to the Pi using the address:

```
sftp://pi/
```

In `home/pi`, I copied:

- the folder `playlist_day` containing the musics for the day mode
- the folder `playlist_night` containing the musics for the night mode
- the folder `playlist_system` containing all the sound for the system

In `home/pi`, create:

- a folder `physical_computing` and place there all the python files of the project should be placed


### Required dependencies

I installed vlc (which is takes quite some time):

```
sudo apt install python3-vlc
```

Note: there is no need to install `vlc` directly (i.e. outside python, an even large set of files).


### Automation using a systemd service

Once the Python script is done and works, it needs to be ran with systemd automatically after boot.

Any solution I read failed (due to difficulties related to pulseaudio and rights).

What has worked for me was an adaptation from https://github.com/torfsen/python-systemd-tutorial.

The idea is to write a service unit (see file `judsound.service` in this repo).

This file points to the python code and define where to right console outputs (although I am not sure that this works since I see instead console outputs in journalctl; see below).

Instead of using system-wide systemd service, I used the user one; i.e. I created a sim link to the service file in a newly created folder `.config/systemd/user/`.

Then, I did:

```
systemctl --user enable judsound.service
systemctl --user start judsound.service
```

Since this is handled by the systemd of the user (pi), the user needs to be automatically active after reboot.
This can simply be done by calling:

```
sudo loginctl enable-linger $USER
```


## Troubleshooting

### Service management

To check the status of the systemd service, I do:

```
systemctl --u status judsound.service
```

Note the `-u` is required because it is a user-level service.

To restart the service, just I use:

```
systemctl --u restart judsound.service
```

### Log inspection

To check the log of the judsound system, I simply do:

```
journalctl | grep python
```

Note: there is no need for sudo since `judsound.service` is a user-level service.

It should report all the `print()` calls from python.

The following can also be useful:

```
dmesg
journalctl -p 3 -x
```


## Upgrading the OS

Rule #1: never jump releases.

I tried once and it broke sudo and I could not do anything but formatting...
