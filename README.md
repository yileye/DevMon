DevMon
======

DevMon - Device Monitor (Ping)

DevMon can be used to monitor multiple devices by pinging them. If a device goes offline for XX seconds, DevMon will then send an email out to the list of E-Mail addresses. DevMon uses the Gmail SMTP server to send Emails, so a valid Gmail account is required and needs to be added to the .cfg file.

**Install**

cd ~

git clone --depth=1 https://github.com/NateMccomb/DevMon.git



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
