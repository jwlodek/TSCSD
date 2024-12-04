#!/bin/bash

cd $(dirname "$0")/..

source venv/bin/activate

export JAVA_HOME=$PWD/phoebus/jvm/jdk-17
export PATH=$JAVA_HOME/bin:$PATH

chmod +x $PWD/phoebus/phoebus.sh
cd phoebus

./phoebus.sh -resource ../ui/tscsd.bob -settings ../settings.ini &>/dev/null & disown

cd ../ioc && ./st.cmd