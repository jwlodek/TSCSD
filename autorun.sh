#!/bin/bash

gnome-terminal -t "Simulation" -- scripts/start-simulation.sh
gnome-terminal -t "EPICS IOC" -- scripts/start-epics.sh
gnome-terminal -t "Tiled" -- scripts/start-tiled.sh
gnome-terminal -t "BSUI" -- scripts/start-bsui.sh
