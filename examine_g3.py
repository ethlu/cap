import os
import so3g
from so3g.hk.getdata import HKArchiveScanner

#Utility to look at g3 data in data_dir. Requires so3g (docker image). Run python interpreter and source "from examine_g3 import *"
data_dir = '/data/'

search = os.walk(data_dir)
files = []
for root, directory, _file in search:
    for f in _file:
        if f[-2:] == 'g3':
            files.append(os.path.join(root,f))

hkcs = HKArchiveScanner()
for filename in files:
    hkcs.process_file(filename)
cat = hkcs.finalize()
fields, timelines = cat.get_fields()

# List all data fields
field_names = []
for field_name in sorted(fields):
    print("field_name: {}, index: {}".format(field_name, len(field_names)))
    group_name = fields[field_name]['timeline']
    field_names.append((field_name, group_name))

# Get field with index i by get_index(i)
fields, timelines = cat.get_data()
def get_index(i):
    print("data: ", fields[field_names[i][0]])
    print("timeline: ", timelines[field_names[i][1]])

