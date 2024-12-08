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
MAX_RANGE = range(MAX_NODES)
INFINITY = -1
EXPIRY_TIME = 30  # no longer neighbor if no hello for more than `30 seconds`
HELLO_MSG = "hello {sender}"
DVECTOR_MSG = "dvector {sender} {origin} {out_distances} in-neighbors {in_neighbors}"
DVECTOR_MSG_FLOOD = "dvector {sender} {original}"
IN_DIST_MSG = "in-distance {sender} {in_distances}"
JOIN_MSG = "join {RID} {SID} {PID} {NID}"
DATA_MSG = "data {sender} {root} {string}"


class RoutingTable:
    def __init__(self, id) -> None:
        self.id: int = id
        self.in_distances: list[int] = [INFINITY] * MAX_NODES
        self.out_distances: list[int] = [INFINITY] * MAX_NODES
        self.out_next_hop: list[int] = [None] * MAX_NODES
        self.out_refresh: list[int] = [None] * MAX_NODES
        self.in_prev_hop: list[int] = [None] * MAX_NODES
        self.in_refresh: list[int] = [None] * MAX_NODES
        self.in_distances[id] = 0
        self.out_distances[id] = 0

    def get_in_neighbors_str(self) -> str:
        return " ".join([str(id) for id in MAX_RANGE if self.in_distances[id] == 1])

    def get_in_neighbors(self) -> list[int]:
        return [id for id, x in enumerate(self.in_distances) if x == 1]

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
            in_neighbors=self.get_in_neighbors_str(),
        )

    def refresh_in_neighbor(self, id: int, current_time: int) -> None:
        self.in_distances[id] = 1
        self.in_prev_hop[id] = id
        self.in_refresh[id] = current_time

    def purge_expired(self, current_time: int) -> None:
        for id in MAX_RANGE:
            if id == self.id:
                # skip self
                continue

            if (
                self.in_refresh[id]
                and (current_time - self.in_refresh[id]) > EXPIRY_TIME
            ):
                # did not receive hello from node `id` for more than EXPIRY_TIME seconds
                self.in_refresh[id] = None
                # self.in_distances[id] = INFINITY
                # self.in_prev_hop[id] = None

                # update other nodes who used this "id" to reach this node
                for in_id in MAX_RANGE:
                    if self.in_prev_hop[in_id] == id and id != self.id:
                        self.in_distances[in_id] = INFINITY
                        self.in_prev_hop[in_id] = None

            if (
                self.out_refresh[id]
                and (current_time - self.out_refresh[id]) > EXPIRY_TIME
            ):
                # did not receive hello from node `id` for more than EXPIRY_TIME seconds
                self.out_refresh[id] = None
                # self.out_distances[id] = INFINITY
                # self.out_next_hop[id] = None

                # update other nodes who used this "id" to reach this node
                for out_id in MAX_RANGE:
                    if self.out_next_hop[out_id] == id and id != self.id:
                        self.out_distances[out_id] = INFINITY
                        self.out_next_hop[out_id] = None

    def process_in_distance_msg(self, message: str) -> None:
        message_split = message.split()
        sender = int(message_split[1])
        sender_in_dist = [int(d) for d in message_split[2:]]
        for id in MAX_RANGE:
            if id == self.id:
                continue

            dist = sender_in_dist[id]
            curr = self.in_distances[id]
            prev_hop = self.in_prev_hop[id]
            if dist == INFINITY:
                if curr != INFINITY and prev_hop == sender:
                    # previously reachable through sender, but no longer
                    self.in_distances[id] = INFINITY
                    self.in_prev_hop[id] = None
                continue

            assert dist != INFINITY
            if curr == INFINITY or (dist + 1) < curr:
                if (dist + 1) < MAX_NODES:
                    self.in_distances[id] = dist + 1
                    self.in_prev_hop[id] = sender
                continue
            # TODO: check if we really need this case
            if (dist + 1) == curr and sender < prev_hop:
                # tie break with lower ID
                self.in_prev_hop[id] = sender

            assert curr != INFINITY
            if (dist + 1) > curr and self.in_prev_hop[id] == sender:
                # update new in distance
                if (dist + 1) >= MAX_NODES:
                    self.in_distances[id] = INFINITY
                    self.in_prev_hop[id] = None
                else:
                    self.in_distances[id] = dist + 1

    def update_out_distances(self, origin: int, origin_out_dist: list[int]) -> None:
        for id in MAX_RANGE:
            self_dist = self.out_distances[id]
            origin_dist = origin_out_dist[id]
            self_next_hop = self.out_next_hop[id]

            if origin_dist == INFINITY:
                # not reachable from origin node
                if self_dist != INFINITY and self_next_hop == origin:
                    # "id" no longer reachable through "origin"
                    self.out_distances[id] = INFINITY
                    self.out_next_hop[id] = None
                    for out_id in MAX_RANGE:
                        if self.out_next_hop[out_id] == id:
                            # remove subsequent nodes using "id" as next hop
                            self.out_distances[out_id] = INFINITY
                            self.out_next_hop[out_id] = None
                continue

            assert origin_dist != INFINITY
            if self_dist == INFINITY or (origin_dist + 1) < self_dist:
                if (origin_dist + 1) < MAX_NODES:
                    self.out_distances[id] = origin_dist + 1
                    self.out_next_hop[id] = origin
                continue
            if (origin_dist + 1) == self_dist and origin < self_next_hop:
                # tie breaker, update with lower ID
                self.out_next_hop[id] = origin

            assert self_dist != INFINITY
            if (origin_dist + 1) > self_dist and self_next_hop == origin:
                # update new in distance
                if (origin_dist + 1) >= MAX_NODES:
                    self.out_distances[id] = INFINITY
                    self.out_next_hop[id] = None
                else:
                    self.out_distances[id] = origin_dist + 1

    def process_dvector_msg(self, message: str, current_time: int) -> str:
        message_split = message.split()
        sender = int(message_split[1])
        origin = int(message_split[2])
        out_dist = [int(d) for d in message_split[3:13]]
        in_neighbors = [int(d) for d in message_split[14:]]

        # print(f"dvector processing: origin: {origin} in_neighbors: {in_neighbors}")

        # update this node's out distances if it is part of in-neighbors of origin
        if self.id in in_neighbors:
            self.update_out_distances(origin, out_dist)
            self.out_refresh[origin] = current_time

        # check if we have to flood
        if sender in self.get_in_neighbors() and sender == self.in_prev_hop[origin]:
            # sender is on shortest path from origin to this/current node
            DVECTOR_MSG_FLOOD = "dvector {sender} {original}"
            return DVECTOR_MSG_FLOOD.format(
                sender=self.id, original=" ".join(message_split[2:])
            )

        # do not have to flood if we reached here
        return None

    def get_parent_from_sender(self, sender_id):
        # if no path determined yet from sender_id to this node
        if self.in_distances[sender_id] == INFINITY:
            return None

        parent = self.in_prev_hop[sender_id]
        return parent


