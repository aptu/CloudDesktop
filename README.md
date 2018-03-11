$ aws sns subscribe --topic-arn arn:aws:sns:us-west-2:437777420713:css490storage_upload_topic --protocol sms --notification-endpoint '+12067475474'
$ python3 CloudDesktop.py config --vm www --size t2.micro --pkgs firefox,x11-apps,vim-gtk
$ python3 CloudDesktop.py connect --vm www

    In ec2 instance:
    $ echo "Some data" > ~/Documents/SampleDocument.txt
    $ gvim ~/Documents/SampleDocument.txt
    $ exit

$ python3 CloudDesktop.py stop --vm www
$ aws sns list-subscriptions
$ aws sns unsubscribe --subscription-arn arn:aws:sns:us-west-2:437777420713:css490storage_upload_topic:c6fada2f-4cba-40b2-b295-294312e477d4
