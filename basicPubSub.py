'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import os
import pexpect
import sys
import logging
import time
import argparse
import boto3
import decimal
import json
import binascii
import Adafruit_ADS1x15
#import signal
import datetime
from decimal import * 

from pulsesensor import Pulsesensor

# Create an ADS1115 ADC (16-bit) instance.
adc = Adafruit_ADS1x15.ADS1115()

# Choose a gain of 1 for reading voltages from 0 to 4.09V.
# Or pick a different gain to change the range of voltages that are read:
#  - 2/3 = +/-6.144V
#  -   1 = +/-4.096V
#  -   2 = +/-2.048V
#  -   4 = +/-1.024V
#  -   8 = +/-0.512V
#  -  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
GAIN = 1
i=0
values = []
def heartBeat():
    global values
    time.sleep(0.5) 
    return ((adc.read_adc(0,gain= GAIN)))

	
AllowedActions = ['both', 'publish', 'subscribe']

# Note you can change the I2C address from its default (0x48), and/or the I2C
# bus by passing in these optional parameters:
adc = Adafruit_ADS1x15.ADS1015(address=0x48, busnum=1)


# *************************Sensor Tag **************************

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

def sensor_tag_init():
	global sensor_data
        sensor_data = [ [0,0,0] , [0,0,0] ]
        global temp 	
        bluetooth_adr ='54:6C:0E:53:18:6C' 
	global tool 
        tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
	tool.expect('\[LE\]>')
	print "Preparing to connect. You might need to press the side button..."
	tool.sendline('connect') # test for success of connect
	tool.expect('Connection successful.*\[LE\]>')
	tool.sendline('char-write-cmd 0x27 01')
	tool.expect('\[LE\]>')
	tool.sendline('char-write-cmd 0x3F 3F00') #00111111 00000000
	tool.expect('\[LE\]>')
	time_old = time.time()
        time_test = time.time()
        time.sleep(0.5)

def get_object_temp(raw_temp_bytes):
        raw_object_temp = int('0x' + raw_temp_bytes[1] + raw_temp_bytes[0], 16)
        object_temp_int = raw_object_temp >> 2 & 0x3FFF
        object_temp_celsius = round ( float(object_temp_int) * 0.03125, 1 )
        print("Temp: " + str(object_temp_celsius))
        return object_temp_celsius

def signedFromHex16(s):
        v = int(s,16)
        if not 0 <= v < 65536:
                raise ValueError, "Hex Number outside 16bit range"
        if (v >= 32768):
                v = v - 65536
        return v

def get_gyro_data(raw_move_bytes):
        str_gyro_x =  '0x' + raw_move_bytes[1] + raw_move_bytes[0]
        raw_gyro_x = signedFromHex16(str_gyro_x)
        gyro_x = round ( (raw_gyro_x * 1.0) / (32768/250), 0 )

        str_gyro_y = '0x' + raw_move_bytes[3] + raw_move_bytes[2]
        raw_gyro_y = signedFromHex16(str_gyro_y)
        gyro_y = round ( (raw_gyro_y * 1.0) / (32768/250), 0 )

        str_gyro_z = '0x' + raw_move_bytes[5] + raw_move_bytes[4]
        raw_gyro_z = signedFromHex16(str_gyro_z)
        gyro_z = round ( (raw_gyro_z * 1.0) / (32768/250), 0 )

        raw_gyro = [raw_gyro_x, raw_gyro_y, raw_gyro_z]
        gyro_data = [gyro_x, gyro_y, gyro_z]
	print("Gyro Data: " + str(gyro_data))

        return gyro_data

def get_acc_data(raw_move_bytes):
        str_acc_x =  '0x' + raw_move_bytes[7] + raw_move_bytes[6]
        raw_acc_x = signedFromHex16(str_acc_x)
        acc_x = round ( ( (raw_acc_x * 1.0) / (32768/2) ), 0 )

        str_acc_y = '0x' + raw_move_bytes[9] + raw_move_bytes[8]
        raw_acc_y = signedFromHex16(str_acc_y)
        acc_y = round ( ( (raw_acc_y * 1.0) / (32768/2) ), 0 )

        str_acc_z = '0x' + raw_move_bytes[11] + raw_move_bytes[10]
        raw_acc_z = signedFromHex16(str_acc_z)
        acc_z = round ( ( (raw_acc_z * 1.0) / (32768/2) ), 0 )

        raw_acc = [raw_acc_x, raw_acc_y, raw_acc_z]
        acc_data = [acc_x, acc_y, acc_z]
 	print("Acc Data: " + str(acc_data))
        return acc_data

def get_sensor_data():
    tool.sendline('char-read-hnd 0x24')
    tool.expect('descriptor: .*')
    rval = tool.after.split()
    raw_temp_data = [ rval[1], rval[2], rval[3], rval[4] ]	
    temp= get_object_temp(raw_temp_data)
    return temp
    
def get_move_acc_data():
    tool.sendline('char-read-hnd 0x3C')
    tool.expect('descriptor: .*')
    rval = tool.after.split()
    raw_move_data = [ rval[1], rval[2], rval[3], rval[4], rval[5], rval[6], rval[7], rval[8], rval[9], rval[10], rval[11], rval[12], rval[13], rval[14], rval[15], rval[16], rval[17], rval[18] ]
    sensor_data[0] = get_acc_data(raw_move_data)
    sensor_data[1] = get_gyro_data(raw_move_data)
    return sensor_data[0]

def get_move_gyro_data():
    return sensor_data[1]                     

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


# Read in comand-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="Hello World!",
                    help="Message to publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, 443)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, 8883)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# ******************************** Pulse Sensor ***********************************
p = Pulsesensor()
p.startAsyncBPM()


# Publish to the same topic in a loop forever
loopCount = 0

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

table = dynamodb.Table('cmpeb-mobilehub-1483690200-RpiTable')

accelerometer = [ 0,0,0 ]
gyroscope = [ 0,0,0 ]
sensor_tag_init()

while True:
    if args.mode == 'both' or args.mode == 'publish':
        bpm = p.BPM
	loopCount +=1
        #serialNo=datetime.date.today().strftime("%B %d, %Y %I:%M:%S")
	temperature = get_sensor_data()
        accelerometer = get_move_acc_data()
        gyroscope = get_move_gyro_data()
 	serialNo = loopCount
	message = {}
	message = table.put_item(
	   Item={
		'serialNo': serialNo,
        	'pulse': bpm,
		'Temp': int(temperature),
                'ACCx': str(accelerometer[0]),
                'ACCy': str(accelerometer[1]),
                'ACCz': str(accelerometer[2]),
                'GYRx': str(gyroscope[0]),
                'GYRy': str(gyroscope[1]),
                'GYRz': str(gyroscope[2])
        	}
	)
        #message = {"PulseSensorValues": bpm,
        #           "ObjectTemperature" : bpm
        #            }
        #message = {"Temp": temperature, 
         #          "ACCx": accelerometer[0],
         #          "ACCy": accelerometer[1],
         #          "ACCz": accelerometer[2],
         #          "GYRx": gyroscope[0],
         #          "GYRy": gyroscope[1],
         #          "GYRz": gyroscope[2]}
        #message['ObjectTemperature'] = get_sensor_data() 
        #message['Accelerometer'] = get_move_acc_data()
	#message['Gyroscope'] = get_move_gyro_data()
	messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        if args.mode == 'publish':
            print('Published topic %s: %s\n' % (topic, messageJson))
    time.sleep(1)
