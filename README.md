# TSCSD

**Training Simple Control System Device**

Simple python program that simulates a device with an ASCII command set that can be used for EPICS/StreamDevice training purposes.

### Starting the Simulation

To start the simulation, simply run the python script included. It will create a socket that by default binds to your localhost interface (`127.0.0.1`) and port `8888`. You can override these by passing the `--intf` and `--port` flags respectively.

For information about additional configuration options, you can run the script with the help flag:

```
./tscsd.py --help
```

### Command List

Note that below, `$CHAN` represents a channel number, meaning a number from 1 up to the total number of configured channels. `%S` is an arbitrary string, `%F` is an arbitrary float value, and `%D` is an arbitrary integer.


#### KILL

Stops all simulation threads and closes the socket.

#### *IDN?

Response Regex | Example Command | Example Response
----|-----|-------
`%S \| %D.%D.%D` | `*IDN?` | `EPICS Trainer \| 0.1.3`

Returns the simulation name, and the version number as three period-separated integers

#### NCHAN?

Response Regex | Example Command | Example Response
----|-----|-------
`%D` | `NCHAN?` | `4`

Returns the number of channels the simulation is configured for.

#### ATSP? $CHAN

Response Regex | Example Command | Example Response
----|-----|-------
`%D` | `ATSP? 2` | `1`

Returns a 1 if the simulated channel is at rest, otherwise returns 0.

#### RR? $CHAN

Response Regex | Example Command | Example Response
----|-----|-------
`RR$CHAN=%F` | `RR? 4` | `RR4=2.1`

Returns an echo of the command and channel number, and the current ramp rate for the channel

#### RR $CHAN %F

Response Regex | Example Command | Example Response
----|-----|-------
`RR$CHAN=%F` | `RR 1 3.4` | `RR1=3.4`

Sets the current ramp rate for the specified channel. Returns the same output as the `RR? $CHAN` command


#### READ? $CHAN

Response Regex | Example Command | Example Response
----|-----|-------
`%F` | `READ? 2` | `2.1`

Returns the current position for the specified channel.

#### SP $CHAN %F

Response Regex | Example Command | Example Response
----|-----|-------
`SP$CHAN=%F` | `SP 5 27.3` | `SP5=27.3`

Sets the setpoint for the channel. If it is different from the current readback, the channel will begin moving toward the setpoint at the given ramp rate. If the specified set point is outside of the limits of the simulation, the simulation will automatically set the value to the appropriate limit.