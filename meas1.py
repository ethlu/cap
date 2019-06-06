##function reports capacitance of CIN1 by communicating with FDC1004 via i2c communication using smbus2 library.
# It takes two arguments,[1]  t_total is the total runtime in minutes, [2] freq is rate at which  to sample
#[per minute]. Note the byte endianess of the registers is the reverse of what smbus2 uses.  For information on
# registers see FDC1004 manual at http://www.ti.com/lit/ds/symlink/fdc1004.pdf

#take inputs for time to run and freq of measurements
import sys
t_total = int( sys.argv[1])
freq = int( sys.argv[2])
#calculate number of cycles and wait period (in minutes)
reps = freq * t_total
wait = 60/freq

#open files to write capacitances to (in pF)
fh1 = open("cap1.txt", "a")

import struct
import time
from smbus2 import SMBusWrapper

#define fdc1004 i2c address
adr = 0x50

#open Bus 2 to configure measurements: CIN1 (bus will close automatically after indented code completed)
with SMBusWrapper(2) as bus:
    #configure meas1 at 0x08, positive input CIN1, no negative input, no offset capacitance,...
    #set to 0x1C00 (endianess reversed)
    bus.write_word_data(adr,0x08,0x001C)

#initalize rep count
x = 0
#begin measuring, runtime for one loop iteration about 0.01s and is ignored in reps estimate.  
while x < reps:
    #open i2c bus (closes upon completion of 2 indent code)
    with SMBusWrapper(2) as bus:
        #trigger single  meas1 at 0x0C, 100S/s, repeat disabled, set to 0x480 End. Reversed
        bus.write_word_data(adr,0x0C,0x8004)

        #wait for measurement
        time.sleep(wait/2)

        #read 16 most sig bits of meas1 at 0x00
        capM1 = bus.read_word_data(adr,0x00)
        #read 8 least sig bits plus one empty byte of meas1 at 0x01
        capL1 = bus.read_word_data(adr,0x01)

    #reverse byte endianness
    MSB1 = struct.unpack('<H', struct.pack('>H',capM1))[0]
    LSB10 = struct.unpack('<H', struct.pack('>H',capL1))[0]
    #drop last byte from LSB (it is automatically 0) 
    LSB1 = (LSB10>>8)
    #format into strings, left pad 0's to fill to byte length
    MSB1 = format(MSB1, '#018b')
    LSB1 = format(LSB1, '08b')
    #concatenate the two strings, convert back to integer
    B_tot1 = MSB1 + LSB1
    twos1 = (int(B_tot1,  base=2))

    #calculate twos complement and convert measurements to pF
    if (1 == (twos1>>23)):
        Cap1 = (-(~twos1+1))/2**19
    else:
        Cap1 = twos1/(2**19)

    #set cursor position in file at end of cap1 txt file, then write a new line of capacitance data
    Caps1 = '\n' + str(Cap1)
    fh1.seek(0,2)
    print(Caps1)
    line = fh1.write(Caps1)

    #increment counter and wait
    x += 1
    time.sleep(wait/2)
#close file, end of program
fh1.close()

