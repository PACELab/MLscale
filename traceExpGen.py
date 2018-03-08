import sys

def main(argv):
	if len(argv)<5:
		print "Usage: python expGen.py trace_file lower_limit upper_limit dt"
	file=open(argv[1],'r')
	a=int(argv[2])
	b=int(argv[3])
	dt=int(argv[4])
	numconns=0
	print "httperf-0.9.0-varrarive/src/httperf --server=loadbalancer --uri=/mypage.php?n=500 --timeout=5",
	max=-1
	min=2<<10
	for line in file:
		if int(line)>max:
			max=int(line)
		if int(line)<min:
			min=int(line)
	file.seek(0)
	for line in file:
		i=rescale(int(line),max,min,a,b)
		iat=1/float(i)
#		print i
		nc=int(dt/iat)
		print "--period=%d:e%f"%(nc,iat),
		numconns+=nc
	print "--num-conns=%d"%numconns

def rescale(x,max,min,a,b):
	return ((b-a)*(x-min))/(max-min)+a

# --period=6000:e0.01000		
main(sys.argv)
