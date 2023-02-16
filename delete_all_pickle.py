import os
from pprint import pprint

result = [os.path.join(dp, f) for dp, dn, filenames in os.walk('Data')
          for f in filenames if os.path.splitext(f)[1] == '.pickle']
pprint(result)
for file in result:
    os.remove(file)
