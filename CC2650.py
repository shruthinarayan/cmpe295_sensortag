import binascii

def signedFromHex16(s):
	v = int(s,16)
	if not 0 <= v < 65536:
		raise ValueError, "Hex Number outside 16bit range"
	if (v >= 32768):
		v = v - 65536
	return v

def raw_data_to_bytes(raw_data):
    raw_data_hex = binascii.hexlify(raw_data[0])
    print(raw_data_hex)
    raw_data_bytes = [ ]
    read_index = 0
    print("Length of raw_data_hex: " +str(len(raw_data_hex)))
    for index, char in enumerate(raw_data_hex):
        actual_byte = raw_data_hex[read_index] + raw_data_hex[read_index+1]			
        raw_data_bytes.append(actual_byte)

        if (read_index+2) == len(raw_data_hex):
            break
        read_index = read_index + 2

    return raw_data_bytes

def get_ambient_temp(raw_temp_bytes):
	raw_ambient_temp = int('0x' + raw_temp_bytes[3] + raw_temp_bytes[2], 16)
	ambient_temp_int = raw_ambient_temp >> 2 & 0x3FFF
	ambient_temp_celsius = float(ambient_temp_int) * 0.03125
	print("Ambient Temp: " + str(ambient_temp_celsius))
	return [ambient_temp_celsius, 0 ,0 ]

def get_object_temp(raw_temp_bytes):
	raw_object_temp = int('0x' + raw_temp_bytes[1] + raw_temp_bytes[0], 16)
	object_temp_int = raw_object_temp >> 2 & 0x3FFF
	#print("raw"+str(raw_object_temp))
        #print("int"+str(object_temp_int))
        object_temp_celsius = float(object_temp_int) * 0.03125
	print("Object (IR) Temp: " + str(object_temp_celsius))
	return [object_temp_celsius, 0, 0 ]

def get_gyro_data(raw_move_bytes):
	str_gyro_x =  '0x' + raw_move_bytes[1] + raw_move_bytes[0]
	raw_gyro_x = signedFromHex16(str_gyro_x)
	gyro_x = (raw_gyro_x * 1.0) / (32768/250)

	str_gyro_y = '0x' + raw_move_bytes[3] + raw_move_bytes[2]
	raw_gyro_y = signedFromHex16(str_gyro_y)
	gyro_y = (raw_gyro_y * 1.0) / (32768/250)

	str_gyro_z = '0x' + raw_move_bytes[5] + raw_move_bytes[4]
	raw_gyro_z = signedFromHex16(str_gyro_z)
	gyro_z = (raw_gyro_z * 1.0) / (32768/250)

	raw_gyro = [raw_gyro_x, raw_gyro_y, raw_gyro_z]
	gyro_data = [gyro_x, gyro_y, gyro_z]
	
	#print("RAW Gyro Data: " + str(raw_gyro))
	print("Gyro Data: " + str(gyro_data))
	return gyro_data

def get_acc_data(raw_move_bytes):
	str_acc_x =  '0x' + raw_move_bytes[7] + raw_move_bytes[6]
	raw_acc_x = signedFromHex16(str_acc_x)
	acc_x = ( float(raw_acc_x) / (32768/8) )

	str_acc_y = '0x' + raw_move_bytes[9] + raw_move_bytes[8]
	raw_acc_y = signedFromHex16(str_acc_y)
	acc_y = ( float(raw_acc_y) / (32768/8) )

	str_acc_z = '0x' + raw_move_bytes[11] + raw_move_bytes[10]
	raw_acc_z = signedFromHex16(str_acc_z)
	acc_z = ( float(raw_acc_z) / (32768/8) )	
	
	raw_acc = [raw_acc_x, raw_acc_y, raw_acc_z]
	acc_data = [acc_x, acc_y, acc_z]
	#print("RAW Acc Data: " + str(raw_acc))	
	print("Acc Data: " + str(acc_data))
	return acc_data

