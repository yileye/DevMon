#!/usr/lib/cgi-bin 
#############################################################################
#                                                                           #
#                DevMon (Ping) V0.4                                         #
#                                                                           #
#                                                                           #
# DevMon will is reloaded the config(DevMon.cfg) at the start of every      #
#   scan so live changes can be made/saved and then updated.                #
#                                                                           #
#                               DevMon Programmer: (Nate.Mccomb@gmail.com)  #
#############################################################################
#
import sys
import os
import requests
import time
import string
import datetime
import getpass #for pulling current username
import socket  #for pulling hostname
import smtplib #for sending emails
import logging
import logging.handlers
from time import sleep

#Var. Setup
IPList = []
IPNameList = []
IPFailed = []
FailedTime = []
EmailFailed = []
IPOnline = []
EmailList = []
StartTime = datetime.datetime.now().replace(microsecond=0)
WaitToSend = 10
UserName = getpass.getuser()
HostName = socket.gethostname()
EmailFrom = '%s' % (HostName)
SleepTime = 1
EmailUser = ''
EmailPass = ''
SMTPserver = 'smtp.gmail.com'
SMTPport = 587
DeviceCount = 0
PingTime = 0
SetupDone = False
#setup logger
LOG_FILENAME = '/var/tmp/DevMon.log'

logger = logging.getLogger('DevMon')
hdlr = logging.FileHandler(LOG_FILENAME)
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=200000,
                                               backupCount=3,
                                               )
logger.addHandler(handler)

logger.setLevel(logging.DEBUG)
#Print() is used to both print and Log to file
def Print(Text):
    global logger
    print Text
    logger.info(Text)
    
Print(' ')
Print(' ')
Print('DevMon Started @ %s' % (StartTime))
Print(' ')
#logger.info('Hello')

def ping(ip):
# Perform the ping using the system ping command (one ping only)
    global PingTime
    rawPingFile = os.popen('ping -c 1 -W 1 %s' % (ip))
    rawPingData = rawPingFile.readlines()
    rawPingFile.close()
    # Extract the ping time
    if len(rawPingData) < 2:
        # Failed to find a DNS resolution or route
        failed = True
        latency = 0
    else:
        index = rawPingData[1].find('time=')
        if index == -1:
            # Ping failed or timed-out
            failed = True
            latency = 0
        else:
            # We have a ping time, isolate it and convert to a number
            failed = False
            latency = rawPingData[1][index + 5:]
            latency = latency[:latency.find(' ')]
            latency = float(latency)
    # Set our outputs
    if failed:
        # Could not ping
        #print '%s Failed' % (ip[:-1])
        return False
    else:
        # Ping stored in latency in milliseconds
        PingTime = latency
    #print ' %f ms \b' % (latency)
        return True
     

def find_element_in_list(element,list_element):
        try:
            index_element=list_element.index(element)
            return index_element
        except ValueError:
            return -1


