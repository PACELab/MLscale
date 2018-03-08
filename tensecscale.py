from ffnet import ffnet, mlgraph, readdata, savenet, loadnet
import time,re,subprocess,numpy
import datetime,csv,sys,traceback

nonce='8c969c76-d44f-409e-bbc1-d0c3b32d45a2'
lb='172.31.9.63'
repWorker='172.31.53.174'
prv_key='../aws-cloud.pem'
usr='ubuntu'
stat_f_select='2-5,8-'
upperRT=90
lowerRT=40

def follow(thefile):
	thefile.seek(0,2)
	while True:
		line = thefile.readline()
		if not line:
			time.sleep(0.1)
			continue
		yield line

def main():
	# load network
	net=loadnet('prcntrt_rr_statwosysdsk.network')
	plog=open('predict.log','w')
	metriclog=open('metric.log','wb')
	mlog=csv.writer(metriclog)
	scalelog=open('scale.log','w')
	accesslog=open('/var/log/apache2/access.log','r')
	loglines=follow(accesslog)
	first=True
	cts=-1
	RT=0
	RTs=[]
	N=0
	timesSuggested=0
	workerStatus=workerInit()
	w=sum(workerStatus.values())
#	exit(0)
	for	line in loglines:
		try:
			if first:
				matches=re.search('.*:([0-9]*:[0-9]*:[0-9])[0-9] .* ([0-9]*)',line)
				cts=matches.group(1)
				RT=float(matches.group(2))/1000.
				RTs.append(RT)
				N=1
				first=False
			else:
	#			print line
				matches=re.search('.*:([0-9]*:[0-9]*:[0-9])[0-9] .* ([0-9]*)',line)
				ts=matches.group(1)
				if cts==ts:
					RTs.append(float(matches.group(2))/1000.)
					RT+=float(matches.group(2))/1000.
					N+=1
				elif cts<ts or (ts[0:7]=="00:00:0" and cts[0:7]=="23:59:5"):
					rt=float(RT/N)
					avgrt=rt
					rr=N
					p_95=numpy.percentile(RTs,95)
					print "====== Average RT for ten second interval %s is %0.2f, 95th percentile is: %0.2f and RC is %d ======"%(cts,rt,p_95,rr)
					cts=ts
					RT=float(matches.group(2))/1000.
					N=1
					RTs=[RT]
				
#					statcmd= '''tail -n 10 stat | grep '[0-9]*:[0-9]*:[0-9]*' | sed 's/ \+/ /g' | cut -d ' ' -f 2-5,8- | awk '{for (i=1;i<=NF;i++){a[i]+=$i;}} END {for (i=1;i<=NF;i++){printf "%f ", a[i]/NR;}}' '''
					statcmd= '''ssh -i %s %s@%s 'tail -n 10 stat' | grep '[0-9]*:[0-9]*:[0-9]*' | sed 's/ \+/ /g' | cut -d ' ' -f %s | awk '{for (i=1;i<=NF;i++){a[i]+=$i;}} END {for (i=1;i<=NF;i++){printf "%%f ", a[i]/NR;}}' '''
					statavg=subprocess.check_output(statcmd%(prv_key,usr,repWorker,stat_f_select),shell=True)
	#				print statavg

					workerStatus=workerInit()
					w=sum(workerStatus.values())

					rt=p_95		# 95th percentile
					print "+++ Testing for scale up +++"
					k=0					
					if rt>upperRT:
						plog.write("%s Testing for SCALE UP, current percentile RT: %d\n"%(ts,rt))
					while rt>upperRT:
						statarr=[float(i) for i in statavg.split()]
						carr=[rr/10]+[statarr[i] for i in [0,2,3,6,7,8,9]]
						metrics=numpy.array(estimateMetrics(carr,w,k))
#						print "Metrics",metrics
						o,r= net.test([metrics],[upperRT],iprint=0)
						rt=o[0][0]
						print "Predicted RT: ", rt," for workers: ",w+k
						plog.write("\tPredicted RT:%d ms for %d workers\n"%(rt,w+k))
						if rt<upperRT:
							break
						k+=1

					rt=p_95
					print "--- Testing for scale down ---"
					if rt<lowerRT and w>1:
						plog.write("%s Testing for SCALE DOWN, current percentile RT: %d\n"%(ts,rt))
					while rt<lowerRT and w>1:
						k-=1
						statarr=[float(i) for i in statavg.split()]
#						print statarr
						carr=[rr/10]+[statarr[i] for i in [0,2,3,6,7,8,9]]
						metrics=numpy.array(estimateMetrics(carr,w,k))
