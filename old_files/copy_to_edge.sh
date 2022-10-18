rm -rf /teits/
mkdir /teits/
mkdir /teits/logs/
cp settings.py /teits/
cp pilot.py /teits/
cp init.sh /teits/
cp clean.sh /teits/
cp -R TelloPy /teits/
sed -i 's/\/mapr\/demo.mapr.com//g' /teits/init.sh
sed -i 's/LOG_FOLDER = ROOT_PATH + "logs\/"/LOG_FOLDER = "\/teits\/logs\/"/g' /teits/settings.py