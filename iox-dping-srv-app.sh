#!/bin/sh
#
# Wrapper to launch the python app inside the C93xx container 
# (non blocking and avoid any output to be sent to stdin/stderr
#
# Copyright 11/2021 Cisco Systems /  jpujol@cisco.com
#
/usr/bin/python3 /usr/bin/iox-dping-srv-app.py >/tmp/iox-dping-srv-app.log 2>&1
