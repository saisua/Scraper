'''cimport cython

from libcpp cimport bool as cbool
from libcpp.string cimport string as cstr
from libcpp.unordered_map cimport unordered_map as cumap # C-unordered map
from libcpp.map cimport map as comap # C-ordered map
from libcpp.vector cimport vector
from libcpp.queue cimport queue
from libcpp.iterator cimport iterator

cdef class Browser():
    """
    A browser site manager, with some data collection capabilities

    In case of using more than one browser it's highly recommended to open them all
    before running them
    """

    # Shared attributes
    cdef object visited_sites_counter # cmap[cstr, cmap[cstr, int]]

    # Unique per-machine
    cdef public object _manager # multiprocessing.Manager

    cdef object __unready_sites_lock # Manager.Lock
    cdef object __ready_sites_lock # Manager.Lock

    cdef queue[cstr] _unready_sites
    cdef queue[cstr] _ready_sites
    cdef vector[cstr] _timed_out_links

    cdef dict _flush_sites_counter

    cdef cumap[cstr, queue[cstr]] proxys

    # Strictly unique per-browser
    cdef public object driver # webdriver.Firefox
    cdef object interceptor # Interceptor

    cdef cumap[int, PyObject*] _site_from_tab # [ int, Site ]

    cdef cumap[cstr,int] config_index
    cdef cumap[int,cbool] configuration

    # Const values
    cdef int max_tabs
    cdef float load_timeout
    cdef float load_wait

    cdef Browser __enter__(self)

    cdef __exit__(self, object _, object __, object ___)

    # Open a new instance of the Browser
    # Called on with Browser as
    cdef open(self, object* options, object profile, object capabilities, 
                    object event_listener_obj,
                    cbool overwrite_config,
                    proxy_cmap proxys, cbool headless,
                    str gecko_path)

    # Close the browser's instance, threads
    # Called on with Browser as
    cdef close(self)

    @cython.boundscheck(False)
    cdef dict get_proxy(self, cbool http, cbool ssl, cbool ftp, cbool socks)

    @cython.boundscheck(False)
    cdef inline dict _cget_proxy(self, 
                cbool http, cbool ssl, cbool ftp, cbool socks)


    # Opens a new tab in the webdriver. Declaring using cdef
    # would be rather useless, since almost every call is to
    # a Python object and they require string args.
    cdef open_tab(self, str link)

    cdef open_tab_load(self, str link)

    cdef open_tabs(self, object links)

    cdef open_tabs_load(self, object links)

    # missing open_tab_log & close_tab_log

    cdef close_current_tab(self)

    cdef close_tab(self, str tab)

    cdef close_tabs(self, object tabs)

    # Used to access the lock and get sites to be loaded
    # There is an inline, but the size of the loop depends exclusively
    # on the arg number
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline vector[cstr]* _get_unready_sites(self, unsigned int number)

    # Used to access the lock and get loaded sites.
    # Can be accessed from python to be used as a lib.
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline vector[cstr]* _cget_ready_sites(self, unsigned int number)

    # Used to access the lock and get loaded sites.
    # Can be accessed from python to be used as a lib.
    @cython.wraparound(False)
    @cython.boundscheck(False)
    cdef list get_ready_sites(self, unsigned int number)

    # Add one site to be opened and processed when avaliable
    # Ideally, use extend_sites
    cdef append_site(self, str site)

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline int _cappend_site(self, cstr site) nogil

    # Add multiple sites to be opened and processed when avaliable
    cdef extend_sites(self, list sites)

    # Add multiple sites to be opened and processed when avaliable
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline int _cextend_sites(self, vector[cstr] sites)
'''