#!/usr/bin/env python3


import sys, time

LOGFILE_STR = "../log/node_{}.log"
INFILE_STR = "../out/input_{}"
OUTFILE_STR = "../out/output_{}"
RCVFILE_STR = "../out/{R}_received_from_{S}"
INIT_ERROR_STR = (
    "Incorrect argument length. Expected: `./node.py node-id [mode] [string] duration`."
)
FILE_WRITE_FAIL_STR = "Failed to write to file: {} -> will retry"
SENDER = "sender"
RECEIVER = "receiver"

MAX_NODES = 10
INFINITY = 99999
EXPIRY_TIME = 30  # no longer neighbor if no hello for more than `30 seconds`
HELLO_MSG = "hello {sender}"
DVECTOR_MSG = "dvector {sender} {origin} {out_distances} in-neighbors {in_neighbors}"
DVECTOR_MSG_FLOOD = "dvector {sender} {original}"
IN_DIST_MSG = "in-distance {sender} {in_distances}"
JOIN_MSG = "join {RID} {SID} {PID} {NID}"
DATA_MSG = "data {sender} {root} {string}"


class RoutingTable:
    def __init__(self, id) -> None:
        self.id = id
        self.in_distances = [INFINITY] * MAX_NODES
        self.out_distances = [INFINITY] * MAX_NODES
        self.out_next_hop = [None] * MAX_NODES
        self.in_prev_hop = [None] * MAX_NODES
        self.last_refresh = [0] * MAX_NODES
        self.in_distances[id] = 0
        self.out_distances[id] = 0

    def get_in_neighbors(self) -> str:
        return " ".join(
            [str(id) for id in range(MAX_NODES) if self.in_distances[id] != INFINITY]
        )

    def get_in_distance_msg(self) -> str:
        return IN_DIST_MSG.format(
            sender=self.id, in_distances=" ".join(map(str, self.in_distances))
        )

    def get_dvector_msg(self) -> str:
        # create this message for the first time => orginator==sender
        return DVECTOR_MSG.format(
            sender=self.id,
            origin=self.id,
            out_distances=" ".join(map(str, self.out_distances)),
            in_neighbors=self.get_in_neighbors(),
        )

    def add_in_neighbor(self, id: int, current_time: int) -> None:
        self.in_distances[id] = 1
        self.in_prev_hop[id] = id
        self.last_refresh[id] = current_time
        # TODO any further processing required?

    def process_in_distance_msg(self, message: str) -> None:
        message_split = message.split()
        sender = int(message_split[1])
        sender_in_dist = [int(d) for d in message_split[2:]]
        for id in range(MAX_NODES):
            dist = sender_in_dist[id]
            curr = self.in_distances[id]
            prev_hop = self.in_prev_hop[id]
            if dist == INFINITY:
                continue
            if curr == INFINITY or (dist + 1) < curr:
                self.in_distances[id] = dist + 1
                self.in_prev_hop[id] = sender
                continue
            # TODO: check if we really need this case
            if (dist + 1) == curr and sender < prev_hop:
                # tie break with lower ID
                self.in_prev_hop[id] = sender


class Neighbor:

    def __init__(self, id, distance, time) -> None:
        self.id = id
        self.distance = distance  # hops
        self.last_refresh_time = time

    def updateTime(self, time) -> None:
        self.last_refresh_time = time


