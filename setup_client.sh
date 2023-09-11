#/bin/bash
sudo apt-get install python3 python3-pip
pip3 install pysimplegui
pip3 install pyserial
pip3 install netifaces
sudo mkdir ~/PMI_RSEth
sudo cp PMI_RSEthServer.py ~/PMI_RSEth/
echo 'alias PMI_RSEthServer="python3 ~/PMI_RSEth/PMI_RSEthServer.py"' >> ~/.bash_aliases