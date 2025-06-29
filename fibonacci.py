import time

this = 1
that = 1

total = int(input("How many do you want? "))

for i in range(total):
	time.sleep(1)
	new = this + that
	print(new, end=" ", flush=True)
	this = that
	that = new

print()

