
scp broker_V1.0.py 2018211007@szcluster.mmlab.top:~/src
scp network2.py 2018211007@szcluster.mmlab.top:~/src
scp Config.py 2018211007@szcluster.mmlab.top:~/src
scp Dealer.py 2018211007@szcluster.mmlab.top:~/src
scp DealController.py 2018211007@szcluster.mmlab.top:~/src
scp Logger.py 2018211007@szcluster.mmlab.top:~/src



scp Config.py 2018211007@szcluster.mmlab.top:~/src/Sequencer
scp Sequencer/Listener.py 2018211007@szcluster.mmlab.top:~/src/Sequencer
scp Sequencer/Master.py 2018211007@szcluster.mmlab.top:~/src/Sequencer
scp Sequencer/pack.py 2018211007@szcluster.mmlab.top:~/src/Sequencer
# scp Sequencer/pack.py 2018211007@szcluster.mmlab.top:~/Sequencer




# scp network2.py 2018211007@szcluster.mmlab.top:~/
#scp broker_V1.0.py 2018211007@szcluster.mmlab.top:~/
#scp broker_V1.0.py 2018211007@szcluster.mmlab.top:~/

ssh 2018211007@szcluster.mmlab.top "./send.sh"
ssh 2018211007@szcluster.mmlab.top "./kill.sh"

