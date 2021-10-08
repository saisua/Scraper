# Local cimports
from Browser import Browser

# Internal imports

# External imports

# Internal cimports
cimport cython

from libcpp.string cimport string as cstr
from libcpp cimport unordered_set as cuset
from libcpp cimport unordered_map as cumap

from cython.operator cimport dereference, postincrement



# C++ extern generates function returns hash int from string

cdef class Server(Browser):
    # static attr with string of sharable attributes
    cdef cuset[cstr, unsigned int] sharable
    cdef cumap[str, str] sharable_return

    # Process (with threads) instances and keeps up with the
    # Clients requests

    # function on_connect sends necessary initial data over tcp

    # Communications' different requests will be differentiated by
    # a regex finditer onto (.*?[^\\])&

    # a)
    # on request, get the hash (uint) send the version of the data

    # on request, get the hash (uint) and send the serialized data,
    # Along a integer with the current version of the var

    # b)
    # on request, a tuple of pairs is sent with the values of
    # (hash, version/tuple of args)
    # the server either 
    # 1- returns a int flags of which attributes are
    #       outdated, skipping functions and
    #   1.1- Waits until client confirmation (int flags), 
    #           then generates and sents back
    #   1.2- Starts generating the data, and when done
    #       1.2.1- Waits until client confirmation (int flags)
    #       1.2.2- Sends it back
    # or
    # 2- directly sent the data, w/o outdated
    #
    # Performance considerations 
    #       (P=packet, C=copy of data)
    #       (%f=% of flags confirmated by the client)
    #       (%o=% of attributes outdated)                       | Total Ops,  best,        worst
    # 1.1-   1 midP + 2 smallP + %fo ( bigC + bigP )            |   5 ops   data size    nº packets
    # 1.2.1- 1 midP + 1 smallP + %o bigC + 1 smallP + %fo bigP  |   5 ops  packet size  copy useless
    # 1.2.2- 1 midP + 1 smallP + %o bigC + %o bigP              |   4 ops   ratio d-p   c+s useless
    # 2-     1 midP + %o bigC + %o bigP                         |   3 ops  straightfwd  c+s useless
    #
    # Prolly the best would be to generate a static predictor / optimizer based on
    # the (size / data + previous decisions) to decide either on client or server side, 
    # which path to go

cdef class Client(Browser):
    # for every attribute that has to be proxied, generates
    # a attribute for its name hash value, and the version number
    # hashes are generated on the Client side to release as much
    # strain in the Server as possible

    # When a proxied attribute is accessed, the attribute barrier
    # is locked. ROB-like structure for reactivating process?

    # Ideally, all access for base features should be done by
    # gathering a list of requests, running each native function
    # (which should, in theory always return a tuple of tuples)
    # written in the Server class. All functions must have a hash too

    # Communications' different requests will be differentiated by
    # a regex finditer onto (.*?[^\\])&

    cdef tuple attr_locks

    def __init__(self):
        self.locks = (self._manager.Lock() for _ in Server.shared.size())


###
# Default static class values
# Server:
Server.shared = iter((b'example',))
Server.sharable_return = iter((("example", "int"),))

###


# Dangerous zone, dynamic generation of proxy-obj
# connection functions
def generate():
    def client_f(count, name, ret):
        cdef bytes bname = bytes(name, 'utf-8')
        def func1(self) -> ret:
            self.attr_locks[count].acquire()
            a = self._get_proxy_var(bname)
            self.attr_locks[count].release()
            
            return a
        
        func1.__name__ = name
        return func1

    cdef cumap[cstr,queue[cstr]].iterator attr_pair = Server.sharable.begin()
    cdef cumap[cstr,queue[cstr]].iterator attr_end = Server.sharable.end()
    cdef str attr_name, attr_return

    cdef unsigned int count = 0
    # iterate over all entries of the unordered_map
    while(attr_pair != attr_end): 
        # Get the attribute name
        attr_name = bytes(dereference(attr_pair).first).decode("utf-8")
        attr_return = Server.sharable_return[attr_name]

        # Generate proxy functions on the Client
        setattr(Client, attr_name, 
                    property(
                        client_f(count, attr_name, attr_return)))
        
        postincrement(attr_pair)
        count += 1
        
generate()