class Node:

    def __init__(self):

        self.id = None
        self.mode = None
        self.duration = None
        self.string = None
        self.senderId = None
        self.logfile = None
        self.read_index = 0
        self.routing_table = None

        match (len(sys.argv)):
            case 3:
                # neither sender/receiver -> only duration
                try:
                    self.id = int(sys.argv[1])
                    self.duration = int(sys.argv[2])
                    self.logfile = open(LOGFILE_STR.format(self.id), "wt")
                except:
                    print(INIT_ERROR_STR)
                    exit(1)

            case 5:
                # node is a sender or receiver
                try:
                    self.id = int(sys.argv[1])
                    self.duration = int(sys.argv[4])
                    self.logfile = open(LOGFILE_STR.format(self.id), "wt")
                except:
                    print(INIT_ERROR_STR)
                    exit(1)

                self.mode = sys.argv[2]
                if self.mode == SENDER:
                    self.string = sys.argv[3]
                elif self.mode == RECEIVER:
                    try:
                        self.senderId = int(sys.argv[3])
                    except:
                        self.write_log(f"Invalid senderId: {sys.argv[3]}")
                        exit(1)
                else:
                    self.write_log(f"Invalid node mode: {sys.argv[2]}")
                    exit(1)

            case _:
                print(INIT_ERROR_STR)
                exit(1)

        # init routing table
        self.routing_table = RoutingTable(self.id)

        # log the config
        self.write_init_logs()

    def write_init_logs(self):
        self.write_log(f"*****STARTED NODE SERVICE*****")
        self.write_log(f"ID: {self.id}")
        self.write_log(f"Mode: {self.mode}")
        if self.mode == SENDER:
            self.write_log(f"Send String: '{self.string}'")
        if self.mode == RECEIVER:
            self.write_log(f"Sender ID: {self.senderId}")
        self.write_log(f"Duration: {self.duration}")

    def write_log(self, value=""):
        if type(value) != str:
            value = str(value)
        self.logfile.write(value + "\n")

    def write_out(self, value: str):
        done = False
        while not done:
            try:
                with open(OUTFILE_STR.format(self.id), "at") as f:
                    f.write(value + "\n")
                    done = True
            except:
                self.write_log(FILE_WRITE_FAIL_STR.format(OUTFILE_STR.format(self.id)))

    def send_hello(self, current_time: int):
        # send hello message, if it is time for another one
        if current_time % 5 == 0:
            self.write_out(HELLO_MSG.format(sender=self.id))

    def send_dvector(self, current_time: int):
        # send a "dvector" message if it is time to do so
        if current_time % 5 == 0:
            self.write_out(self.routing_table.get_dvector_msg())

    def send_in_distance(self, current_time: int):
        # send an "in-distance" message, if it is time to do so
        if current_time % 5 == 0:
            self.write_out(self.routing_table.get_in_distance_msg())

    def refresh_parent(self, current_time: int):
        # send join message to each parent of each tree I am involved in, if time to do so
        pass

    def read_input_file(self, current_time: int):
        # read the input file and process each new message received
        messages = None
        try:
            with open(INFILE_STR.format(self.id), "rt") as f:
                messages = f.readlines()
        except:
            self.write_log("Could not read this node's input file")
        if messages:
            filtered = messages[self.read_index :]
            if len(filtered) > 0:
                self.read_index = len(messages)
                for msg in filtered:
                    self.process_message(msg, current_time)

    def process_message(self, message: str, current_time: int):
        # process individual incoming message
        self.write_log(f"Processing message: {message}")
        match message.split()[0]:
            case "hello":
                hello_from = int(message.split()[1])
                self.routing_table.add_in_neighbor(hello_from, current_time)

            case "in-distance":
                self.write_log(
                    f"Before: Distance: {self.routing_table.in_distances} PrevHop: {self.routing_table.in_prev_hop}"
                )
                self.routing_table.process_in_distance_msg(message)
                self.write_log(
                    f"After: Distance: {self.routing_table.in_distances} PrevHop: {self.routing_table.in_prev_hop}"
                )

            case _:
                self.write_log(f"Unhandled message: {message}")

    def execute(self):
        for current_time in range(self.duration):
            self.write_log(f"=============Processing for t={current_time}")
            self.send_hello(current_time)
            self.send_dvector(current_time)
            self.send_in_distance(current_time)
            self.refresh_parent(current_time)
            self.read_input_file(current_time)
            time.sleep(1)

    def __del__(self):
        if self.logfile:
            self.write_log("****END****")
            self.logfile.close()


if __name__ == "__main__":
    Node().execute()


def parse_dvector():
    pass
