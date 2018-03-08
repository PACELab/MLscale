import time,re,subprocess,numpy
import datetime,csv
import sys,os

nonce='f25ec155-acf1-4f3c-bbba-9c03f7d3809c'
repWorker='172.31.53.174'
prv_key='../aws-cloud.pem'
usr='ubuntu'
lb='172.31.9.63'
stat_f_select='2-5,8-'
upper=90
lower=40

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
	metriclog=open('../logs/metric.log.naive%i%i'%(lower,upper),'wb')
	mlog=csv.writer(metriclog)
	scalelog=open('../logs/scale.log.naive%i%i'%(lower,upper),'w')
	accesslog=open('/var/log/apache2/access.log','r')
	loglines=follow(accesslog)
	first=True # hack to check if the script was just started
	cts=-1 # time-stamp we are looking to calculate response time for
	RT=0 # RT keeps the total of response time
	RTs=[] # array to keep individual RT observations
	N=0 # number of requests arrived in cts
	timesSuggested=0
	workerStatus=workerInit() # keeps track of which workers are up and running
	w=sum(workerStatus.values()) # number of workers active
#	exit(0)
	for	line in loglines: # follow the apache accesslog file
		try:
			if first: # if script just started, initialize the necessary variables 
				matches=re.search('.*:([0-9]*:[0-9]*:[0-9])[0-9] .* ([0-9]*)',line)
				cts=matches.group(1)
				RT=float(matches.group(2))/1000.
				RTs.append(RT)
				N=1
				first=False
			else:
	#			print line
				matches=re.search('.*:([0-9]*:[0-9]*:[0-9])[0-9] .* ([0-9]*)',line)
				ts=matches.group(1) # extract the time stamp of request
				if cts==ts: # if the timestamp is same, not changed then keep incrementing the variables
					RTs.append(float(matches.group(2))/1000.) # add to list for percentile
					RT+=float(matches.group(2))/1000. # add to sum for mean
					N+=1 
				elif cts<ts or (ts[0:7]=="00:00:0" and cts[0:7]=="23:59:5"): # case when the new request timestamp has changed -> interval passed
					rt=float(RT/N) # calculate averate rt
					avgrt=rt
					rr=N # request rate 
#					RTs.sort()
#					print RTs
#					print RTs[int(0.95*len(RTs))]
					p_95=numpy.percentile(RTs,95) # calculate percentile
					print "====== Average RT for ten second interval %s is %0.2f, 95th percentile is: %0.2f and RC is %d ======"%(cts,rt,p_95,rr)
					cts=ts # update the interval to current timestamp
					RT=float(matches.group(2))/1000. # reinitialize RT, N , RTs variables for next interval
					N=1
					RTs=[RT]
				
					statcmd= '''ssh -i %s %s@%s 'tail -n 10 stat' | grep '[0-9]*:[0-9]*:[0-9]*' | sed 's/ \+/ /g' | cut -d ' ' -f %s | awk '{for (i=1;i<=NF;i++){a[i]+=$i;}} END {for (i=1;i<=NF;i++){printf "%%f ", a[i]/NR;}}' '''
					statavg=subprocess.check_output(statcmd%(prv_key,usr,repWorker,stat_f_select),shell=True)
#					print statavg

					workerStatus=workerInit()
					w=sum(workerStatus.values())

					print "+++ Testing for scale up +++"
					k=0
					rt=p_95
#					rt=float(statavg.split()[0]) # mind the variable names after this point, rt=cpu for cputhreshscale.py
#					print rt
					if rt>upper: # if rt is greater than the upper limit, consider scaling out
						k+=1

					print "--- Testing for scale down ---"
					if rt<lower and w>1: # if rt is less than lower limit, consider scaling in
						k-=1
				
					# log to file
					rt=avgrt # average rt for last interval
					statarr=[float(i) for i in statavg.split()] # all the stats from collectl
					carr=[rr/10]+statarr # calculated per second request rate since 10 second interval
					mlog.writerow([ts, p_95, avgrt, w]+carr) # add the timestamp, 95th percentile, avg rt, and number of workers to stats and log
					metriclog.flush()
					
			
					if k>0: # if continous suggestion of scale out then scale out
						timesSuggested+=1 
						if timesSuggested>3: # control continous suggestion number here
							timesSuggested=0
							for t in range(0,k): # add k workers one by one
								addWorker(workerStatus,scalelog)
								workerStatus=workerInit()
							w=sum(workerStatus.values())
					elif k<0: # if continous suggestion to scale in, then scale in
						timesSuggested+=1
						if timesSuggested>3: # control continous suggestion number here
							timesSuggested=0
#							for t in range(0,-k):
#								print "Removing worker",t+1
							removeWorker(workerStatus,scalelog)# remove only one worker
							workerStatus=workerInit()#					
							w=sum(workerStatus.values())
					else:
						timesSuggested=0 # if neither scale out nor scale in was suggested, reset the timesSuggested
		except Exception as e:
			print line
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print(exc_type, fname, exc_tb.tb_lineno)
			
	scalelog.close()
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
	
main()
