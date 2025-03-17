# Linux setup for the project

This is the folder where I put all the info related to everything soft related that is not part of the python code.


## Getting the system ready

### Installation of the OS using desktop computer

The official doc is this one: https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system

On a desktop computer Linux, I first installed rpi-imager:

```
sudo apt install rpi-imager
```

or 

```
sudo dnf install rpi-imager
```


Then I ran this software:

```
rpi-imager
```

I clicked on "CHOOSE OS", then selected Raspberry Pi OS (other) and then Raspberry Pi OS Lite (32-bits).

Note that the Pi Zero does not support 64 bits OS.

I then selected the correct storage ("CHOOSE STORAGE").

Note that my computer did not read the micro-sd card in its native reader, so I used an external card reader.

I clicked on EDIT settings and I do this:
- set hostname
- set username and passwd
- configure wireless LAN
- set local setting
- enable SSH (I used with public key)

Notes: 
- some of these settings did not seem to work as intended, but I show below how to fix the issues.

Then I clicked on "YES" to write the image of the OS on the micro-SD card.

I made sure to eject the micro-SD card properly.


### Activate Gadget mode

The so-called gadget mode allows one to SSH into the Pi directly using a USB cable, which is very convenient for setup as it makes it possible to copy paste code.

The setup used to be simple (https://howchoo.com/pi/raspberry-pi-gadget-mode), but with the latest release of the RPiOS based on Debian bookworm, this is no longer sufficient.
Nothing I tried worked, so I gave up setting that up before first run.


### Run the OS

I connected a screen and a keyboard to the Pi (required unless the gadget mode is working).

As I only have a single screen, I connected the HDMI cable to a HDMI video capture dongle, which generates a video flow I read in using Kamoso (Zoom works but it has a much poorer resolution and frame). I selected USB Video as the camera.

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

I also enabled the SSH server (using **Interface Options**), but perhaps that is not necessary if the step above during installation worked (I thought it did not hurt anyhow).

See end of file for trouble shooting.

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
# Disable Bluetooth (introduced by ALEX)
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
Note that if the wifi was configured while creating the OS image, it may be called "preconfigured".

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


### Set locales

Somehow my locales were not fine, so I just did:

```
sudo nano /etc/environment
```

and added

```
LC_ALL=en_US.UTF-8
LANG=en_US.UTF-8
LANGUAGE=en_US.UTF-8
```

I also did the same here:

```
sudo nano /etc/default/locale
```

Then I rebooted.
It is probably an overkill, but that worked.


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
# Enable audio (loads snd_bcm2835) (modified by ALEX)
dtparam=audio=off
```

I also added:

```
# Enable sound card (introduced by ALEX)
dtoverlay=hifiberry-dac
force_eeprom_read=0

# Disable HDMI audio (introduced by ALEX)
dtoverlay=vc4-kms-v3d,audio=off

# Enable power on / off from GPIO (introduced by ALEX).
dtoverlay=gpio-shutdown

# Enable debuging message in dmsg (introduced by ALEX)
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

Edit the paths in the file `main.py` if you username is not `pi`.

### Dependencies

The project requires to install `python3-vlc` (which is takes quite some time):

```
sudo apt install python3-vlc
```

Note: there is no need to install `vlc` directly (i.e. outside python, an even large set of files).

Also, very useful for debugging:

```
sudo apt install ipython3
```


### Automation using a systemd service

Once the Python script is done and works, it needs to be ran with systemd automatically after boot.

Any solution I read failed (due to difficulties related to pulseaudio and rights).

What has worked for me was an adaptation from https://github.com/torfsen/python-systemd-tutorial.

The idea is to write a service unit (see file `judsound.service` in this repo).

This file points to the python code and define where to right console outputs (although I am not sure that this works since I see instead console outputs in journalctl; see below).

Instead of using system-wide systemd service, I used the user one; i.e. I created a sim link to the service file in a newly created folder in home `.config/systemd/user/`.

So edit the file `judsound.service` to make sure that the paths are correct (update username if you username is not `pi`, and not to be mixed up with hostname).
Then copy the file `judsound.service` into the folder `physical_computing` and then do the following after replacing `[user]` by your username (and not the hostname):

```
mkdir -p ~/.config/systemd/user/
ln -s ~/physical_computing/judsound.service ~/.config/systemd/user/judsound.service
chown [user]:[user] ~/.config/systemd/user/judsound.service
chmod 0644 ~/.config/systemd/user/judsound.service
```

Then, I did:

```
systemctl --user start judsound.service
systemctl --user enable judsound.service
```

Check that things are ok here:

```
systemctl --user list-unit-files | grep judsound
```

Note that if you update `/physical_computing/judsound.service `, for the effect to be perceived in the running session, it is needed to do:

```
systemctl --user daemon-reload
systemctl --user stop judsound.service
systemctl --user disable judsound.service
ln -s ~/physical_computing/judsound.service ~/.config/systemd/user/judsound.service
chown [user]:[user] ~/.config/systemd/user/judsound.service
chmod 0644 ~/.config/systemd/user/judsound.service
systemctl --user enable judsound.service
systemctl --user start judsound.service
```

Since this service is handled by the systemd of the user, the user needs to be automatically active after reboot.

This can simply be done by calling:

```
sudo loginctl enable-linger $USER
```

Reboot.


## Troubleshooting

### Check that the Pyton program is working

```
python3 physical_computing/main.py 
```

### Checking that GPIOs are working

Check that the following does not result in any error:

```
ipython3
from gpiozero import Button
button = Button(22,bounce_time=0.1)

def press():
  print("pressed\n")

button.when_pressed = press
```

Note the this must be launched from your home folder or any other folder for which you have rights (but not from a system folder!).


### Checking that VLC is working

Try the following in a folder that contains e.g. the file `test.mp3`:

```
ipython3
import vlc
instance_vlc = vlc.Instance()
player = instance_vlc.media_player_new()
track = instance_vlc.media_new("test.mp3")
player.set_media(track)
player.audio_set_volume(20)
player.play()
```

If you here the music, then try pausing:

```
player.pause()
```

Try resuming:

```
player.play() # or player.pause()
```

Try stopping:

```
player.stop()
```

These tests showed that an error message I get does not impact behaviour...:

```
vlcpulse audio output error: PulseAudio server connection failure: Connection refused
```

### Sound issues

I had possible problems caused by a wrong sound card being used by systemd.
I did this to check which card(s) are setup:

```
alsactl info
aplay -l 
```

Since I used a HifiBerry miniAmp, I want HifiBerry there.
Initially, the HDMI driver was taking over, but I modified the dtoverlay setting accordingly and it should now be ok.


### Systemd service management

To check the status of the systemd services, I do:

```
systemctl --user list-unit-files
```

For the specific judsound.service:

```
systemctl --u status judsound.service
journalctl --user-unit judsound.service
```

Note the `-u` is required because it is a user-level service.

If the log gets too cluttered, you can reset it (forever):

```
sudo journalctl --rotate
sudo journalctl --vacuum-time=1s
```


To restart the service, I use:

```
systemctl --u restart judsound.service
```

### WIFI issues

Check that you detect wifi:

```
nmcli dev wifi list
```

If you router is not listed but should be, it could be a channel issue.
On router, try to change channel for 2.4 Ghz wifi and try again.
The list of allowed channel is shown here on the pi:

```
iwlist wlan0 freq
```

Some channel are not allowed with some country settings.
The country that maters for that seems to be the one shown here:

```
iw reg get
```

which you can change as this (here for germany):

```
sudo iw reg set DE
```

### SSH key issues
If you are using a wrong set of keys, without password authentification you may struggle to add the new key.
The easiest is simply to log in locally and then add the correct public keys there:

```
nano .ssh/authorized_keys
```

If there is a problem on the desktop side "Host identification has changed".
Just remove the line starting with the IP of the Pi in .ssh/known_hosts

### Log inspection

To check the log of the judsound system, I used to simply do:

```
journalctl | grep python
```
But this is no longer working...

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
