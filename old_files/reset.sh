rm -rf /mapr/demo.mapr.com/video_stream
maprcli stream create -path /mapr/demo.mapr.com/video_stream -produceperm p -consumeperm p -topicperm p -copyperm p -adminperm p
rm -rf /mapr/demo.mapr.com/recording_stream
maprcli stream create -path /mapr/demo.mapr.com/recording_stream -produceperm p -consumeperm p -topicperm p -copyperm p -adminperm p
rm -rf /mapr/demo.mapr.com/images/*
