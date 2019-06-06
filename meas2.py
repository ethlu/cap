##function takes two arguements,[1]  t_total is the total time to run in minutes, [2] freq is rate at which  to
#sample [per minute] This program write capacitance measurements of CIN1 to capA.txt and CIN2 to capB.txt 
#For information on registers see FDC1004 manual at http://www.ti.com/lit/ds/symlink/fdc1004.pdf

#take inputs for time to run and freq of measurements
import sys
t_total = int( sys.argv[1])
freq = int( sys.argv[2])
#calculate number of cycles and wait period (in minutes)
reps = freq * t_total
wait = 60/freq

#open files to write capacitances to (in pF)
fh1 = open("capA.txt", "a")
fh2 = open("capB.txt", "a")

import struct
import time
from smbus2 import SMBusWrapper

#define fdc1004 i2c address
adr = 0x50

#configure two measurements: CIN1, CIN2
with SMBusWrapper(2) as bus:
    #configure meas1 at 0x08, positive input CIN1, no negative input, no offset capacitance,...
    #set to 0x1C00 (endianess reversed)
    bus.write_word_data(adr,0x08,0x001C)

    #congfigure meas2 at 0x09, positive input CIN2, no negative input, no offset capacitance,...
    #set to 0x 3C00 (endianess reversed)
    bus.write_word_data(adr,0x09,0x003C)

#initalize rep count
x = 0
#begin measuring, runtime for one loop iteration about 0.01s and is ignored in reps estimate
while x < reps:
    #open i2c bus to aquire meas1, meas2  data.  Wait time is distributed betweem i2c queries to 
    #avoid communication errors
    with SMBusWrapper(2) as bus:
        #trigger single  meas1 at 0x0C, 100S/s, repeat disabled, set to 0x480 End. Reversed
        bus.write_word_data(adr,0x0C,0x8004)
        time.sleep(wait/4)
        #read 16 most sig bits of meas1 at 0x00
        capM1 = bus.read_word_data(adr,0x00)
        #read 8 least sig bits plus one empty byte of meas1 at 0x01
        capL1 = bus.read_word_data(adr,0x01)
        time.sleep(wait/4)

        #tigger single meas2 at 0x0C 100S/s, repeat disabled, set to 0x440, End. Reversed
        bus.write_word_data(adr,0x0C,0x4004)
        time.sleep(wait/4)

        #read 16 most sig bits of meas2 at 0x02
        capM2 = bus.read_word_data(adr,0x02)
        #read 8 least sig bits plus one empty byte of meas2 at 0x03
        capL2 = bus.read_word_data(adr,0x03)
        time.sleep(wait/4)
    #reverse byte endianness
    MSB1 = struct.unpack('<H', struct.pack('>H',capM1))[0]
    LSB10 = struct.unpack('<H', struct.pack('>H',capL1))[0]

    MSB2 = struct.unpack('<H', struct.pack('>H',capM2))[0]
    LSB20 = struct.unpack('<H', struct.pack('>H',capL2))[0]

    #drop last byte from LSB 
    LSB1 = (LSB10>>8)
    LSB2 = (LSB20>>8)

    #format into strings, left pad 0's to fill to byte length
    MSB1 = format(MSB1, '#018b')
    LSB1 = format(LSB1, '08b')

    MSB2 = format(MSB2, '#018b')
    LSB2 = format(LSB2, '08b')

    #concatenate the two strings, convert back to integer
    B_tot1 = MSB1 + LSB1
    twos1 = (int(B_tot1, base=2))

    B_tot2 = MSB2 + LSB2
    twos2 = (int(B_tot2, base=2))

    #calculate twos complement and convert measurements to pF
    if (1 == (twos1>>23)):
        Cap1 = (-(~twos1+1))/2**19
    else:
        Cap1 = twos1/(2**19)

    #set cursor position in file at end of file, then write a new line of capacitance data
    Caps1 = '\n' + str(Cap1)
    fh1.seek(0,2)
    line = fh1.write(Caps1)




    if (1 == (twos2>>23)):
        Cap2 = (-(~twos2+1))/2**19
    else:
        Cap2 = twos2/(2**19)

    #set cursor position in file at end of file, then write a new line of capacitance data

    Caps2 = '\n' + str(Cap2)
    fh2.seek(0,2)
    line = fh2.write(Caps2)

    x += 1

fh1.close()
fh2.close()