def OpenConfig(filename):
    UpdateFound = False
    emailadd = None
    AddDeviceCount = 0
    global DeviceCount
    #print 'Checking for updates in %s' % (filename)
    
    # Read in Config file line for line
    with open(os.path.expanduser(filename)) as f:
        for line in f:
            line = line.rstrip('\n')
            line = line.rstrip('\r')
            #Skip lines that start with '#'
            if not line.startswith('#'):
                if ':' in line:
                    #Look for EMAIL: in line to update send Email addresses
                    if 'EMAILTO:' in line.upper():
                        global EmailList
                        if EmailList != (line[8:]):
                            if UpdateFound == False:
                                Print('*' * 79)
                            #Return a list of Email addresses to send to
                            UpdateFound = True
                            EmailList = (line[8:])
                            EmailAddressList = EmailList.split(";")
                            Print( '    **** Updated - %s Email Address(s): (To:)   \/   \/' % len(EmailAddressList))
                            for line in EmailAddressList:
                                Print('\t \t \t %s' % line)
                    #Look for WAIT: in line to update wait to send
                    elif 'WAIT:' in line.upper():
                        global WaitToSend
                        if WaitToSend != (line[5:]):
                            if UpdateFound == False:
                                Print( '*' * 79)
                            OldWait = WaitToSend
                            WaitToSend = (line[5:])
                            UpdateFound = True
                            Print( '    **** Updated - Device timeout before sending email: from %s to %s Sec.' % (OldWait, WaitToSend))
                    #Look for SMTPserver: in line 
                    elif 'SMTPSERVER:' in line.upper():
                        global SMTPserver
                        if SMTPserver != (line[11:]):
                            if UpdateFound == False:
                                Print( '*' * 79)
                            SMTPserver = (line[11:])
                            UpdateFound = True
                            Print( '    **** Updated - SMTP Server Set to: %s' % (SMTPserver))
                    #Look for SMTPserver: in line 
                    elif 'SMTPPORT:' in line.upper():
                        global SMTPport
                        if SMTPport != (line[9:]):
                            if UpdateFound == False:
                                Print( '*' * 79)
                            SMTPport = (line[9:])
                            UpdateFound = True
                            Print( '    **** Updated - SMTP Port Set to: %s'% (str(SMTPport).rstrip('\r')))
		    #Look for EmailUser: in line to update SMTP User
                    elif 'EMAILUSER:' in line.upper():
                        global EmailUser
                        if EmailUser != (line[10:]):
                            if UpdateFound == False:
                                Print( '*' * 79)
                            EmailUser = (line[10:])
                            UpdateFound = True
                            Print( '    **** Updated - Email User Name Set to: %s' % (EmailUser))
                    #Look for EmailPass: in line to update SMTP User
                    elif 'EMAILPASS:' in line.upper():
                        global EmailPass
                        if EmailPass != (line[10:]):
                            if UpdateFound == False:
                                Print( '*' * 79)
                            EmailPass = (line[10:])
                            UpdateFound = True
                            Print( '    **** Updated - Email User Password ********')
                    #Look for Sleep: in line to update Sleep time
                    elif 'SLEEP:' in line.upper():
                        global SleepTime
                        if SleepTime != (line[6:]):
                            if UpdateFound == False:
                                Print( '*' * 79)
                            OldSleep = SleepTime
                            SleepTime = (line[6:])
                            UpdateFound = True
                            Print( '    **** Updated - Sleep Time: From %s to %s Sec.' % (str(OldSleep).rstrip('\r'),str(SleepTime).rstrip('\r')))
            
                else:
                    #Look in IPList to see if we have already added IP in 'Line'
                    IPADD = ''
                    IPNAME = 'Device%s' % (DeviceCount)
                    line = line.split("|")
                    if len(line) > 0:
                        IPADD = line[0]
                    if len(line) > 1:
                        IPNAME = line[1]
                    
                    if find_element_in_list(IPADD,IPList) == -1:
                        #IP was not found in 'IPList
			DeviceCount += 1
                        AddDeviceCount += 1
                        if UpdateFound == False:
                                Print( '*' * 79)
                        Print( "    **** Adding:%-*s **With the Name:%s" % (15,IPADD,IPNAME))
                        IPList.append(IPADD)
                        IPNameList.append(IPNAME)
                        global FailedTime
                        IPFailed.append(ScanTime)
                        EmailFailed.append(None)
                        IPOnline.append(ScanTime)
                        FailedTime.append(ScanTime)
                        UpdateFound = True
    
    if UpdateFound == True:
        Print("    **** %d Total Devices, %d New Devices Added" % (DeviceCount,AddDeviceCount))
        Print('    **** Updates found in %s - Done' % (filename))
        Print('*' * 79)
    




def send_email(TEXT,STATUS):
            

            gmail_user = EmailUser
            gmail_pwd = EmailPass
            FROM = EmailUser #'DevMon@GMX.com'
            TO = EmailList #must be a list
            SUBJECT = "%s %s" % (EmailFrom,STATUS)
            #TEXT = "Testing sending mail using gmail servers"
            #print FROM
            #print TO
            
            # Prepare actual message
            message = """\From: <%s>\nTo: %s\nSubject: %s\n\n%s
            """ % (FROM, TO, SUBJECT, TEXT)
            #add the tail of the log file to the email
            Tail = '\n\n** Last %s Lines from Log:\n\n' % str((DeviceCount * 2) + 2)
            for line in tail('/var/tmp/DevMon.log',str((DeviceCount * 2) + 2)):
                Tail = Tail + '         ' + line
	    #Debug SMTP \/ ###########
	    #print SMTPserver
	    #print SMTPport
	    #print message               
            ##########################
	    try:
                #server = smtplib.SMTP(SERVER) 
                server = smtplib.SMTP(SMTPserver, SMTPport) #or port 465 doesn't seem to work!
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_pwd)
                server.sendmail(FROM, TO.split(";"), message + Tail)
                #server.quit()
                server.close()
                Print( '               ****   Successfully Sent Email   ****')
            except:
                Print( '                ****   Failed to Send Email   ****')
                e = sys.exc_info()[0]
                Print('  ~~~ Error: %s ~~~ ' % e)

