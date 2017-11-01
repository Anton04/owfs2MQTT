FROM python:2.7

MAINTAINER Anton Gustafsson  <anton.gustafsson@ri.se>

#RUN apt-get update

##################################################
# Set environment variables                      #
##################################################



##################################################
# Add app user                                   #
##################################################

#RUN useradd --create-home --home-dir /home/app --shell /bin/bash app


##################################################
# Install tools                                  #
##################################################
RUN pip install paho-mqtt terminaltables

COPY ownet/python ownet

WORKDIR "./ownet"

RUN ["python", "setup.py","install"]

#####SPECIFIC#####

USER root


#EXPOSE 

COPY 1W2MQTT-docker.py 1W2MQTT.py 


CMD [ "python", "./1W2MQTT.py" ]
