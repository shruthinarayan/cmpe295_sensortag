# 
# Read temperature from the TMP006 sensor in the TI SensorTag 
# It's a BLE (Bluetooth low energy) device so using gatttool to
# read and write values. 
#
#sudo hciconfig hci0 up
#sudo hcitool lescan  #To find the address of your SensorTag run 
#gatttool -b 54:6C:0E:53:18:6C --interactive
#connect
#python main.py 54:6C:0E:53:18:6C
# 
#characteristics # to verify uuid and handler
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#

import pexpect
import sys
import time
import CC2650 as sensor
import signal

def signal_handler(signal, frame):
	print("__MAIN__: You pressed Ctrl+C!")
	sys.exit(0)

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

signal.signal(signal.SIGINT, signal_handler)
sensor_data = [ [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] ]
bluetooth_adr = sys.argv[1]
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
while True:
    time_test = time.time()
    time.sleep(0.5)
 
    tool.sendline('char-read-hnd 0x24')
    tool.expect('descriptor: .*') 
    rval = tool.after.split()
    raw_temp_data = [ rval[1], rval[2], rval[3], rval[4] ]     
    sensor_data[6] = sensor.get_object_temp(raw_temp_data)
    
    tool.sendline('char-read-hnd 0x3C')
    tool.expect('descriptor: .*')
    rval = tool.after.split()
    raw_move_data = [ rval[1], rval[2], rval[3], rval[4], rval[5], rval[6], rval[7], rval[8], rval[9], rval[10], rval[11], rval[12], rval[13], rval[14], rval[15], rval[16], rval[17], rval[18] ]
    sensor_data[3] = sensor.get_acc_data(raw_move_data)
    sensor_data[3] = sensor.get_gyro_data(raw_move_data)
    sensor_data[3][0] = abs(sensor_data[3][0]) * 0.5
    sensor_data[3][1] = abs(sensor_data[3][1]) * 0.5
    sensor_data[3][2] = abs(sensor_data[3][2]) * 0.5
    
    print("")
