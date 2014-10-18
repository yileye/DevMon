#!/usr/lib/cgi-bin 
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
    rawPingFile = os.popen('ping -c 1 %s' % (ip))
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
        #print '%s @ %f ms' % (ip,latency)
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
                                Print('*' * 70)
                            #Return a list of Email addresses to send to
                            UpdateFound = True
                            EmailList = (line[8:])
                            Print( '    **** Updated - Email (To:) Address: %s' % EmailList)
                    #Look for WAIT: in line to update wait to send
                    elif 'WAIT:' in line.upper():
                        global WaitToSend
                        if WaitToSend != (line[5:]):
                            if UpdateFound == False:
                                Print( '*' * 70)
                            OldWait = WaitToSend
                            WaitToSend = (line[5:])
                            UpdateFound = True
                            Print( '    **** Updated - Wait to send failed ping email from %s to %s Sec.' % (OldWait, WaitToSend))
                    #Look for EmailUser: in line to update SNMP User
                    elif 'EMAILUSER:' in line.upper():
                        global EmailUser
                        if EmailUser != (line[10:]):
                            if UpdateFound == False:
                                Print( '*' * 70)
                            EmailUser = (line[10:])
                            UpdateFound = True
                            Print( '    **** Updated - Email User Name to %s' % (EmailUser))
                    #Look for EmailPass: in line to update SNMP User
                    elif 'EMAILPASS:' in line.upper():
                        global EmailPass
                        if EmailPass != (line[10:]):
                            if UpdateFound == False:
                                Print( '*' * 70)
                            EmailPass = (line[10:])
                            UpdateFound = True
                            Print( '    **** Updated - Email User Password')
                    #Look for Sleep: in line to update Sleep time
                    elif 'SLEEP:' in line.upper():
                        global SleepTime
                        if SleepTime != (line[6:]):
                            if UpdateFound == False:
                                Print( '*' * 70)
                            OldSleep = SleepTime
                            SleepTime = (line[6:])
                            UpdateFound = True
                            Print( '    **** Updated - Sleep Time From %s to %s Sec.' % (str(OldSleep).rstrip('\r'),str(SleepTime).rstrip('\r')))
            
                else:
                    #Look in IPList to see if we have already added IP in 'Line'
                    
                    if find_element_in_list(line,IPList) == -1:
                        #IP was not found in 'IPList
                        if UpdateFound == False:
                                Print( '*' * 70)
                        Print( "    **** Adding :%s" % (line))
                        IPList.append(line)
                        global FailedTime
                        IPFailed.append(ScanTime)
                        EmailFailed.append(None)
                        IPOnline.append(ScanTime)
                        FailedTime.append(ScanTime)
                        UpdateFound = True
    
    if UpdateFound == True:
        Print( '    **** Updates found in %s - Done' % (filename))
        Print('*' * 70)
    




def send_email(TEXT,STATUS):
            

            gmail_user = EmailUser
            gmail_pwd = EmailPass
            FROM = 'DevMon@gmail.com'
            TO = EmailList #must be a list
            SUBJECT = "%s %s" % (EmailFrom,STATUS)
            #TEXT = "Testing sending mail using gmail servers"
            #print FROM
            #print TO
            
            # Prepare actual message
            message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (FROM, TO, SUBJECT, TEXT)
            try:
                #server = smtplib.SMTP(SERVER) 
                server = smtplib.SMTP("smtp.gmail.com", 587) 
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_pwd)
                server.sendmail(FROM, TO.split(";"), message)
                #server.quit()
                server.close()
                Print( '               ****   Successfully Sent Email   ****')
            except:
                Print( '                ****   Failed to Send Email   ****')



if __name__ == "__main__":
    while(True):
        #get the current time for the start of this scan 
        ScanTime = datetime.datetime.now().replace(microsecond=0) 
        #Load in config settings
        OpenConfig('%s/DevMon.cfg' % (os.path.dirname(os.path.abspath(__file__))))  
        
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
                        LastoffLine = ' *Went Offline Last @ %s for %s' % (IPFailed[find_element_in_list(item,IPList)],FailedTime[find_element_in_list(item,IPList)])
                    else:
                        LastoffLine = ' '
                    # get the uptime for this device
                    Print( '%s - Up Time for: %s %s' % ((IPOnline[find_element_in_list(item,IPList)] - IPFailed[find_element_in_list(item,IPList)]), item, LastoffLine))
                    # this device is now back online so send an online email only if we send an offline email
                    if EmailFailed[find_element_in_list(item,IPList)] == True:
                        Print( '*' * 70)
                        Print( '****        Send Email for %s - Online        ****' % (item))
                        send_email('%s Is Back Online After %s Sec. of Being Down @ %s '% ((item), (FailedTime[find_element_in_list(item,IPList)]) ,IPOnline[find_element_in_list(item,IPList)]), (" - %s Now Online" % (item)))
                        Print( '*' * 70)
                        EmailFailed[find_element_in_list(item,IPList)] = False
                
            else: # Ping came back bad
                # set the time for the last bad ping
                IPFailed[find_element_in_list(item,IPList)] = ScanTime
                if IPFailed[find_element_in_list(item,IPList)] != None:
                    TimeOffLine = (IPFailed[find_element_in_list(item,IPList)] - IPOnline[find_element_in_list(item,IPList)])
                    Print( '%s - Offline for: %s @ %s' % (item, TimeOffLine, IPOnline[find_element_in_list(item,IPList)]))
                    FailedTime[find_element_in_list(item,IPList)] = TimeOffLine
                    if datetime.timedelta(seconds=int(WaitToSend)) <=  TimeOffLine and EmailFailed[find_element_in_list(item,IPList)] != True:
                        Print( '*' * 70)
                        Print( '    **** %s has been offline for more then %s Sec. ****' % (item, WaitToSend))
                        Print( '    ****        Send Failed Email for %s          ****' % (item))
                        send_email('%s Went offline for more then %s Sec. @ %s' % (item, WaitToSend, IPFailed[find_element_in_list(item,IPList)]), " - %s Went Offline" % (item))
                        Print( '*' * 70)
                        EmailFailed[find_element_in_list(item,IPList)] = True

        Print( '-' * 42)
        sleep(int(SleepTime))
        
