#! /bin/bash

# for install run as root or with sudo. Also running from the base user ezmeral
# focus is to move all to python3. assuming python3 is default. opencv for python2 has issues

# TODO: Split os package installs and python to different scripts. and run from here.
# TODO: add in volume and user creations using mapr user to set up ezmeral user

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
        echo "installing python packages on ubuntu in conda environment."
        

		export PATH="/opt/miniconda/bin:$PATH"
		
		pip3 install --upgrade pip
		pip3 install protobuf==3.20.*
		pip3 install maprdb-python-client
		pip3 install --global-option=build_ext --global-option="--library-dirs=/opt/mapr/lib" --global-option="--include-dirs=/opt/mapr/include/" mapr-streams-python
		pip3 install numpy
		pip3 install Flask
		pip3 install imutils
		pip3 install opencv-python
		pip3 install Pillow
		pip3 install tellopy 
		pip3 install av
		pip3 install robomasterpy
		pip3 install multiprocessing
		pip3 install subprocess
		pip3 install threading
		pip3 install deface
		pip3 install confluent_kafka
		pip3 install webbrowser
        pip install 'protobuf <=3.20.1' --force-reinstall

		

		#conda install av -c conda-forge -y
		#conda update -n base -c defaults conda
		
else
        echo "assuming redhat/centos. TODO: add checks for further os types"


		#yum install -y bzip2


		#wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
		#bash ./miniconda.sh -b -p /opt/miniconda
		#export PATH="/opt/miniconda/bin:$PATH"


		#wget http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
		#rpm -ivh epel-release-latest-7.noarch.rpm

		#yum install -y gcc-c++
		#yum install -y python-pip

		#pip install --upgrade pip

		#pip install maprdb-python-client
		#pip install --global-option=build_ext --global-option="--library-dirs=/opt/mapr/lib" --global-option="--include-dirs=/opt/mapr/include/" mapr-streams-python

		#pip install numpy
		#pip install Flask
		#pip install imutils
		#pip install opencv-python
		#pip install Pillow

		#conda install av -c conda-forge -y
		
fi




