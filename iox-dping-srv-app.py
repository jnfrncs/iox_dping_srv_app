#
# iox-dping-app : Distributed ping app
#
# distributes simultaneous ping requests from various sources (APs)
# with optional MTU/TTL option
#
# This small app server is running either on a local machine or in a container
# (could be installed in a container on a Cisco Catalyst switch)
# to be started from the associated shell wrapper
#
# requires the presence of iox-ping-app (container) running on
# at least one Catalyst C9120-30 AP
#
# Copyright 11/2021 Cisco Systems /  jpujol@cisco.com
# 
#

from bottle import route, run
import time
from threading import Thread, Event
from urllib import request
import json

PING_AP_PORT = 8010 # port open for ping service on APs
"""
Should match the configuration in the iox-ping-app (running on APs, with TCP port = PING_AP_PORT)
"""
REACHABLE_AP_VALUE="ping"
STATS_AP_VALUE="stats"
REACHABLE_AP_CODE="Reachable"
UNREACHABLE_AP_CODE="Unreachable"
DPING_SERVICE_PORT = 8011 # local port for requests

DFLT_PKT_SIZE="56" # default ICMP packet size
DFLT_TTL="255" # default ICMP TTL

RESPONSE_HEADER  = [('Content-type','text/html')]
HELPMSG = { "/dping/help" : "This help",
           "/dping/list" : "List APs in the group",
           "/dping/add/<AP IP@>" : "Add an AP (IP@) into the group",
           "/dping/remove/<AP IP@>" : "remove an AP (IP@) from the group",
           "/dping/target/<target IP@>" : "ping target IP@ from all APs in the group",
           "/dping/target/<target IP@>/size/<packet size>" : "ping target IP@ (w/ packet size) from all APs in the group",
           "/dping/target/<target IP@>/ttl/<TTL value>" : "ping target IP@ (w/ TTL value) from all APs in the group"}

agent_aps = [  ]

