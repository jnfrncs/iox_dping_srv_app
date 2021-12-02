# iox_dping_srv_app

Provide a single point of control to initiate calls to iox_c91xx_ping_app running in containers on Cisco C9120-30 APs

(see iox-ping-app project https://github.com/jnfrncs/iox_c91xx_ping_app)

This application has been written for python3 and can be used on a local machine or embedded into a container package and installed on a Catalyst switch for example.
Requires bottle and urllib python libraries

Copyright 11/2021 Cisco Systems / jpujol@cisco.com

![iox-dping-srv-app schema](https://github.com/jnfrncs/iox_dping_srv_app/blob/main/dping_app.jpg)

# How to start it: 

% python iox-dping-srv-app.py 

Bottle v0.12.19 server starting up (using WSGIRefServer())...

Listening on http://0.0.0.0:8011/

Hit Ctrl-C to quit.

# help :
curl http://localhost:8011/dping/help
	
> help
	
/dping/help	"This help"

/dping/list	"List APs in the group"

/dping/add/<AP IP@>	"Add an AP (IP@) into the group"

/dping/remove/<AP IP@>	"remove an AP (IP@) from the group"

/dping/target/<target IP@>	"ping target IP@ from all APs in the group"

/dping/target/<target IP@>/size/<packet size>	"ping target IP@ (w/ packet size) from all APs in the group"
	
/dping/target/<target IP@>/ttl/<TTL value>	"ping target IP@ (w/ TTL value) from all APs in the group"
  
  # result :
  curl http://http://localhost:8011/dping/target/172.16.90.9/ttl/5
  
  Result	Result	"[Success]: 172.16.90.9 is 100% reachable from all available APs (pkt size=56 B, TTL=5)"
  score	100
  score	100
	
# Creating a docker container :
	$ docker build -t iox-dping-app .
	
	$ docker save iox-dping-app -o iox-dping-app.tar
	
# Installing the container to a Cisco Catalyst 9300 :
	
	1/ copy the file into the local usb flash :
	
	copy sftp://<srv>/iox-dping-app/iox-dping-app.tar usbflash1:
	
	2/ configure the network 
	
	IOS# configure terminal
	
	app-hosting appid ioxdping
	
 	  app-vnic AppGigabitEthernet trunk
	
  		vlan <accessvlan> guest-interface 0
	
   		  guest-ipaddress <container IP> netmask <container net mask>
	
 	  app-default-gateway <container net defaultgtw> guest-interface 0
	
	3/ install and start the container
	app-hosting install appid ioxdping package usbflash1:iox-dping-app.tar
	
	app-hosting activate appid ioxdping
	
	app-hosting start appid ioxdping


	
	
	