class Node:

    def __init__(self):

        self.id = None
        self.mode = None
        self.duration = None
        self.send_string = None
        self.sender_id = None
        self.logfile = None
        self.read_index = 0
        self.routing_table = None
        self.multicast_rt = None

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
                    self.send_string = sys.argv[3]
                elif self.mode == RECEIVER:
                    try:
                        self.sender_id = int(sys.argv[3])
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
        self.multicast_rt = MulticastRoutingTable(self.id, self)

        # log the config
        self.write_init_logs()

    def write_init_logs(self):
        self.write_log(f"*****STARTED NODE SERVICE*****")
        self.write_log(f"ID: {self.id}")
        self.write_log(f"Mode: {self.mode}")
        self.write_log(f"Duration: {self.duration}")
        self.write_log(
            f"\nINIT: IN Distance: {self.routing_table.in_distances} PrevHop: {self.routing_table.in_prev_hop}"
            + f"\nINIT: OUT: {self.routing_table.out_distances} NextHop: {self.routing_table.out_next_hop}\n\n"
        )
        if self.multicast_rt.node_mode == SENDER:
            self.write_log(f"Send String: '{self.multicast_rt.send_string}'")
        if self.multicast_rt.node_mode == RECEIVER:
            self.write_log(f"Sender ID: {self.multicast_rt.sender_id}")
            self.write_log(f"Multicast Table: {self.multicast_rt.info}")

    def write_log(self, value=""):
        if type(value) != str:
            value = str(value)
        if not value.endswith("\n"):
            value = value + "\n"
        self.logfile.write(value)

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
        if current_time % 5 == 0:
            # purge any expired entries in multicast routing table
            self.multicast_rt.purge_expired(current_time)
            msg = self.multicast_rt.get_join_messages()
            if msg:
                self.write_out(msg)
            self.write_log(f"MC TABLE: {self.multicast_rt.info}\n")

    def send_multicast_data(self, current_time: int):
        # data message if this node is a sender and every ten seconds
        if self.mode == SENDER and (current_time % 10) == 0:
            msg = DATA_MSG.format(sender=self.id, root=self.id, string=self.send_string)
            self.write_out(msg)

    def read_input_file(self, current_time: int):
        # read the input file and process each new message received
        messages = None
        try:
            with open(INFILE_STR.format(self.id), "rt") as f:
                messages = f.readlines()
        except:
            self.write_log("Could not read this node's input file")
        if messages:
            filtered = set(messages[self.read_index :])
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
                self.routing_table.refresh_in_neighbor(hello_from, current_time)

            case "in-distance":
                self.routing_table.process_in_distance_msg(message)
                self.write_log(
                    f"After: IN Distance: {self.routing_table.in_distances} PrevHop: {self.routing_table.in_prev_hop}\n"
                )

            case "dvector":
                flood_msg = self.routing_table.process_dvector_msg(
                    message, current_time
                )
                self.write_log(
                    f"After: OUT: {self.routing_table.out_distances} NextHop: {self.routing_table.out_next_hop}\n"
                )
                if flood_msg:
                    # output the message if it has to flood it
                    self.write_out(flood_msg)

            case "join":
                fwd_join_msg = self.multicast_rt.process_join_msg(message, current_time)
                self.write_log(f"MC TABLE: {self.multicast_rt.info}\n")
                if fwd_join_msg:
                    self.write_out(fwd_join_msg)

            case "data":
                fwd_data_msg = self.multicast_rt.process_data_msg(message)
                if fwd_data_msg:
                    self.write_out(fwd_data_msg)
                    self.write_log(f"Forwarding data message: {fwd_data_msg}\n")

            case _:
                self.write_log(f"Unhandled message: {message}")

    def execute(self):
        for current_time in range(self.duration):
            self.write_log(f"=============Processing for t={current_time}")
            self.send_hello(current_time)
            self.routing_table.purge_expired(current_time)
            self.send_dvector(current_time)
            self.send_in_distance(current_time)
            self.refresh_parent(current_time)
            self.send_multicast_data(current_time)
            self.read_input_file(current_time)
            time.sleep(1)

    def __del__(self):
        if self.logfile:
            self.write_log("****END****")
            self.logfile.close()


