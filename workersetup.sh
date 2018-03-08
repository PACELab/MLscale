#!/bin/bash
sudo apt-get update
#sudo apt-get -y install apache2 php5
# uncomment following for load balancer
#sudo a2enmod proxy proxy_http proxy_balancer lbmethod_byrequests slotmem_shm
# uncomment following for THE scaling directive VM
sudo apt-get -y install python-scipy python-numpy python-pip gfortran python-dev
sudo pip install networkx
sudo pip install ffnet	# neural network library
#sudo apt-get -y install ntpdate tmux collectl moreutils
#sudo ntpdate -s time.nist.gov
