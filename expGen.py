import sys

def main(argv):
	if len(argv)<5:
		print "Usage: python expGen.py lower_limit upper_limit dt dn"
	n1=int(argv[1])
	n2=int(argv[2])
	dt=int(argv[3])
	dn=int(argv[4])
	numconns=0
	print "httperf-0.9.0-varrarive/src/httperf --server=loadbalancer --uri=/mypage.php?n=500 --timeout=5",
	for i in range(n1,n2+dn,dn):
		iat=1/float(i)
		nc=int(dt/iat)
		print "--period=%d:e%f"%(nc,iat),
		numconns+=nc
	print "--num-conns=%d"%numconns

# --period=6000:e0.01000		
main(sys.argv)
