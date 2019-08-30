#function takes one input, a target register in hex format, then prints the
# value of the target register

#take in target register in hex format, convert to an integer
import sys
reg = int(sys.argv[1],16)

import struct
from smbus2 import SMBusWrapper
#set fdc1004 address
adr = 0x50
#open i2c bus 
with SMBusWrapper(2) as bus:
	#read 2 bytes from register specified in arguement, bigendian
	data = bus.read_word_data(adr,reg)
#reverse  endianness, change to hex format
Lend = struct.unpack('<H', struct.pack('>H',data))[0]
val = hex(Lend)
print(val)

