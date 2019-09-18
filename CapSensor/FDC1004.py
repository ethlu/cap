#from smbus2 import SMBusWrapper
import struct

class Chip:
    config_reg = 0x0C

    def __init__(self, measurements, measure_rate=0b01):
        self.meas = {m.num: m for m in measurements}
        self.rate = measure_rate
        self.reset()

    def trigger(self):
        self.reset()
        trigger_word = self.rate << 10
        trigger_word |= 1<<8 #repeated
        for n in self.meas.keys():
            trigger_word |= 1<<(8-n)
        reg_write(Chip.config_reg, trigger_word)

    def trigger_single(self, meas_num):
        self.reset()
        trigger_word = self.rate << 10
        trigger_word |= 1<<(8-meas_num)
        reg_write(Chip.config_reg, trigger_word)
        
    def poll(self, time=None):
        done = self._check_done()
        for n in done:
            self.meas[n]._read(time)
        return done

    def get_data(self, meas_num):
        return self.meas[meas_num].get_data()
    
    def add_meas(self, meas):
        old = self.meas.get(meas.num)
        self.meas[meas.num] = meas
        self.reset()
        return old
    
    def remove_meas(self, meas_num):
        self.reset()
        return self.meas.pop(meas_num)

    def reset(self):
        reg_write(Chip.config_reg, 1<<15)
        self._write_configs()

    def _write_configs(self):
        for m in self.meas.values():
            m._write_config()

    def _check_done(self):
        status = reg_read(Chip.config_reg)
        return [n + 1 for n in range(4) if status & 1<<(3-n)]

class Measurement:
    config_regs = (0x08, 0x09, 0x0A, 0x0B)
    MSB_regs = (0x00, 0x02, 0x04, 0x06)
    LSB_regs = (0x01, 0x03, 0x05, 0x07)

    def __init__(self, meas_num, name = None): 
        assert 1 <= meas_num <= 4
        self.num = meas_num
        if name is None:
            self.name = "cap" + str(meas_num)
        else:
            self.name = name
        self.config_reg = Measurement.config_regs[meas_num - 1]
        self.MSB_reg = Measurement.MSB_regs[meas_num - 1]
        self.LSB_reg = Measurement.LSB_regs[meas_num - 1]
        self.data = []
        self.timeline = []

    def config(self, CHA, CHB=0b111, CAPDAC=0b00000):
        self.CHA = CHA
        self.CHB = CHB
        self.CAPDAC = CAPDAC

    def get_data(self):
        ret = list(self.data), list(self.timeline)
        self.data.clear()
        self.timeline.clear()
        return ret

    def _write_config(self):
        config_word = self.CHA<<13 | self.CHB<<10 | self.CAPDAC<<5 
        reg_write(self.config_reg, config_word)

    def _read(self, time):
        MSB = reg_read(self.MSB_reg) 
        LSB = reg_read(self.LSB_reg) 
        twos = (MSB<<8) + (LSB>>8)

        if (1 == (twos>>23)):
            cap = (twos-(1<<24))/2**19
        else:
            cap = twos/(2**19)

        self.data.append(cap)
        self.timeline.append(time)
        

#fdc1004 i2c address
adr = 0x50

def reg_write(reg, data):
    with SMBusWrapper(2) as bus:
        bus.write_word_data(adr, reg, swap_endian(data))

def reg_read(reg):
    with SMBusWrapper(2) as bus:
        return swap_endian(bus.read_word_data(adr, reg))

def swap_endian(data):
    return struct.unpack('<H', struct.pack('>H', data))[0]



