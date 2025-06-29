bikes = [''] * 100
bikes.append('dingdong')
bikes[25] = 'foofy'
bikes.insert(26,'kakkaa')
bikes[0] = 'nahp'
bikes[2] = 'pahp'

print(bikes)
print(bikes.pop().upper())
bikes.remove('')
print(bikes)
print(len(bikes))
import sys
print(sys.version)