"""
    manage parallel calls to the list of APs (agent_aps)
"""
class ThreadwRV(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        # print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
            
    def join(self, *args):
        Thread.join(self, *args)
        return self._return
"""
    request sent to each AP (iox-ping-app running in a container)
"""
def urlFetch(url):
        reply = ""
        try:
            response = request.urlopen(url, timeout=5)
        except request.URLError as e:
            print("Error when fetching " + url)
            print(e.reason)
            exit(-1)
        reply = response.read()
        # print('urlQuery response:' + str(reply))
        return(reply)

"""
    final message with results and stats
"""
def report(target_ip, pktsize, ttl, agent_aps, nreachables, nrequests, minRtt, avgRtt, maxRtt):
    if nrequests == 0:
        message = "[Error]: no available agent AP for testing."
        print(message)
        return { "Result" : message , "code" : -1 }
    average = int(nreachables / nrequests * 100)
    if average == 100:
        message  = "[Success]: " + target_ip  + " is 100% reachable from all available APs (pkt size=" + pktsize + " B, TTL=" + ttl + ")"
    elif average < 100 and average > 0: 
        message = "[Partial success]: " + target_ip + " is reachable from " + average, "of all available APs (", nreachables, ")  (pkt size=" + pktsize + " B, TTL=" + ttl + ")"
    else:
        message = "[Failure]: " + target_ip + " is not reachable from any AP  (pkt size=" + pktsize + " B, TTL=" + ttl + ")"
        average = 0
    if nrequests > 0 and nreachables > 0:
        stats = { 'minRtt' : minRtt, 'avgRtt': avgRtt, 'maxRtt':maxRtt}
    return(message, average, stats)
   
"""
    Statistics (% success, summarization of rtt values from each ap)
"""
def analyze(replies):
    nrequests = 0
    nreachables = 0
    nstats = 0
    minRtt = { 'val':100.0, 'ap':''}
    maxRtt = { 'val':0.0, 'ap':''}
    avgRtt = 0.0
    failures = []
    for ap in replies.keys():
        if replies[ap] != None:
            nrequests +=1
            jreply = json.loads(replies[ap])
            if jreply[REACHABLE_AP_VALUE] == REACHABLE_AP_CODE:
                nreachables += 1
                if STATS_AP_VALUE in jreply.keys():
                    nstats += 1
                    min = float(jreply[STATS_AP_VALUE]['min'])
                    if min < minRtt['val']:
                        minRtt['val'] = round(min,2)
                        minRtt['ap'] = ap
                    avgRtt += float(jreply[STATS_AP_VALUE]['avg'])
                    max = float(jreply[STATS_AP_VALUE]['max'])
                    if max > maxRtt['val']:
                        maxRtt['val'] = round(max,2)
                        maxRtt['ap'] = ap
            else:
                print(" Result from:", ap , "is: ", jreply['ping'] )
                if jreply['ping'] == UNREACHABLE_AP_CODE:
                    failures.append(ap)
        else:
            print("Warning:", ap, "AP unavailable for testing.")
    if nstats != 0:
        avgRtt = round(avgRtt / nstats,2)
    return(nrequests, nreachables, minRtt, avgRtt, maxRtt, failures)

"""
    main procedure executed for all types of ping requests
"""
def ping_thread(target_ip, pktsize, ttl, agent_aps):
    
    replies = {}
    twrv = {}
    
    if len(agent_aps) < 1:
        message = "[Failure]: empty list of APs. Add agent APs first. Try /dping/help."
        print(message)
        return { "Result" : message,  "score" : "-1" }
    
    if ttl != DFLT_TTL:
        ping_opt = "/ttl/" + ttl
    else:
        ping_opt = "/size/" + pktsize
    
    for ap in agent_aps:
        url = "http://" + ap + ":" + str(PING_AP_PORT) + "/ping/" + target_ip + ping_opt
        twrv[ap] = ThreadwRV(target=urlFetch, args=(url,))
        twrv[ap].start()
        print("> AP[", ap, "] : sent.")
    print("done.")
    
    for ap in agent_aps:
        replies[ap] = twrv[ap].join(3)
        
    print("got results...")
        
    nrequests, nreachables, minRtt, avgRtt, maxRtt, failures = analyze(replies)
    
    message, average, stats = report(target_ip, pktsize, ttl, agent_aps, nreachables, nrequests, minRtt, avgRtt, maxRtt)
    
    print(message)
    return { "Result" : message , "score" : average, 'failures': failures, 'stats' : stats}

"""
    Supported URLs with corresponding action
"""
@route('/dping/help')
def group():
    
    return { "help" : HELPMSG }

@route('/dping/list')
def glist():
    return { "AP list (ping from)" : agent_aps }

@route('/dping/add/<ap_ip>')
def add(ap_ip):
    global agent_aps
    ap_ip = str(ap_ip)
    if ap_ip not in agent_aps:
        agent_aps.append(ap_ip)
    return { "new AP list (ping from)" : agent_aps }

@route('/dping/remove/<ap_ip>')
def remove(ap_ip):
    global agent_aps
    ap_ip = str(ap_ip)
    if ap_ip in agent_aps:
        agent_aps.remove(ap_ip)
    return { "new AP list (ping from)" : agent_aps }

@route('/dping/target/<target_ip>')
def dping(target_ip):
    target_ip = str(target_ip)
    return(ping_thread(target_ip, DFLT_PKT_SIZE, DFLT_TTL, agent_aps))

@route('/dping/target/<target_ip>/size/<pktsize>')
def dping_size(target_ip, pktsize):
    target_ip = str(target_ip)
    pktsize = str(pktsize)
    return(ping_thread(target_ip, pktsize, DFLT_TTL, agent_aps))

@route('/dping/target/<target_ip>/ttl/<ttl>')
def dping_ttl(target_ip, ttl):
    target_ip = str(target_ip)
    ttl = str(ttl)
    return(ping_thread(target_ip, DFLT_PKT_SIZE, ttl, agent_aps))

if __name__ == '__main__' :       

    run(host='0.0.0.0', port=DPING_SERVICE_PORT)  
    
