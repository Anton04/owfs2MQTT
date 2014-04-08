#!/usr/bin/python


import sys

import mosquitto 
import os
from time import gmtime, strftime, time, localtime, sleep
import thread
#import asyncore
from math import fabs
#import daemon
import ownet
import psutil
from subprocess import call
#import socket
import json
 
class MessageHandler(mosquitto.Mosquitto):

	def __init__(self,ip = "localhost", port = 1883, clientId = "owfs2MQTT", user = None, password = None, prefix = "hardware/1-wire/"):
		mosquitto.Mosquitto.__init__(self,clientId)
	
		self.prefix = prefix
		self.ip = ip
    		self.port = port
    		self.clientId = clientId
		self.user = user
    		self.password = password
    		
    		if user != None:
    			self.username_pw_set(user,password)

    		print "Connecting"
    		self.connect(ip)
    		self.subscribe(self.prefix + "#", 0)
    		self.on_connect = self.mqtt_on_connect
    		self.on_message = self.mqtt_on_message
    		
    		return
    		
    	def mqtt_on_connect(self, selfX,mosq, result):
    		print "MQTT connected!"
    		self.subscribe(self.prefic + "#", 0)
    
  	def mqtt_on_message(self, selfX,mosq, msg):
    		print("RECIEVED MQTT MESSAGE: "+msg.topic + " " + str(msg.payload))
    	
    		return
    	
    	def ControlLoop(self):
    		# schedule the client loop to handle messages, etc.
      		while(True):
      			self.loop()
        		sleep(0.1)

    	def SendEvent(self,timestamp,event_type,id,value):
    		topic = self.prefix + "/" + id
    		params = {"time":timestamp,"type":event_type,"value":value}
    		packet = json.dumps(params)
    		self.publish(topic, packet, 1)
    	