#						print "Metrics",metrics
						o,r= net.test([metrics],[lowerRT],iprint=0)
						rt=o[0][0]
						print "Predicted RT: ", rt," for workers: ",w+k
						plog.write("\tPredicted RT:%d ms for %d workers\n"%(rt,w+k))
						if rt>upperRT:
							k+=1
							break
						if w+k==1:
							break
				
					# log to file
					rt=p_95
					statarr=[float(i) for i in statavg.split()]
					carr=[rr/10]+[statarr[i] for i in [0,2,3,6,7,8,9]]
#					carr=[rr/10]+statarr
#					mlog.write("Time:%s"%ts)
					mlog.writerow([ts, p_95, avgrt, w]+carr)
					metrics=numpy.array(carr)
					o,r= net.test([metrics],[80],iprint=0)
					pRT=o[0][0] # calculating model RT
					logstr="%s\tAverage RT: %f\tPredicted RT: %f\tNo. of workers in use: %d\tSuggested k: %d\tTimes suggested: %d\n"%(ts,rt,pRT,w,k,timesSuggested)
					print "@LOG: "+logstr
					scalelog.write(logstr)
					scalelog.flush()
					metriclog.flush()					
			
					if k>0:
						timesSuggested+=1
						if timesSuggested>2:
							timesSuggested=0
							for t in range(0,k):
								addWorker(workerStatus,scalelog)
								workerStatus=workerInit()
							w=sum(workerStatus.values())
					elif k<0:
						timesSuggested+=1
						if timesSuggested>2:
							timesSuggested=0
#							for t in range(0,-k):
#								print "Removing worker",t+1
							removeWorker(workerStatus,scalelog)#
							workerStatus=workerInit()#					
							w=sum(workerStatus.values())
					else:
						timesSuggested=0
		except Exception as e:
			traceback.print_exception(*sys.exc_info())
			print line
			
	scalelog.close()
	plog.close()
	mlog.close()

def addWorker(workerStatus,scalelog):
	workerIP=-1
	for worker in workerStatus:
		if workerStatus[worker]==False:
			workerIP=worker
			break
	if workerIP!=-1:
		print "Adding worker: "+workerIP
		enablecmd= 'wget --quiet "http://%s/balancer-manager" --post-data="w_status_I=0&w_status_N=0&w_status_D=0&w_status_H=0&b=mybalancer&w=http%%3A%%2F%%2F%s%%2F&nonce=%s" -O outputWget '%(lb,workerIP,nonce)
		subprocess.check_output(enablecmd,shell=True)
		scalelog.write(datetime.datetime.now().strftime("%H:%M:%S ")+"Worker "+workerIP+" added.\n")
		scalelog.flush()
	else:
		print "No workers left"	

def removeWorker(workerStatus,scalelog):
	workerIP=-1
	for worker in workerStatus:
		if workerStatus[worker]==True and worker!=repWorker:
			workerIP=worker
			break
	if workerIP!=-1:
		print "Removing worker: "+workerIP
		enablecmd= 'wget --quiet "http://%s/balancer-manager" --post-data="w_status_I=0&w_status_N=0&w_status_D=1&w_status_H=0&b=mybalancer&w=http%%3A%%2F%%2F%s%%2F&nonce=%s" -O outputWget '%(lb,workerIP,nonce)
		subprocess.check_output(enablecmd,shell=True)
		scalelog.write(datetime.datetime.now().strftime("%H:%M:%S ")+"Worker "+workerIP+" removed.\n")
		scalelog.flush()
	else:
		print "It should not come here"	

def workerInit():
	d={}
	cmd= " curl -s http://%s/balancer-manager | grep 'Init' "%(lb)
	allW=subprocess.check_output(cmd,shell=True,universal_newlines=True).splitlines()
	workercmd=" curl -s http://%s/balancer-manager | grep 'Init Ok' "%(lb)
	working = subprocess.check_output(workercmd,shell=True).splitlines()
	for line in allW:
		workerIP=re.search('.*http:\/\/([0-9]*.[0-9]*.[0-9]*.[0-9]*).*',line).group(1)
		d[workerIP]=False
	for line in working:
		workerIP=re.search('.*http:\/\/([0-9]*.[0-9]*.[0-9]*.[0-9]*).*',line).group(1)
		d[workerIP]=True		
	return d
	
def estimateMetrics(metrics,w,k):
	from bvaluesAWS import bvalues
        for i in range(0,len(metrics)):
                metrics[i]=numpy.dot(bvalues[i],[(metrics[i]*w)/(w+k),(metrics[i]*k)/(w+k),1])
        return metrics

main()