class MulticastTableEntry:

    def __init__(self, sender_id: int, receiver_id: int, last_refresh: int):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.last_refresh = last_refresh

    def __repr__(self):
        return f"(Receiver: {self.receiver_id} last_refresh: {self.last_refresh}"


class MulticastRoutingTable:

    def __init__(self, id: int, node: Node):
        self.id: int = id
        self.node_mode: str = node.mode
        self.unicast_rt: RoutingTable = node.routing_table
        self.info: dict[int, list[MulticastTableEntry]] = dict()

        if self.node_mode == SENDER:
            self.send_string = node.send_string
        if self.node_mode == RECEIVER:
            self.sender_id = node.sender_id
            self.info[self.sender_id] = [
                MulticastTableEntry(self.sender_id, self.id, 0)
            ]

    def purge_expired(self, current_time: int):
        for sender_id, entry_list in self.info.items():
            for entry in entry_list:
                if entry.receiver_id == self.id:
                    # this should only be true if this node is running in receiver mode
                    assert self.node_mode == RECEIVER
                    # update to current time and skip purge for this
                    entry.last_refresh = current_time
                    continue

            # retain only when curr-last_refresh <= 30
            updated_receivers = [
                entry
                for entry in entry_list
                if current_time - entry.last_refresh <= EXPIRY_TIME
            ]

            self.info[sender_id] = updated_receivers

        # retain sender_id records only for non-empty receiver list
        self.info = {
            sender_id: entries_list
            for sender_id, entries_list in self.info.items()
            if len(entries_list) > 0
        }

    def get_join_messages(self):
        join_messages: list[str] = []
        for sender_id in self.info.keys():
            # create join messages
            parent_id = self.unicast_rt.get_parent_from_sender(sender_id)
            if parent_id is None:
                # unreachable, skip join
                continue
            next_hop_id = self.unicast_rt.out_next_hop[parent_id]
            if next_hop_id is None:
                # unreachable, skip join
                continue

            # add join message to send
            join_messages.append(
                JOIN_MSG.format(
                    RID=self.id, SID=sender_id, PID=parent_id, NID=next_hop_id
                )
            )

        if len(join_messages) == 0:
            return None

        return "\n".join(join_messages)

    def process_join_msg(self, message: str, current_time: int) -> str | None:
        rid, sid, pid, nid = list(map(int, message.split()[1:]))
        if nid != self.id:
            # ignore this message, not for me
            return None

        if pid != self.id:
            # just need to fwd this to next hop
            next_hop_id = self.unicast_rt.out_next_hop[pid]
            return JOIN_MSG.format(RID=rid, SID=sid, PID=pid, NID=next_hop_id)

        # pid == nid == self.id
        entries: list[MulticastTableEntry] = self.info.get(sid, None)

        if not entries:
            # no record for sid, add fresh record
            self.info[sid] = [MulticastTableEntry(sid, rid, current_time)]
            return None

        # check for an existing entry with this receiver
        entry: MulticastTableEntry = next(
            (entry_itr for entry_itr in entries if entry_itr.receiver_id == rid), None
        )

        if entry:
            # existing entry found, just update last refresh
            entry.last_refresh = current_time
        else:
            # need to create entry in the multicast rt
            entries.append(MulticastTableEntry(sid, rid, current_time))

        return None

    def process_data_msg(self, message: str) -> str | None:
        message_split = message.split()
        sender = int(message_split[1])
        root = int(message_split[2])

        mc_entries: list[MulticastTableEntry] = self.info.get(root, None)
        if not mc_entries:
            # this node is not on the root's tree, ignore
            return None

        parent = self.unicast_rt.get_parent_from_sender(root)
        if sender != parent:
            # not from parent, ignore
            return None

        # sender == parent
        # 1. self_service
        # 2. fwd to children

        fwd_service = False
        for mc_entry in mc_entries:
            if mc_entry.receiver_id == self.id:
                # this node is the one of receiver, write the received string
                self.write_multicast_out(root, " ".join(message_split[3:]))
            else:
                # need to forward the packet to children on root's tree
                fwd_service = True

        if fwd_service:
            return DATA_MSG.format(
                sender=self.id, root=root, string=" ".join(message_split[3:])
            )

        # no forward service required
        return None

    def write_multicast_out(self, root: int, value: str):
        done = False
        while not done:
            try:
                with open(RCVFILE_STR.format(R=self.id, S=root), "at") as f:
                    f.write(value + "\n")
                    done = True
            except:
                pass


if __name__ == "__main__":
    Node().execute()