class OwEventGuard(MessageHandler):
	
	root = None
	alarms = None
	current_state = {}

	#Temp fix.
	PolledDevices = ["29.3C460C000000"]

	def __init__(self,ip = "localhost", port = 1883, clientId = "owfs2MQTT", user = None, password = None, prefix = "hardware/1-wire/",owserver = ("127.0.0.1",4304)):
		
		#Init MQTT connection
		MessageHandler.__init__(self,ip, port, clientId, user, password, prefix)
		
		#Other
		self.VerifiedConnection = time()
		self.SensorVerification = {}

		#self.StartKeepAliveProc()

		self.owport = owserver[0]
		self.owadress = owserver[1]
	
		print "starting"
		
		self.failcount = 0
		self.BusID = "81.4EC92F000000"		
		#self.BussVerifier = ownet.Sensor("uncached/12.E5F66C000000","localhost",4304)
		#self.CheckOwserver()

		self.root = ownet.Sensor("/",self.owadress,self.owport)
		self.alarms = ownet.Sensor("/alarm",self.owadress,self.owport)

		self.temp_sensor_list = []		

		#self.init_sensors()
		
		self.devices_initiated = True
		return
		
    
  	def mqtt_on_message(self, selfX,mosq, msg):
    		#try:
    		if True:
    			print("RECIEVED MQTT MESSAGE: "+msg.topic + " " + str(msg.payload))
    			topics = msg.topic.split("/")

		#Handle set commands here.
	
    		return
    


	def init_sensors(self):
		#self.temp_sensor_list = []

		for e in self.root.sensors():
			print e	
			if hasattr(e, 'type'):
				id = str(e.family) +"."+ str(e.id)
				print id
				sensor = ownet.Sensor("/uncached/"+id,self.owadress,self.owport)
				if not hasattr(sensor,"type"):
					continue
				type = sensor.type
				
				if type == "DS2406":
					#Set latch alarm
					#sensor.set_alarm = 311
					#sensor.set_alarm = 311
					#if sensor.set_alarm != 311:
					#	sensor.set_alarm = 311
					#	print "Retrying"
					value = sensor.sensed_BYTE
					timestamp = time()
					sensor.latch_BYTE = 255
					event_type = "DIGITAL_SENSOR"
				elif type == "DS2408":
					#Set latch alarm
					#sensor.set_alarm = 133333333
					value = sensor.sensed_BYTE
					timestamp = time()
					sensor.latch_BYTE = 255
					event_type = "DIGITAL_SENSOR"
				elif type == "DS18B20":
					#Set latch alarm
					#sensor.templow = -100
					#sensor.temphigh = 100
					value = sensor.temperature
					timestamp = time()
					self.temp_sensor_list.append((timestamp,id))
					event_type = "TEMPERATURE"
				elif type == "DS1420":
					self.BusID = id
					continue
				else:
					continue

				#print type
				#print value
				self.Update(timestamp,event_type, id,value)


		#print self.current_state

		return
		
	#Check new state of devices in alarm mode and reset the alarm state. 
	def CheckAlarms(self):

		self.alarms = ownet.Sensor("/alarm",self.owadress,self.owport)
		alarms = self.alarms.entryList()
		count = 0
		checks = 0		

		for s in alarms:
			#print s
			sensor = ownet.Sensor("/uncached/" + s,self.owadress,self.owport)
			if not hasattr(sensor, 'type'):
				continue
				
			id = str(sensor.family) +"."+ str(sensor.id)
			type = sensor.type
					
			if type == "DS2406":
				value = sensor.sensed_BYTE
				timestamp = time()
				sensor.latch_BYTE = 255
				event_type = "DIGITAL_SENSOR"
				checks += 1
			elif type == "DS2408":
				value = sensor.sensed_BYTE
				timestamp = time()
				sensor.latch_BYTE = 255
				event_type = "DIGITAL_SENSOR"
				#print type
				#print value
				checks += 1
			else:
				continue

			#Keep track of errors
			if value == "":
				print "Connection lost"
				self.failcount += 1
				continue
			
			#Data read OK! Update. 
			self.failcount = 0
			self.VerifiedConnection = time()
			self.SensorVerification[id] = self.VerifiedConnection
	
			count += self.Update(timestamp,event_type,id,value)

		#If no checks have been prefomed do one. 
		if False:
			if checks == 0:
	        		if self.BussVerifier.sensed_BYTE != "":
        	        		self.VerifiedConnection = time()
                     		else:
                			self.failcount += 1

			print "Alarms: %i"%count

			if self.failcount:
				print "Current failcount %i" % self.failcount
	
		return count

	def Update(self,timestamp,event_type,id,value,threshold = 0.0):

		#Update the sensor list.
		HEventGuardEventGuardasChanged = self.UpdateSensorList(id,timestamp,value,threshold)

		if HasChanged:
			#print "%s\t%s\t%s\t%s"%(timestamp,event_type,"1W"+id,str(value))
			self.SendEvent(timestamp,event_type,id,value)
			
			return True

		return False
		

	def CheckTemperatures(self,threshold = 0.0):
		#Find the oldest value.
		
		if len(self.temp_sensor_list) == 0:
			return False
		self.temp_sensor_list.sort()
		#print "lista"
		#print self.temp_sensor_list
		#print self.temp_sensor_list[-1]
		(_,id) =  self.temp_sensor_list[-1]
		#print id 

		s = ownet.Sensor("/uncached/" + id, self.owadress,self.owport)
		value = s.temperature
		timestamp = time()
		self.temp_sensor_list[-1] = (timestamp,id)
		return self.Update(timestamp,"TEMPERATURE",id,value,threshold)
		

	def UpdateSensorList(self,id,timestamp,new_value,threshold = 0.0):
		#Has the sensor been read before?
		if not self.current_state.has_key(id):
			#New sensor. Add it.
			self.current_state.update({id:(timestamp,new_value)})
			return True

		#Has the value changed?
		(old_timestamp,old_value) = self.current_state[id]
		if old_value == new_value:
			return False

		#Some readings are not considered changed until a threshold value is reached. 
		if fabs(old_value - new_value) < threshold:
			return False

		#YES - update new value
		self.current_state.update({id:(timestamp,new_value)})
		return True
			
	def loop(self):
		if not self.devices_initiated:
			self.looping = False
			return

		self.looping = True

		while(self.looping):
			try:
				self.CheckAlarms()
				self.CheckTemperatures(0.2)
				sleep(0.1)
			except Exception,e:
				print e
				self.CheckOwserver()
				sleep(1)	

			if self.failcount > 1:
				print "Failcount threshhold reached"
				self.RestoreOwserver()	
		return

	def CheckOwserver(self):
		try:
			for f in range(0,2):
				#print self.owadress,self.owport
				#sensor = ownet.Sensor("uncached/12.E5F66C000000/sensed.BYTE",self.owadress,self.owport)

				if self.BussVerifier.sensed_BYTE != "":
					self.VerifiedConnection = time()
					return
				else:
					print "Failed to verify connection."

			print "Owserver online but not working!"

		except Exception,e:
			print "Unable to verify connection. Process might not be running"
			print e

		self.RestoreOwserver()

		return
		
	def RestoreOwserver(self,pidfile = "/var/run/owfs/owserver.pid"):
		try:
			owpidfile = open(pidfile,"r")
    			owpid = int(owpidfile.readline())
			print "Owserver pid should be: %i" % owpid
			
			if psutil.pid_exists(owpid):
				print "Terminating faulty owserver process..."
				owserver = psutil.Process(owpid)
				#owserver.send_signal(9)

			else:
				print "Process does not exists!"
		except:
			print "Unable to find pid file"

		try:
			print "Trying to restart it..."
			call(["/etc/init.d/owserver","restart"])
			
		except Exception,e:
			print "Something went wrong when restarting owserver"		
			print e
							
	def KeepAliveProcedure(self,intervall = 20):

		print "Starting keep alive procedure"

		while True:
			Now = time()
			Delta = Now - self.VerifiedConnection

			#print Delta

			if Delta > intervall:
				print "EventGuard stalled restarting owserver"
				call(["/etc/init.d/owserver","restart"])
			
			if Delta > (intervall/2):
				print "%i seconds since last verified reading!" % Delta

			sleep(intervall)

		return

	def StartKeepAliveProc(self):
		thread.start_new_thread(self.KeepAliveProcedure,())
		return

def	RunGuard():
	EventGuard = OwEventGuard(('localhost', 34343), '1Wire:001')

	#g.say(g.CurrentTime() + '\tLOGICAL EVENT\t1wire event guard\tStarted\n\r')

	#Start new thread for server connunication
	#thread.start_new_thread(EventGuard.loop,())

	#Start a thread that monitors if things goes wrong and locks up. 
	#OwEventGuard.StartKeepAliveProc()
	while(1):
		EventGuard.loop()

if __name__ == '__main__':
	#with daemon.DaemonContext():
	RunGuard()

