#! /usr/bin/env python

'''

This script monitors any kind of stream, in this case Radio Valencia's
Icecast stream. Makes an entry in rv_stream_tester_log.txt whenever the
state of the stream changes (goes up or goes down) and keeps track of
uptime, downtime and number of outages. 

Ideally would be run from more than one location to rule out local internet
issues.

Tested only on Python 2 but should work fine in Python 3.

-Wrybread 5/4/2020


'''

import os, sys
import time
import socket

#import colorama # pip install colorama

try:
    # Python 3
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from urllib2 import urlopen





# the URL of the stream to monitor
url = "http://live.str3am.com:3010/live"


# Set the timeout for the stream. Somewhere between .5
# and 2 seconds makes sense.
timeout = 1





#######################
## helper functions
#######################

# format the timestamp
def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# convert seconds to days:hours:minutes:seconds
def elapsed(secs):

    days = secs//86400
    hours = (secs - days*86400)//3600
    minutes = (secs - days*86400 - hours*3600)//60
    seconds = secs - days*86400 - hours*3600 - minutes*60    

    # this will print "2:05:02:30" (days:hours:mins:seconds)
    o=""
    if secs > 60:
        if secs > 86400:    o+= "%s:" % days
        if secs > 3600:     o+= "%02d:" % hours
        if secs > 60:    o+= "%02d:" % minutes
        o+= "%02d" % seconds
    else:
        o = "%s seconds" % seconds
    return o


# output to log file and console. Spacer param adds extra hard return, add_summary adds total uptime and downtime.
last_msg_type = None
def write(msg, msg_type, spacer=0, add_summary=1):

    global last_msg_type
    
    #totals = "%s outages: %s uptime / %s downtime" % ( total_outages , elapsed(total_uptime), elapsed(total_downtime) )
    totals = "%s uptime / %s downtime" % ( elapsed(total_uptime), elapsed(total_downtime) )
    output = "%s: %s" % (timestamp(), msg)
    if add_summary: output += " (%s)" % totals
        
    #print (output) # will print to the console constantly

    if msg_type == "log" or msg_type != last_msg_type: # print every log message
    
        if spacer: output = "\r\n%s" % output # adds a spacer 
        print (output) # will print to the console only when status changes
        h = open(error_log, "a")
        h.write(output + "\r\n")
        h.close()
    
    last_msg_type = msg_type    



# possibly add colored output at some point
#colorama.init()
#print(colorama.Fore.YELLOW + 'some red text')
#import termcolor
#print(termcolor.colored('Hello, World!', 'green', 'on_red'), "asdf")


#################
##  script vars
#################

# the output log
current_directory = os.path.dirname(os.path.realpath(__file__)) # so the output log is in same directory as script
error_log = os.path.join(current_directory, "rv_stream_tester_log.txt")

tmp_file="output.mp3"
total_uptime=0
total_downtime=0
total_outages=0
last_result_time=time.time()
last_result_type=None
last_success_time=0
first_run=1

# set the timeout rate for urllib
socket.setdefaulttimeout(timeout)

write("Monitoring %s with a timeout of %s seconds" % (url, timeout), "log", spacer=1, add_summary=0)
write("Logging to %s" % error_log, "log2", spacer=0, add_summary=0)

##############################################
## run the test forever (or until control-c)
##############################################

while True:

    # delete the temp file, otherwise it'll get huge. Could just redirect to null but this allows further troubleshooting
    try: os.unlink(tmp_file)
    except: pass

    try:

        req = urlopen(url)
        downloaded = 0
        CHUNK = 50 * 1024 # download about 200k of the stream at a time 
        with open(tmp_file, 'wb') as fp:
            
            while True:
                chunk = req.read(CHUNK)
                downloaded += len(chunk)
                if not chunk:
                    raise ValueError("No chunk was downloaded!")
                    break
                fp.write(chunk)
                
                # download was a success! Keep track of totals and log it
                total_uptime += int(time.time() - last_result_time)

                if last_result_type == "error":
                    # it's back up after an outage, so figure out how long it was down
                    d = int(time.time() - last_success_time) # number of seconds it was down
                    msg = "Up after %s" % elapsed(d)
                else:                 
                    msg = "Stream is up!"
                    add_spacer=0

                if first_run: write(msg, "success", add_summary=0) # don't add summary on first run
                else: write(msg, "success")
                
                last_result_type = "success"
                last_success_time = time.time()
                last_result_time = time.time()

    except KeyboardInterrupt:
        # closing the program, write a final report
        msg = "Done logging."
        write(msg, "log")
        #time.sleep(3) # pause so can read from console before exiting
        sys.exit()
            
    except Exception as e:
        # download failed, the stream is down! Keep track of totals and log it  
        total_downtime += int(time.time() - last_result_time)

        if last_result_type == "success":
            # this is a new outage (could trigger email or txt here)
            total_outages+=1
        
        msg = "Down (#%s) (%s)" % (total_outages, str(e) )
        write(msg, "error", spacer=1)

        last_result_time = time.time()
        last_result_type = "error"
        time.sleep(1)
        
    first_run=0




