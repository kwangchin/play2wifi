#!/usr/bin/python
# -*- coding: utf-8 -*-

##############################################################################################################
# This scripts allows video streams as input to xbmc.                                                        #
#
# ---------------------------------------------------------------------------------------------------------- #
#                                                                                                            #
# Author: Andreas Ruppen                                                                                     #
# License: GPL                                                                                               #
# This program is free software; you can redistribute it and/or modify                                       #
#   it under the terms of the GNU General Public License as published by                                     #
#   the Free Software Foundation; either version 2 of the License, or                                        #
#   (at your option) any later version.                                                                      #
#                                                                                                            #
#   This program is distributed in the hope that it will be useful,                                          #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of                                           #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                            #
#   GNU General Public License for more details.                                                             #
#                                                                                                            #
#   You should have received a copy of the GNU General Public License                                        #
#   along with this program; if not, write to the                                                            #
#   Free Software Foundation, Inc.,                                                                          #
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.                                                #
##############################################################################################################

import sys, os
import logging

if float(sys.version[:3])<3.0:
    import ConfigParser
else: 
    import configparser as ConfigParser
import optparse
import subprocess
import urllib
import xml.dom.minidom

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from datetime import datetime, date
import time


class Play2wifi():
    '''
    classdocs
    '''


    def __init__(self):
        """Do some initialization stuff"""
        self.__mylogger = logging.getLogger("Play2wifi")
        self.__mylogger.setLevel(logging.DEBUG)
        fformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        cformatter = logging.Formatter('%(name)s - %(message)s')
        fileh = logging.FileHandler(filename='Play2wifi.log', mode='w')
        fileh.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        
        fileh.setFormatter(fformatter)
        console.setFormatter(cformatter)
        
        
        self.__mylogger.addHandler(fileh)
        self.__mylogger.addHandler(console)
        
        self.__cwd = os.getcwd()
        self.__mylogger.debug("\033[1;33m"+self.__cwd+"\033[0m")

        
        self.__mylogger.debug("Reading general configuration from play2wifi.cfg")
        self.__play2wifiConfig = ConfigParser.SafeConfigParser()
        self.__play2wifiConfig.read("play2wifi.cfg")
        self.__xbmcserver = self.__play2wifiConfig.get("XBMC", "xbmcserver")
        self.__xbmcport = self.__play2wifiConfig.get("XBMC", "xbmcport")
        self.__play2wifiport = self.__play2wifiConfig.get("Play2wifi", "play2wifiport")
        
        self.__xmbc = "http://"+self.__xbmcserver+":"+self.__xbmcport+"/xbmcCmds/"
        self.__myurlopener = MyURLOpener()
        
        
    def main(self):
        """This is the main method"""
        #define xml interaction with xbmc webserver
        self.__myurlopener.open(self.__xmbc+"xbmcHttp?command=setresponseformat%28webheader;false;webfooter;false;header;%3Cxml%3E;footer;%3C/xml%3E;opentag;%3Ctag%3E;closetag;%3C/tag%3E;closefinaltag;true%29")
        #Create the ServerPart
        #factory = protocol.ServerFactory()
        #factory = Factory()
        #Use play2wifiProtocol as Protocol
        #factory.protocol = Play2wifiProtocol#(self.__xbmcserver, self.__xbmcport)
        #factory.serv = self.__xbmcserver
        #factory.port = self.__xbmcport
        reactor.listenTCP(int(self.__play2wifiport), Play2WifiProtocolFactory(self.__xbmcserver, self.__xbmcport))
        #endpoint = TCP4ServerEndpoint(reactor, 8007)
        #endpoint.listen(factory)
        reactor.run()
        
    def getArguments(self, argv):
        usage = "usage: %prog [options]"
        parser = optparse.OptionParser(usage=usage, version="%prog 1.0")
        parser.add_option("-s", "--server", 
                          action="store", dest="server", type="string",  metavar="server",
                          help="host where xmbc is running")
        parser.add_option("-p", "--port", 
                          action="store", dest="port", type="string",  metavar="port",
                          help="port on which xbmc web server is listening")
       

        (options, args) = parser.parse_args()
        
        if options.server is not None:
            self.__xbmcserver = options.server
        if options.port is not None:
            self.__xbmcport = options.port
        self.main()

class MyURLOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'
    

    
class Play2wifiProtocol(Protocol):
    """This is the play2wifi protocol and the core of this script"""
    def __init__(self):
        
        # define a Handler which writes INFO messages or higher to the sys.stderr other are CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
        self.__mylogger = logging.getLogger("Play2wifiProtocol")
        self.__mylogger.setLevel(logging.DEBUG)
        fformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        cformatter = logging.Formatter('%(name)s - %(message)s')
        fileh = logging.FileHandler(filename='Play2wifi.log', mode='a')
        fileh.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        
        fileh.setFormatter(fformatter)
        console.setFormatter(cformatter)
        
        
        self.__mylogger.addHandler(fileh)
        self.__mylogger.addHandler(console)
        
        
    def dataReceived(self, data):
        """Defines the protocol"""
        try:
            self.__xbmcserver = self.factory.serv
            self.__xbmcport = self.factory.port
            self.__xbmc = "http://"+self.__xbmcserver+":"+self.__xbmcport+"/xbmcCmds/"
            self.__currentPlayingUri = self.__xbmc+"xbmcHttp?command=GetCurrentlyPlaying"
            self.__stopCmd = self.__xbmc+"xbmcHTTP?command=Stop()"
            self.__pauseCmd = self.__xbmc+"xbmcHTTP?command=Pause()"
            self.__myurlopener =  MyURLOpener()
            
            answer = ""
            if(data.find('Content-Location')>-1):#This contains the video URI
                self.playMedia(data)
                answer = "HTTP/1.1 200 OK"
                answer += "\r\nDate: "+self.getDateTime()
                answer += "\r\nContent-Length: 0"
                answer += "\r\n\r\n"
            elif(data.find('stop')>-1): #ends the conversation. Send back the current position.
                duration, position = self.getPlayerPosition()
                self.__myurlopener.open(self.__stopCmd)
                content = "duration: "+duration+".360107"
                content += "\r\nposition: "+position+".749201"
                clength = len(bytes(content))
                answer = "HTTP/1.1 200 OK"
                answer += "\r\nDate: "+self.getDateTime()
                answer += "\r\nContent-Length: "+str(clength)
                answer +="\r\n\r\n"
                answer += content
            elif(data.find('GET /scrub') > -1): #gets polled every second for the actual position
                duration, position = self.getPlayerPosition()
                content = "duration: "+duration+".360107"
                content += "\r\nposition: "+position+".749201"
                clength = len(bytes(content))
                answer = "HTTP/1.1 200 OK"
                answer += "\r\nDate: "+self.getDateTime()
                answer += "\r\nContent-Length: "+str(clength)
                answer +="\r\n\r\n"
                answer += content
            elif(data.find('reverse')>-1): #don't know exactly what this is doing ;-)
                answer = "HTTP/1.1 101 Switching Protocols"
                answer += "\r\nDate: "+self.getDateTime()
                answer += "\r\nUpgrade: PTTH/1.0"
                answer += "\r\nConnection: Upgrade"
                answer += "\r\n\r\n"
            elif(data.find('POST /rate')>-1):# play is 1.000000, pause is 0.000000
                #if(self.isPause()): #not really necessary since there is only one xbmc command
                lasttime = self.factory.lasttime
                now = time.time()
                self.factory.lasttime = now 
                if((lasttime is not None) and (now-lasttime>1)):
                    self.__mylogger.debug("Lasttime is: "+str(now-lasttime))
                    self.__myurlopener.open(self.__pauseCmd)
                answer = "HTTP/1.1 200 OK"
                answer += "\r\nDate: "+self.getDateTime()
                answer += "\r\nContent-Length: 0"
                answer += "\r\n\r\n"
            elif(data.find('POST /scrub') > -1):#seeking on the iPad
                self.setPlayerPosition(data)
                answer = "HTTP/1.1 200 OK"
                answer += "\r\nDate: "+self.getDateTime()
                answer += "\r\nContent-Length: 0"
                answer += "\r\n\r\n"
            else:
                logging.debug("got something else")
                logging.debug(data)
                
            if(answer is not ""):
                self.transport.write(answer)
            else:#this case should not happen :-D
                self.transport.write(data)
        except IOError:
            self.transport.write(data)
            
        
    def getDateTime(self):
        """Returns the time for the Date header"""
        today =datetime.now()
        datestr = today.strftime("%a, %d %b %Y %H:%M:%S")
        return datestr+" GMT"
    
    def getPlayerPosition(self):
        """Returns the actual playing position in XBMC"""
        
        try:
            mydom=xml.dom.minidom.parse(self.__myurlopener.open(self.__currentPlayingUri))
            root = mydom.childNodes[0]
            duration = ""
            durationString = ""
            position = ""
            positionString = ""
            for item in root.getElementsByTagName('tag'):
                child = item.firstChild.data
                #self.__mylogger.debug("Child from CurrentPlaying XML: "+child)
                if(child.find('Time')>-1):
                    sub1 = 'Time:'
                    position = child.split(sub1)[1]
                    self.__mylogger.debug("CurrentPlaying Length: "+position)
                elif(child.find('Duration') > -1):
                    sub1 = 'Duration:'
                    duration = child.split(sub1)[1]
                    self.__mylogger.debug("CurrentPlaying Position: "+duration)
                    
            if(duration != "" and position != ""):
                durationSplit = duration.split(":")
                positionSplit = position.split(":")
                durationString = str(int(durationSplit[0])*60+int(durationSplit[1]))
                positionString = str(int(positionSplit[0])*60+int(positionSplit[1]))
        except xml.parsers.expat.ExpatError:
                self.__mylogger.error("Could not parse current position xml")
        except IOError:
                self.__mylogger.error("IO EXception")
        
        return durationString, positionString
    
    def setPlayerPosition(self, data):
        sub1 = 'POST /scrub?position='
        sub2 = ' HTTP/1.1'
        finalPosition = data.split(sub1)[-1].split(sub2)[0]
        duration, position = self.getPlayerPosition()
        if(duration != ""):
            self.__mylogger.debug("Position before Seeking: "+duration)
            percentage = str(round(float(finalPosition)*100/float(duration)))
            self.__mylogger.debug("Will set player position to: "+percentage)
            self.__myurlopener.open(self.__xbmc+"xbmcHttp?command=SeekPercentage("+percentage+")")
            
        
            
    def playMedia(self, data):
        sub1 = 'Content-Location: '
        sub2 = '\nStart-Position: '
        location = data.split(sub1)[-1].split(sub2)[0]
        self.__mylogger.debug("Found the following Media to play: "+location)
        if location.find("googlevideo") > 0:
            url_data = urllib.urlencode(dict(url=location))
            ret = urllib.urlopen("http://tinyurl.com/api-create.php", data=url_data).read().strip()
            subprocess.call(["xbmc-send", "-a", "PlayMedia("+ret+")"], cwd="./", stdout=open("/dev/null", 'w'))
        else:
            subprocess.call(["xbmc-send", "-a", "PlayMedia("+location+")"], cwd="./", stdout=open("/dev/null", 'w'))

        
    def isPause(self, data):
        sub1 = '/rate?value='
        sub2 = ' HTTP/1.1'
        command = data.split(sub1)[-1].split(sub2)[0] # play is 1.000000, pause is 0.000000
        #TODO compare time
        lasttime = self.factory.lasttime
        now = time.time()
        self.factory.lasttime = now 
        if((lasttime is not None) and (now-lasttime>1)):
            self.__mylogger.debug("Lasttime is: "+str(now-lasttime))
            if(command == '1.000000'):
                return False
            elif(command == '0.000000'):
                return True
        
class Play2WifiProtocolFactory(Factory):
    """Factory Class for creating protocols"""
    
    protocol = Play2wifiProtocol
    
    def __init__(self, serv, port):
        self.serv = serv
        self.port = port
        self.lasttime = None
    
    
if __name__ == "__main__":
    ap = Play2wifi()
    ap.getArguments(sys.argv[1:])
        
