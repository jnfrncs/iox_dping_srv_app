FROM ubuntu:18.04 
RUN apt-get update -yq && apt-get install -yq python3 python3-pip && apt-get install -yq curl && apt-get install -yq iputils-ping
RUN python3 -m pip install bottle
RUN apt-get remove -yq python3-pip && apt-get clean
COPY iox-dping-srv-app.py /usr/bin/iox-dping-srv-app.py
COPY iox-dping-srv-app.sh /usr/bin/iox-dping-srv-app.sh
RUN chmod 777 /usr/bin/iox-dping-srv-app.sh
CMD /usr/bin/iox-dping-srv-app.sh
