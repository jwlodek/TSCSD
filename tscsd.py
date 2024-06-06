#!/usr/bin/env python3

import threading
import socket
import time

TOLERANCE=0.1

MIN_RAMP_RATE=0.0001

__version__="0.0.1"


class Channel:

    def __init__(self, id, rr=1, max_rr=5, max_val=100, min_val = -100):
        self._id = id
        self._at_rest = True
        self._rb = 0
        self._sp = 0
        self._rr = rr
        self._max_rr = max_rr
        self._max_val = max_val
        self._min_val = min_val
        self._keep_alive = True
        self._channel_thread = threading.Thread(target=self.run)
        self._channel_thread.start()

    def kill(self):
        self._keep_alive = False
        print(f"Shutting down channel {self._id}...")
        self._channel_thread.join()
        print(f"Channel {self._id} shut down.")

    def run(self):
        while self._keep_alive:
            if abs(self._sp - self._rb) > TOLERANCE:
                self._at_rest = False
                if self._sp > self._rb:
                    self._rb += self._rr
                else:
                    self._rb -= self._rr
            else:
                self._at_rest = True

            # Make sure we don't overshoot our ranges
            if self._rb > self._max_val:
                self._rb = self._max_val
            elif self._rb < self._min_val:
                self._rb = self._min_val

            time.sleep(1)

    def set_rr(self, rr):
        if rr > self._max_rr:
            self._rr = self._max_rr
        elif rr < 0:
            self._rr = MIN_RAMP_RATE
        else:
            self._rr = rr

    def get_rr(self):
        return self._rr

    def is_at_rest(self):
        return self._at_rest

    def set(self, target):
        if target > self._max_val:
            self._sp = self._max_val
        elif target < self._min_val:
            self._sp = self._min_val
        else:
            self._sp = target

    def read(self):
        return self._rb

class SimpleDevice:

    def __init__(self, nchannels = 4, intf='127.0.0.1', port=8888, in_term='\n', out_term='\n'):
        self._model = "Simple EPICS Training Device"
        self._socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # for quick restarts
        self._intf = intf
        self._port = port
        self._comm_thread = threading.Thread(target=self.communicate)
        self._keep_alive = True
        self._channels = []
        self._in_term = in_term
        self._out_term = out_term
        for i in range(nchannels):
            self._channels.append(Channel(i))

        self._cmd_to_func_map = {
            "KILL": [self.kill],
            "*IDN?": [self.identify],
            "NCHAN?": [lambda : str(len(self._channels))],
            "READ?": [self.get_chan_val, "Channel Num"],
            "SP": [self.set_chan_sp, "Channel Num", "Set Point"],
            "RR?": [self.get_chan_rr, "Channel Num"],
            "RR":  [self.set_chan_rr, "Channel Num", "Ramp Rate"],
            "ATSP?": [self.is_chan_at_rest, "Channel Num"],
            "STOP": [self.stop_channel, "Channel Num"]
        }

    def stop_channel(self, chan_num):
        rb = self.get_chan_val(chan_num)
        self._channels[int(chan_num) - 1].set(float(rb))
        return self.is_chan_at_rest(chan_num)

    def get_chan_val(self, chan_num):
        return self._channels[int(chan_num) - 1].read()

    def set_chan_sp(self, chan_num, set_point):
        self._channels[int(chan_num) - 1].set(float(set_point))
        return f"SP{chan_num}={self._channels[int(chan_num) - 1]._sp}"
   
    def get_chan_rr(self, chan_num):
        return f"RR{chan_num}={self._channels[int(chan_num) - 1].get_rr()}"
    

    def set_chan_rr(self, chan_num, rr):
        self._channels[int(chan_num) - 1].set_rr(float(rr))
        return self.get_chan_rr(chan_num)
    

    def is_chan_at_rest(self, chan_num):
        return "1" if self._channels[int(chan_num) - 1].is_at_rest() else "0"

    def power_on(self):
        self._comm_thread.start()

    def kill(self):
        self._keep_alive = False
        print("Shutting down device...")
        for channel in self._channels:
            channel.kill()
        
        print("Done.")


    def identify(self):
        return f"{self._model} | v{__version__}"

    def rec_cmd(self, client_socket):

        command = None
        saw_terminator = False
        while not saw_terminator and self._keep_alive:
            try:
                command = client_socket.recv(48).decode('utf-8')
                if self._in_term in str(command):
                    saw_terminator = True
                if command == '':
                    raise RuntimeError("socket connection broken")
                print(f"Recd {command.strip()} command.")
            except socket.timeout:
                print("Recd no cmd")
        if command is not None:
            return command.strip()
        else:
            return None
        

    def wait_for_conn(self):
        connected = False
        while self._keep_alive and not connected:
            try:
                (client_socket, address) = self._socket_conn.accept()
                client_socket.settimeout(5.0)
                print(f"Connected to client w/ address {address}...")
                connected = True
                return client_socket
            except socket.timeout:
                pass

    def communicate(self):
        self._socket_conn.bind((self._intf, self._port))
        self._socket_conn.listen(1)
        print("Starting simple device...")
        self._socket_conn.settimeout(5.0)
        client_socket = self.wait_for_conn()
        while self._keep_alive:
            try:
                command = self.rec_cmd(client_socket)
                if command is not None:
                    output = self.execute_command(command.split(' '))
                    if output is not None:
                        print(output)
                        client_socket.sendall(str.encode(f"{output}{self._out_term}"))
            except RuntimeError:
                print("Socket disconnected. Waiting for new connection...")
                self.wait_for_conn()

    def execute_command(self, command_as_list):
        base_cmd = command_as_list[0]
        if base_cmd == "":
            pass # Ignore empty commands
        else:
            if base_cmd not in self._cmd_to_func_map:
                print(f"Command {base_cmd} not supported!")
            else:
                cmd_func_sig = self._cmd_to_func_map[command_as_list[0]]
                if len(cmd_func_sig) - 1 != len(command_as_list) - 1:
                    print(f"Command {command_as_list[0]} requires {len(cmd_func_sig) - 1} arguments!")
                else:
                    output = self._cmd_to_func_map[base_cmd][0](*command_as_list[1:])
                    if output is not None:
                        return output
        return None

    def show_simple_shell(self):
        try:
            while self._keep_alive:
                cmd = input("> ")
                cmd_w_args = cmd.split(' ')
                output = self.execute_command(cmd_w_args)
                if output is not None:
                    print(output)

        except KeyboardInterrupt:
            self.kill()

if __name__ == "__main__":
    sd = SimpleDevice()
    sd.power_on()
    sd.show_simple_shell()
