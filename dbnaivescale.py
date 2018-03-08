import time,re,subprocess
import datetime,csv,sys,traceback

lb='10.2.10.76'
repWorker='10.2.10.102'
prv_key='/home/ubuntu/cewit.pem'
usr='ubuntu'
stat_f_select='2-'
#stat_m_select=[0,2,3,6,7,8,9]
upperRT=100 # unkown yet
lowerRT=60
inertia=2
dns={}

def follow(thefile):
	thefile.seek(0,2)
	while True:
		line = thefile.readline()
		if not line:
			time.sleep(0.1)
			continue
		yield line

def main():
	metriclog=open('metric.log','wb')
	mlog=csv.writer(metriclog)
	accesslog=open('/home/ubuntu/phplog/rt_wid.txt','r')
	scalelog=0
	loglines=follow(accesslog)
	first=True
	cts=-1
	RT=0
	N=0
	timesSuggested=0
	workerStatus=workerInit()
	w=sum(workerStatus.values())
#	print workerStatus
#	exit(0)
	for	line in loglines:
		try:
			if first:
				matches=re.search('([0-9]*:[0-9]*:[0-9])[0-9] ([0-9]*)',line)
				cts=matches.group(1)
				RT=float(matches.group(2)) # already in milliseconds
				N=1
				first=False
			else:
				matches=re.search('([0-9]*:[0-9]*:[0-9])[0-9] ([0-9]*)',line)
				ts=matches.group(1)
				if cts==ts:
					RT+=float(matches.group(2))
					N+=1
				elif cts<ts or (ts[0:7]=="00:00:0" and cts[0:7]=="23:59:5"):
					rt=float(RT/N)
					avgrt=rt
					rr=N/10
					print "====== Average RT for ten second interval %s is %0.2f, and RC is %d ======"%(cts,rt,rr)
					cts=ts
					RT=float(matches.group(2))
					N=1
				
					statcmd= '''ssh -i %s %s@%s 'tail -n 10 stat' | grep '[0-9]*:[0-9]*:[0-9]*' | sed 's/ \+/ /g' | cut -d ' ' -f %s | awk '{for (i=1;i<=NF;i++){a[i]+=$i;}} END {for (i=1;i<=NF;i++){printf "%%f ", a[i]/NR;}}' '''
					statavg=subprocess.check_output(statcmd%(prv_key,usr,repWorker,stat_f_select),shell=True)
	#				print statavg

					workerStatus=workerInit()
					w=sum(workerStatus.values())

					rt=avgrt
					k=0					
					if rt>upperRT:
						k+=1

					if rt<lowerRT and w>1:
						k-=1
				
					# log to file
					rt=avgrt
					statarr=[float(i) for i in statavg.split()]
#					carr=[rr]+[statarr[i] for i in stat_m_select]
					carr=[rr]+statarr
					mlog.writerow([ts, avgrt, w]+carr)
					metriclog.flush() #file for csv write mlog
					
#					continue			
					if k>0:
						timesSuggested+=1
						print "--- Scale UP suggested %d times---"%timesSuggested
						if timesSuggested>inertia:
							timesSuggested=0
							for t in range(0,k):
								addWorker(workerStatus,scalelog)
							w=sum(workerStatus.values())
					elif k<0:
						timesSuggested+=1
						print "--- Scale DOWN suggested %d times---"%timesSuggested
						if timesSuggested>inertia:
							timesSuggested=0
							removeWorker(workerStatus,scalelog)#
							w=sum(workerStatus.values())
					else:
						timesSuggested=0

		except Exception as e:
			traceback.print_exception(*sys.exc_info())
			print line
			
	mlog.close()

def addWorker(workerStatus,scalelog):
	workerIP=-1
	for worker in workerStatus:
		if workerStatus[worker]==False:
			workerIP=worker
			break
	if workerIP!=-1:
		print "Adding worker: "+workerIP
		
#		enablecmd= """ ssh -i %s %s@%s 'echo "enable server mysql-cluster/%s" | socat stdio /etc/haproxy/haproxysock' """ %(prv_key,usr,lb,dns[workerIP])

		enablecmd= " ssh -i %s %s@%s './changeWeight.sh %s 1' "
		subprocess.check_output(enablecmd%(prv_key,usr,lb,dns[workerIP]),shell=True)
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
#		disablecmd= """ ssh -i %s %s@%s 'echo "disable server mysql-cluster/%s" | socat stdio /etc/haproxy/haproxysock' """%(prv_key,usr,lb,dns[workerIP])

		disablecmd= " ssh -i %s %s@%s './changeWeight.sh %s 0' "
		subprocess.check_output(disablecmd%(prv_key,usr,lb,dns[workerIP]),shell=True)
	else:
		print "It should not come here"	

def workerInit():
	d={} # DB nodes on back of HAproxy, there might be a smart way to get them from HAproxy, but I got no time for that
	rdns={}
	d['10.2.10.102']=False
	d['10.2.10.103']=False
	d['10.2.10.104']=False
	dns['10.2.10.102']='database1'
	dns['10.2.10.103']='database2'
	dns['10.2.10.104']='database3'
	rdns['database1']='10.2.10.102'
	rdns['database2']='10.2.10.103'
	rdns['database3']='10.2.10.104'

#	cmd= "curl -s http://%s:9000/ | grep 'database' | grep UP "%(lb)
#	res= subprocess.check_output(cmd,shell=True,universal_newlines=True,stderr=subprocess.STDOUT)
#	down=res.splitlines()
#	for line in down:
#		workerName=re.search('.*(database[0-9]).*',line).group(1)
#		d[rdns[workerName]]=True
# write code to init worker now from haproxy.cfg

	cmd= " ssh -i %s %s@%s 'tail /etc/haproxy/haproxy.cfg | head -n 3' "
	cfgout=subprocess.check_output(cmd%(prv_key,usr,lb),shell=True).splitlines()
	for line in cfgout:
		workerName=re.search('.*(database[0-9]).*',line).group(1)
		weight=re.search('.*weight ([0-1])',line).group(1)
		weight=int(weight)
		d[rdns[workerName]]=(weight==1)
	
	return d
	

main()
