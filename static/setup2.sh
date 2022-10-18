sudo yum install -y bzip2 
wget https://repo.continuum.io/miniconda/Miniconda3-3.7.0-Linux-x86_64.sh
bash ~/miniconda.sh -b
export PATH="$HOME/miniconda/bin:$PATH"

sudo yum install -y python-pip
sudo yum install -y gcc-c++

pip install maprdb-python-client
pip install --global-option=build_ext --global-option="--library-dirs=/opt/mapr/lib" --global-option="--include-dirs=/opt/mapr/include/" mapr-streams-python

pip install Flask
pip install imutils
pip install opencv-python

pip install Pillow

