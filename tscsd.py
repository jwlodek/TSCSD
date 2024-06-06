#!/usr/bin/env python3

import argparse
import threading
import socket
import time

from sys import platform

if platform != "win32":
    import readline

# Configure logging
import logging
logging.basicConfig()


# Some global constants
TOLERANCE=0.1
MIN_RAMP_RATE=0.0001

# Version number
__version__="0.0.3"


class Channel:
    """Simple class that simulates a scalar device that can ramp up/down like a temp controller"""

    def __init__(self, id, logger, rr=1, max_rr=5, max_val=100, min_val = -100):
        self._id = id
        self._logger = logger
        self._at_rest = True
        self._rb = 0
        self._sp = 0
        self._rr = rr
        self._max_rr = max_rr
        self._max_val = max_val
        self._min_val = min_val
        self._keep_alive = True
        self._channel_thread = threading.Thread(target=self.run) # Create seperate thread for simulation
        self._channel_thread.start()


    def kill(self):
        """Cleans up simulation thread"""

        self._keep_alive = False
        self._logger.info(f"Shutting down channel {self._id}...")
        self._channel_thread.join()
        self._logger.info(f"Channel {self._id} shut down.")


    def run(self):
        """Simulation loop function run in seperate thread"""

        while self._keep_alive:

            # Check if our readback value is within tolerance of setpoint
            if abs(self._sp - self._rb) > TOLERANCE:
                self._at_rest = False
                if self._sp > self._rb:
                    self._rb += self._rr
                else:
                    self._rb -= self._rr
            else:
                self._at_rest = True

            # Make sure we don't overshoot our min/max ranges
            if self._rb > self._max_val:
                self._rb = self._max_val
            elif self._rb < self._min_val:
                self._rb = self._min_val

            # Poll rate
            time.sleep(1)


    def set_rr(self, rr):
        """Update ramp rate as long as within min/max tolerance"""

        if rr > self._max_rr:
            self._rr = self._max_rr
        elif rr < 0:
            self._rr = MIN_RAMP_RATE
        else:
            self._rr = rr


    def get_rr(self):
        """Returns current ramp rate"""

        return self._rr


    def is_at_rest(self):
        """Checks if channel is currently moving"""

        return self._at_rest


    def set(self, target):
        """Sets the target setpoint"""

        if target > self._max_val:
            self._sp = self._max_val
        elif target < self._min_val:
            self._sp = self._min_val
        else:
            self._sp = target


    def read(self):
        """Returns the current position"""

        return self._rb


