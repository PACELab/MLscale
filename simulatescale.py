from ffnet import ffnet, mlgraph, readdata, savenet, loadnet
import time,re,subprocess,numpy
import datetime,csv

def main():
	# load network
	net=loadnet('expData/rt_rr_statwosysdsk.network')
	timesSuggested=0
	loglines=open('expData/partTrace.csv')
	for	line in loglines:
		metrics=line.split(',')
		rt=float(metrics[1])
		w=int(metrics[2])
		carr=[float(metrics[i]) for i in [3,4,6,7,10,11,12,13] ]
		inputs=numpy.array(carr)
		o,r=net.test([inputs],[100],iprint=0)
		print "Avg. RT: "+str(rt)+"  Workers: "+str(w) + " Predicted RT: "+str(o[0][0])
		print "Request rate and stat: ",
		for i in carr:
			print i,
		print
		
		k=0
		while rt>100:
#			inputs=numpy.array(carr)*(float(w)/float(w+k))
			inputs=numpy.array(estimateMetrics(carr,w,k))
			print "\t\tEstimates: ",
			for i in inputs:
				print i,
			print
			o,r=net.test([inputs],[100],iprint=0)
			rt=o[0][0]
			print "\t\tPredicted RT:",rt," Workers: ",w+k
			if rt<100:
				break
			k+=1

		rt=float(metrics[1])
		while rt<70 and w>1:
			k-=1
#			inputs=numpy.array(carr)*(float(w)/float(w+k))
			inputs=numpy.array(estimateMetrics(carr,w,k))
			print "\t\tEstimates: ",
			for i in inputs:
				print i,
			print
			o,r=net.test([inputs],[100],iprint=0)
			rt=o[0][0]
			print "\t\tPredicted RT:",rt," Workers: ",w+k
			if rt>70:
				k+=1
				break
			if w+k==1:
				break			
		if k!=0:
			print "\tSuggested k",k
			

def estimateMetrics(metrics,w,k):
	if k==0:
		return metrics
        from bvalues import bvalues
        for i in range(0,len(metrics)):
                metrics[i]=numpy.dot(bvalues[i],[(metrics[i]*w)/(w+k),(metrics[i]*k)/(w+k),1])
        return metrics


main()
