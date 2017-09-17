#
# Maglev Hashing Codes
#
# author: zhangchaowei
#

import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

# max size of lookup table size
max_lookup_tab_size = 65537

# node name hashing function
def str_hash(name):
    return abs(hash(name))

class maglev_hash:
    backends_num = 13   # => N
    lookuptab_size = 5  # => M
    permutation = []    # => prefer list
    lookuptab = []      # => lookup table
    backend_list = []   # => backend list
    def __init__(self, nodes, lookup_size):
        self.backends_num = len(nodes)
        self.lookuptab_size = lookup_size
        self.backend_list = [ backend for backend in nodes ]
        self.generatePopulation()
        self.populate()
    def add_node(self, new_node):
        if new_node in self.backend_list:
            print("node " + new_node + " is found in existing list")
            return
        self.backend_list.append(new_node)
        self.backends_num = len(self.backend_list)
        self.generatePopulation()
        self.populate()
    def del_node(self, node):
        if node not in self.backend_list:
            print("node ", node, " is not found in existing list")
            return
        self.backend_list.remove(node)
        self.backends_num = len(self.backend_list)
        self.generatePopulation()
        self.populate()
    def get_name(node):
        if (self.backends_num == 0):
            print("empty backend list")
            return None
        key = str_hash(node)
        return self.backend_list[ self.lookuptab[ key%self.lookuptab_size ] ]
    def generatePopulation(self):
        if 0 == self.backends_num:
            return
        for backend in self.backend_list:
            offset = str_hash(backend) % self.lookuptab_size
            skip = (str_hash(backend) % (self.lookuptab_size-1)) + 1
            iRows = []
            for j in range(self.lookuptab_size):
                # keypoint1: ==>
                iRows.append( (offset + j * skip) % self.lookuptab_size )
            self.permutation.append(iRows)
    def populate(self):
        if 0 == self.backends_num:
            return
        next_idx = [ 0 for i in range(self.backends_num) ]
        entry = [ -1 for i in range(self.lookuptab_size) ]
        filled_entry = 0
        # keypoint2 ==>
        while True:
            for idx_backend in range(self.backends_num):
                c = self.permutation[idx_backend][ next_idx[idx_backend] ]
                while entry[c] >= 0:
                    next_idx[idx_backend] += 1
                    c = self.permutation[idx_backend][next_idx[idx_backend]]
                entry[c] = idx_backend
                next_idx[idx_backend] += 1
                filled_entry += 1
                if filled_entry == self.lookuptab_size:
                    self.lookuptab = entry
                    return
    def debug_lookuptab(self, indent):
        print(indent + "debug lookup table content: ")
        lookup = self.get_node_in_lookuptab()
        print(indent*2+ str(lookup) )
        # for i in self.lookuptab:
            # print(indent*2 + str(i) + " <--> " + self.backend_list[ i ])
    def get_node_in_lookuptab(self):
        return [ self.backend_list[node] for node in self.lookuptab ]
    def debug_print_maglev(self, indent):
        print(indent + ("nodes number: %d" % self.backends_num))
        for i in range(self.backends_num):
            print(indent*2 + self.backend_list[i] + ": prefer list => " + str(self.permutation[i]) )
        self.debug_lookuptab(indent)

def show_in_text_format(lookup_size, nodes_num):
    # test case
    indent = "    "
    nodes = []
    for i in range(nodes_num):
        nodes.append("backend-%d" % i)
    test1 = maglev_hash(nodes, lookup_size)
    print("init backend set info: ")
    test1.debug_print_maglev(indent)

    # add a new node
    nodes.append("backend-%d" % nodes_num)
    nodes_num += 1
    test1.add_node( nodes[-1] )
    print("====== add a new node ======")
    test1.debug_print_maglev(indent)

    # remove a existing node
    test1.del_node(nodes[-1])
    print("====== remove an existing node ======")
    test1.debug_print_maglev(indent)

def show_in_char_format(lookup_size, init_nodes):
    nodes = []
    for i in range(init_nodes):
        nodes.append("backend-%d" % i)
    test1 = maglev_hash(nodes, lookup_size)
    prev_lookup = test1.get_node_in_lookuptab()
    curr_loopup = None
    # add new node until (numbaer of node) is equal to (number of lookup table)
    y_num_diff = [lookup_size]
    x_num_nodes = [init_nodes]
    while init_nodes < lookup_size:
        test1.add_node( "backend-%d" % init_nodes )
        curr_loopup = test1.get_node_in_lookuptab()
        i, n = 0, 0
        while i < lookup_size:
            if prev_lookup[i] != curr_loopup[i]:
                n += 1
            i += 1
        y_num_diff.append(n)
        prev_lookup = curr_loopup
        init_nodes += 1
        x_num_nodes.append(init_nodes)
    # print x_num_nodes
    # print y_num_diff
    # show its figure
    fig = plt.figure()
    plt.bar(x_num_nodes, y_num_diff, 0.4, color="green")
    plt.xlabel("number of nodes")
    plt.ylabel("number of distributes")
    plt.title("Maglev Hashing")
    plt.show()
    # plt.savefig("maglev_hash_bar1.jpg")

if __name__ == '__main__':
    show_in_text_format(13, 5)
    show_in_char_format(13, 1)