class SimpleDevice:
    """Class that simulates a simple serial device"""

    def __init__(self, nchannels = 4, intf='127.0.0.1', port=8888, in_term='\n', out_term='\n', log_level = logging.INFO):

        # Configure logger
        self._logger = logging.getLogger(name="TSCSD")
        self._logger.setLevel(log_level)

        self._model = "Simple EPICS Training Device"
        self._socket_conn = None
        self._intf = intf
        self._port = port

        # Create main seperate thread for comms
        self._comm_thread = threading.Thread(target=self.communicate)

        self._keep_alive = True
        self._channels = []
        self._in_term = in_term
        self._out_term = out_term

        # Create individual channels
        for i in range(nchannels):
            self._channels.append(Channel(i, self._logger))

        # Supported commands
        self._cmd_to_func_map = {
            "KILL": [self.kill],
            "*IDN?": [lambda : f"{self._model} | {__version__}"],
            "NCHAN?": [lambda : str(len(self._channels))],
            "READ?": [self.get_chan_val, "Channel Num"],
            "SP": [self.set_chan_sp, "Channel Num", "Set Point"],
            "RR?": [self.get_chan_rr, "Channel Num"],
            "RR":  [self.set_chan_rr, "Channel Num", "Ramp Rate"],
            "ATSP?": [self.is_chan_at_rest, "Channel Num"],
            "STOP": [self.stop_channel, "Channel Num"],
            "DEBUG": [self.adjust_log_level, "Log Level"],
        }


    def stop_channel(self, chan_num):
        """Sets setpoint to current channel readback"""

        rb = self.get_chan_val(chan_num)
        self._channels[int(chan_num) - 1].set(float(rb))
        return self.is_chan_at_rest(chan_num)


    def get_chan_val(self, chan_num):
        """Get channel value"""

        return self._channels[int(chan_num) - 1].read()


    def set_chan_sp(self, chan_num, set_point):
        """Sets target setpoint for channel"""

        self._channels[int(chan_num) - 1].set(float(set_point))
        return f"SP{chan_num}={self._channels[int(chan_num) - 1]._sp}"


    def is_chan_at_rest(self, chan_num):
        """Checks if channel is at rest"""

        return "1" if self._channels[int(chan_num) - 1].is_at_rest() else "0"


    def get_chan_rr(self, chan_num):
        """Get channel ramprate"""

        return f"RR{chan_num}={self._channels[int(chan_num) - 1].get_rr()}"


    def set_chan_rr(self, chan_num, rr):
        """Sets channel ramp rate"""

        self._channels[int(chan_num) - 1].set_rr(float(rr))
        return self.get_chan_rr(chan_num)


    def adjust_log_level(self, log_level):
        """Adjusts level of logging"""

        if int(log_level) in range(0, 6):
            # Logging log levels go in increments of 10 from 0 to 50
            self._logger.setLevel(int(log_level) * 10)
            self._logger.info("Updated log level")
        else:
            self._logger.error(f"Log level {log_level} invalid!")


    def power_on(self):
        """Start the communications"""

        self._comm_thread.start()


    def kill(self):
        """Shut down all channel threads and stop main comms thread"""
        self._keep_alive = False
        self._logger.info("Shutting down device...")
        for channel in self._channels:
            channel.kill()

        self._logger.info("Done.")


    def rec_cmd(self, client_socket):
        """Function responsible for recieving command over socket connection"""

        command = None
        while self._keep_alive:
            try:
                command = client_socket.recv(48).decode('utf-8') # Commands are all short, under 48 chars
                if command == '':
                    raise RuntimeError("socket connection broken")
                self._logger.debug(f"Recieved {command.strip()} command.")
            except socket.timeout:
                pass
        if command is not None:
            return command.strip()
        else:
            return None


    def wait_for_conn(self):
        """Function that creates our socket, and waits for connection"""

        # If socket was already open, close it
        if self._socket_conn is not None:
            self._logger.info("Closing socket, making new one...")
            self._socket_conn.close()

        # Create socket and bind to specified intf/port
        self._socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # for quick restarts
        self._socket_conn.bind((self._intf, self._port))
        self._socket_conn.listen(1)
        self._socket_conn.settimeout(5.0)

        # Loop until either killed or connected and wait for connection.
        connected = False
        while self._keep_alive and not connected:
            try:
                (client_socket, address) = self._socket_conn.accept()
                client_socket.settimeout(5.0)
                self._logger.info(f"Connected to client w/ address {address}...")
                connected = True
                return client_socket
            except socket.timeout:
                pass


    def communicate(self):
        """Function responsible for main comms loop for simple device"""

        self._logger.info("Starting simple device...")
        client_socket = self.wait_for_conn()
        while self._keep_alive:
            try:
                command = self.rec_cmd(client_socket)
                if command is not None:
                    output = self.execute_command(command.split(' '))
                    if output is not None:
                        self._logger.debug(output)
                        client_socket.sendall(str.encode(f"{output}{self._out_term}"))
            except RuntimeError as e:
                self._logger.error("Socket disconnected. Waiting for new connection...")
                client_socket = self.wait_for_conn()


    def execute_command(self, command_as_list):
        """Executes the selected command"""

        base_cmd = command_as_list[0] # Base command is what we use to find function pointer from dict
        
        if base_cmd.strip() == "":
            pass # Ignore empty commands, so user can spam enter to get 
        else:
            if base_cmd not in self._cmd_to_func_map: # Make sure the command is in the dict
                self._logger.error(f"Command {base_cmd} not supported!")
            else:
                cmd_func_sig = self._cmd_to_func_map[command_as_list[0]]
                if len(cmd_func_sig) - 1 != len(command_as_list) - 1: # Check if we have correct # of args
                    self._logger.error(f"Command {command_as_list[0]} requires {len(cmd_func_sig) - 1} arguments!")
                else:
                    try:
                        output = self._cmd_to_func_map[base_cmd][0](*command_as_list[1:]) # Run command with args
                    except Exception as e:
                        self._logger.error(f"Failed to exectue {base_cmd} command! - {str(e)}")
                    if output is not None:
                        return output
        return None


    def show_simple_shell(self):
        """Blocking loop that allows for sending commands within the device"""

        try:
            while self._keep_alive:
                cmd = input("> ")
                cmd_w_args = cmd.split(' ')
                output = self.execute_command(cmd_w_args)
                if output is not None:
                    self._logger.info(output)

        except KeyboardInterrupt:
            self.kill()


def main():
    parser = argparse.ArgumentParser("Training Simple Control Systems Device")
    parser.add_argument("-i", "--intf", default="127.0.0.1", help="The network interface on which the socket should bind")
    parser.add_argument("-p", "--port", default=8888, type=int, help="Port number for socket to bind to")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable full debug logging")
    parser.add_argument("-n", "--nchannels", default=4, type=int, help="Number of simulated channels")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    sd = SimpleDevice(intf=args.intf, port=args.port, nchannels=args.nchannels, log_level=log_level)
    sd.power_on()
    sd.show_simple_shell()


if __name__ == "__main__":
    main()