def tail(f, n):
  stdin,stdout = os.popen2("tail -n "+n+" "+f)
  stdin.close()
  lines = stdout.readlines(); stdout.close()
  return lines[:]

if __name__ == "__main__":
    while(True):
        #get the current time for the start of this scan 
        ScanTime = datetime.datetime.now().replace(microsecond=0) 
        #Load in config settings
        try:
            OpenConfig('/home/pi/DevMon/DevMon.cfg')
        except:
            if SetupDone == False:
                e = sys.exc_info()[1]
                Print('  ~~~ Error: %s ~~~ ' % e)
            OpenConfig('%s/DevMon.cfg' % (os.path.dirname(os.path.abspath(__file__))))  
        SetupDone = True
        #ping each device listed in config
        for item in IPList:
            Status = ping(item)
            if Status == True: # Ping came back good
                # set the time for the last good ping
                IPOnline[find_element_in_list(item,IPList)] = ScanTime
                
                if IPOnline[find_element_in_list(item,IPList)] != None:
                    # Find if this device has gone offline since DevMon started
                    LastOffLine = ''
                    
                    if IPFailed[find_element_in_list(item,IPList)] != None and StartTime != IPFailed[find_element_in_list(item,IPList)]:
                        LastoffLine = '\n             *Went Offline for %-15s \t@ %s' % (FailedTime[find_element_in_list(item,IPList)],IPFailed[find_element_in_list(item,IPList)] - FailedTime[find_element_in_list(item,IPList)])
                    else:
                        LastoffLine = ' '
                    # get the uptime for this device
                    Print( '%s - Up Time For: %-12s\t(%s)\t Responsed in:%.3fms %s' % ((IPOnline[find_element_in_list(item,IPList)] - IPFailed[find_element_in_list(item,IPList)]),IPNameList[find_element_in_list(item,IPList)], item, PingTime, LastoffLine))
		    # this device is now back online so send an online email only if we send an offline email
                    if EmailFailed[find_element_in_list(item,IPList)] == True:
                        Print( '*' * 79)
                        Print( '****        Send Email for %s(%s) - Online        ****' % (IPNameList[find_element_in_list(item,IPList)],item))
                        send_email('%s(%s) Is back online after being down %s seconds. Device went down @ %s '% (IPNameList[find_element_in_list(item,IPList)],(item), (FailedTime[find_element_in_list(item,IPList)]) ,IPOnline[find_element_in_list(item,IPList)]), (" - %s(%s) Now online (Down Time:%s)" % (IPNameList[find_element_in_list(item,IPList)],item,(FailedTime[find_element_in_list(item,IPList)]))))
                        Print( '*' * 79)
                        EmailFailed[find_element_in_list(item,IPList)] = False
                
            else: # Ping came back bad
                # set the time for the last bad ping
                IPFailed[find_element_in_list(item,IPList)] = ScanTime
                if IPFailed[find_element_in_list(item,IPList)] != None:
                    TimeOffLine = (IPFailed[find_element_in_list(item,IPList)] - IPOnline[find_element_in_list(item,IPList)])
                    Print( '%-15s\t(%s) - Offline for: %s \t@ %s' % (IPNameList[find_element_in_list(item,IPList)],item, TimeOffLine, IPOnline[find_element_in_list(item,IPList)]))
                    FailedTime[find_element_in_list(item,IPList)] = TimeOffLine
                    if datetime.timedelta(seconds=int(WaitToSend)) <=  TimeOffLine and EmailFailed[find_element_in_list(item,IPList)] != True:
                        Print( '*' * 79)
                        Print( '    **** %s has been offline for more then %s seconds ****' % (IPNameList[find_element_in_list(item,IPList)], WaitToSend))
                        Print( '       **** Send Email For %s(%s) Not Responding  ****' % (IPNameList[find_element_in_list(item,IPList)],item))
                        send_email('%s(%s) Went offline for more then %s Seconds @ %s' % (IPNameList[find_element_in_list(item,IPList)],item, WaitToSend, IPFailed[find_element_in_list(item,IPList)]), " - %s(%s) Has gone offline" % (IPNameList[find_element_in_list(item,IPList)],item))
                        Print( '*' * 79)
                        EmailFailed[find_element_in_list(item,IPList)] = True
        Print('')
        Print( '-' * 79)
        sleep(int(SleepTime))
        Print('\n\n')
        Print('\t  Current System Time: %s' % ScanTime)
