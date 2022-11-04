#! /bin/bash

# for install run as root or with sudo. Also running from the base user ezmeral
# For Ubunu use sudo with this script

# pkgs installed with this script. python and pip updates executed in setup.sh

# functions
function package_exists() {
	dpkg -s "$1" &> /dev/null
    return $?  
}

function py2_pkg_exists() {
	python2 -m "$1" --version
    return $?  
}

# Check OS platform version
UNAME=$(uname | tr "[:upper:]" "[:lower:]")
# If we see Linux, get version of linux, looking for ubuntu, redhat, centos, etc.
if [ "$UNAME" == "linux" ]; then
    # use LSB to get version if present
    if [ -f /etc/lsb-release -o -d /etc/lsb-release.d ]; then
        export DISTRIBUTION=$(lsb_release -i | cut -d: -f2 | sed s/'^\t'//)
    # if not, use data in file
    else
        export DISTRIBUTION=$(ls -d /etc/[A-Za-z]*[_-][rv]e[lr]* | grep -v "lsb" | cut -d'/' -f3 | cut -d'-' -f1 | cut -d'_' -f1)
    fi
fi
# could not find an answer so set to generic type fond with uname
[ "$DISTRIBUTION" == "" ] && export DISTRIBUTION=$UNAME
unset UNAME
echo "found $DISTRIBUTION"
if [ "$DISTRIBUTION" == "Ubuntu" ]; then
        echo "installing for ubuntu. at the time only v 20.+ was used. python 3 is default"
        
        add-apt-repository universe
		apt-get -y update
        
        if package_exists bzip2 ; then
    		echo "bzip2 already installed"
    	else
    	    echo "installing bzip2"
    		apt-get -y install bzip2
		fi
		
		# check if miniconda exists
		if [ -d "/opt/miniconda/bin" ] ; then
			echo "miniconda already installed"
		else
			echo "install miniconda"
			wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
			bash ./miniconda.sh -b -p /opt/miniconda
		fi
		export PATH="/opt/miniconda/bin:$PATH"
		
		if package_exists build-essential ; then
			echo "build-essential already installed"
    	else
    		echo "installing build-essential"
    		apt-get -y install build-essential
		fi
		
		if package_exists g++ ; then
    		echo "g++ already installed"
    	else
    		echo "installing g++"
    		apt-get -y install g++
		fi
		
		
		if package_exists python3-pip ; then
    		echo "python3-pip already installed"
    	else
    		echo "installing python3-pip"
    		apt-get -y install python3-pip
		fi 
		
		#if package_exists libopencv-dev ; then
    	#	echo "libopencv-dev already installed"
    	#else
    	#	echo "installing libopencv-dev"
    	#	apt-get -y install libopencv-dev
		#fi
		
		# python 2 install stuff
		#if package_exists python2 ; then
    	#	echo "python2 already installed"
    	#else
    	#	echo "installing python2"
    	#	apt-get -y install python2
		#fi 
		
		
		#if py2_pkg_exists pip ; then
		#	echo "pip installed on pythin2"
		#else
		#	echo "installing pip on python2"
		#	wget https://bootstrap.pypa.io/pip/2.7/get-pip.py -O get-pip.py
		#	python2 get-pip.py
		#fi
		
		#su ezmeral -c "pip3 install --upgrade pip"
		#su ezmeral -c "pip3 install maprdb-python-client"
		#su ezmeral -c 'pip3 install --global-option=build_ext --global-option="--library-dirs=/opt/mapr/lib" --global-option="--include-dirs=/opt/mapr/include/" mapr-streams-python'
		#su ezmeral -c "pip3 install numpy"
		#su ezmeral -c "pip3 install Flask"
		#su ezmeral -c "pip3 install imutils"
		#su ezmeral -c "pip3 install opencv-python"
		#su ezmeral -c "pip3 install Pillow"
		#su ezmeral -c "pip3 install tellopy" 
		#su ezmeral -c "pip3 install av"
		#su ezmeral -c "pip3 install confluent_kafka"
		
	
		#su - ezmeral -c "pip2 install --upgrade pip"
		#su - ezmeral -c "pip2 install maprdb-python-client"
		#su - ezmeral -c 'pip2 install --global-option=build_ext --global-option="--library-dirs=/opt/mapr/lib" --global-option="--include-dirs=/opt/mapr/include/" mapr-streams-python'
		#su - ezmeral -c "pip2 install numpy"
		#su - ezmeral -c "pip2 install Flask"
		#su - ezmeral -c "pip2 install imutils"
		#su - ezmeral -c "pip2 install opencv-python"
		#su - ezmeral -c "pip2 install Pillow"
	

		
		#conda install av -c conda-forge -y
		#conda update -n base -c defaults conda
		
else
        echo "assuming redhat/centos. TODO: add checks for further os types"


		yum install -y bzip2


		wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
		bash ./miniconda.sh -b -p /opt/miniconda
		export PATH="/opt/miniconda/bin:$PATH"


		wget http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
		rpm -ivh epel-release-latest-7.noarch.rpm

		yum install -y gcc-c++
		yum install -y python-pip

		pip install --upgrade pip

		pip install maprdb-python-client
		pip install --global-option=build_ext --global-option="--library-dirs=/opt/mapr/lib" --global-option="--include-dirs=/opt/mapr/include/" mapr-streams-python

		pip install numpy
		pip install Flask
		pip install imutils
		pip install opencv-python
		pip install Pillow

		conda install av -c conda-forge -y
		
fi




