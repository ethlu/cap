#function takes two arguements, the first being the target register, second
#being the 2 byte data (big endian) to be written to the target register.
# The word is endianness reversed and then written. 

#take in arguements
import sys
reg = int(sys.argv[1],16)
word = int(sys.argv[2],2)

import struct
from smbus2 import SMBusWrapper
#set fdc1004 address
adr = 0x50
#reverse  endianess of two byte word
rdwo = struct.unpack('<H', struct.pack('>H',word))[0]

#open i2c bus 2
with SMBusWrapper(2) as bus:
        #write  2 bytes to specified address
         bus.write_word_data(adr,reg,rdwo)
#bus closes after wrapper
