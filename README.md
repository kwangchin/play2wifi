# Installation Instructions #

This short page will guide you through the installation and use of the script.

## Info ##
Special thanks goes to Erica Sadun who released AirPlayer earlier this month. This was the software which let me discover the world of AirPlay


## Before you start ##

What is currently working:
  * Select a video/podcast/serie on the iThing (should also work in other iThings) and launch it on xbmc.
  * Play/Pause of the video through the controls on the iThing.
  * Switch back the video to the iThing.
  * Seeking in the timeline on the iThing.

What is currently not working:
  * Playback of Youtube videos. XBMC cannot handle the files.

Known Bugs:
  * When resuming the video back to the iThing it's paused even if the interface say it's not. This need some more work.
  * When launching a video for the second time xmbc asks wheter it should resume or start over again. Don't know how to fix that.

## What you need to know ##
Actually there is no code in the in the SVN. All the code is just a Python scripts which launches a server on the port 22555. Some work would need to be done here again in order to make a nice xmbc-plugin. But I have know knowledge in this domain.

The choosen approach in the python is script may not be the simplest one. In fact, the script depends upon the Twisted framework. I spend most time decoding and describing the protocol.

## Needed software ##
In orther to make everything work there some additional software is needed. The airplay discovery is based upon Bonjour (avahi). Therefore install the package avahi-daemon (`apt-get install avahi-daemon`) Furthermore the scripts calls xmbc through either
  * xbmc-send (install `apt-get install xbmc-eventclients-xbmc-send`) or
  * through the web interface (be sure to setup Web interface in XBMC on port XXXX)
Furhtermore python needs the Twisted framwork. It can be installed with `apt-get install python-twisted`.

## Installation ##
This hack was developed on Ubuntu (but should also work on other linux systems). Therefore installation istruction will be for linux only (Ubuntu). It should be possible to port the code to other platform since it's only python. However I have no ideas about the dependencies (avahi for example).
  * Copy the `play2wifi.service` script to `/etc/avahi/services/` and restart avahi `service avahi-daemon restart`.
  * Adapt the play2wifi.cfg script (at least line 3 to whatever port xbmc web interface is running). This parameter can also be overwritten with the `-p` startup parameter.
  * Launch the script `python play2wifi.py`.
  * Launch a video/podcast on the iThing and switch it over to xbmc.