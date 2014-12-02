DevMon
======

DevMon - Device Monitor (Ping)

DevMon can be used to monitor multiple devices by pinging them. If a device goes offline for XX seconds, DevMon will then send an email out to the list of E-Mail addresses. DevMon uses the Gmail SMTP server to send Emails, so a valid Gmail account is required and needs to be added to the .cfg file.


**First Time Installing**

sudo apt-get update

sudo apt-get upgrade

sudo apt-get install python-requests

git clone --depth=1 https://github.com/NateMccomb/DevMon.git /var/tmp/DevMon

cp /var/tmp/DevMon/ ~/DevMon

**Update DevMon.py Only** 
This way .cfg doesn't get overridden

cp /var/tmp/DevMon/ /var/tmp/DevMonOld/

git clone --depth=1 https://github.com/NateMccomb/DevMon.git /var/tmp/DevMon

cp /var/tmp/DevMon/DevMon.py ~/DevMon/

**Edit Config**

sudo nano DevMon/DevMon.cfg



**Run DevMon from command line(CLI)**

sudo python DevMon/DevMon.py 



**View Log file**

tail /var/tmp/DevMon.log -n 200



**Run at startup**

sudo crontab -u root -e



**Add to the end of crontab**

@reboot /bin/sleep 30; sudo python /home/pi/DevMon/DevMon.py
