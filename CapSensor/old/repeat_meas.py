##function reports capacitance of CIN1 by communicating with FDC1004 via i2c communication using smbus2 library.
# It takes two arguments,[1]  t_total is the total runtime in minutes, [2] freq is rate at which  to sample
#[per minute]. Note the byte endianess of the registers is the reverse of what smbus2 uses.  For information on
# registers see FDC1004 manual at http://www.ti.com/lit/ds/symlink/fdc1004.pdf

#take inputs for time to run and freq of measurements

#open files to write capacitances to (in pF)


import struct, csv, time
from smbus2 import SMBusWrapper
from statistics import mean, variance

#define fdc1004 i2c address
adr = 0x50
POLL_FREQ = 500

def swap_endian(data):
   return struct.unpack('<H', struct.pack('>H', data))[0]

#open Bus 2 to configure measurements: CIN1 (bus will close automatically after indented code completed)
with SMBusWrapper(2) as bus:
    #configure meas1 at 0x08, positive input CIN1, no negative input, no offset capacitance,...
    #set to 0x1C00 (endianess reversed)
    bus.write_word_data(adr,0x08,0x001C)
    bus.write_word_data(adr,0x0C,0x8005)

i = 0
start = time.time()
write_file = open("capRepeat.txt", "w")
writer = csv.writer(write_file)
data = []

#begin measuring, runtime for one loop iteration about 0.01s and is ignored in reps estimate.  
while True:
    #open i2c bus (closes upon completion of 2 indent code)
    time.sleep(1/POLL_FREQ)
    with SMBusWrapper(2) as bus:
        #trigger single  meas1 at 0x0C, 100S/s, repeat disabled, set to 0x480 End. Reversed
        status = swap_endian(bus.read_word_data(adr,0x0C))
        if ((1<<3) & status):
            #read 16 most sig bits of meas1 at 0x00
            MSB1 = swap_endian(bus.read_word_data(adr,0x00))
            #read 8 least sig bits plus one empty byte of meas1 at 0x01
            LSB10 = swap_endian(bus.read_word_data(adr,0x01))
        else:
            continue

    twos1 = (MSB1<<8) + (LSB10>>8)

    #calculate twos complement and convert measurements to pF
    if (1 == (twos1>>23)):
        Cap1 = (twos1-(1<<24))/2**19
    else:
        Cap1 = twos1/(2**19)

    #writer.writerow([time.time(), Cap1])
    data.append(Cap1)
    i+=1

    if not (i%100):
        print("reading: ", mean(data))
        print("SD: ", variance(data)**0.5)
        data=[]
        
        #print("freq: ", i / (time.time()-start))

write_file.close()

