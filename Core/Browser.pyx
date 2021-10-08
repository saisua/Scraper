# Local cimports
from Settings.browser_configuration import get_configuration
from Utils.utils cimport to_cstring as to_cstr

# Internal imports
from multiprocessing import Manager
from multiprocessing.queues import Queue
from random import shuffle, randint

# External imports
from cython.parallel import prange
from selenium import webdriver

# Internal cimports
cimport cython

from libcpp cimport bool as cbool
from libcpp.string cimport string as cstr
from libcpp.unordered_map cimport unordered_map as cumap # C-unordered map
from libcpp.map cimport map as comap # C-ordered map
from libcpp.vector cimport vector
from libcpp.queue cimport queue
from libcpp.iterator cimport iterator

from libc.stdlib cimport malloc, free

from cpython.array cimport array
from cpython.ref cimport PyObject
from cython.operator cimport dereference, postincrement

from libc.time cimport time, time_t

# External declarations
cdef extern from "stdlib.h" nogil:
    double drand48()
    void srand48(long int seedval)

cdef extern from "time.h" nogil:
    long int time(int)

# Wrappers
cdef class proxy_cmap:
    cdef cumap[cstr, queue[cstr]]* _cmap

    def __cinit__(self):
        self._cmap = new cumap[cstr, queue[cstr]]()

        #for key, value in data.items():
        #    if(isinstance(key, cstr) and isinstance(value, queue)):
        #        self._cmap[<cstr>key] = <queue[cstr]>value

    def __del__(self):
        if(not (self._cmap is NULL)):
            del self._cmap

    def __dealloc__(self):
        if(not (self._cmap is NULL)):
            del self._cmap

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

    # Time (in ms) to wait to get new ready sites
    cdef vector[time_t] _unready_time
    cdef vector[cstr] _unready_sites
    cdef vector[cstr] _ready_sites
    cdef vector[cstr] _timed_out_links

    cdef dict _flush_sites_counter

    cdef cumap[cstr, queue[cstr]] proxys

    # Strictly unique per-browser
    cdef public object driver # webdriver.Firefox
    cdef object interceptor # Interceptor

    cdef cumap[int, PyObject*] _site_from_tab # [ int, Site ]
    cdef int num_tabs

    cdef cumap[cstr,int] config_index
    cdef cumap[int,cbool] configuration

    # Const values
    cdef int max_tabs
    cdef float load_timeout
    cdef float load_wait

    def __init__(self, list sites=[], float load_timeout=20.0,
                int max_tabs=25, cbool headless=False, 
                object manager=None,
                #cbool load_images=True, cbool autoload_videos=False,
                float load_wait=3, cbool disable_downloads=False, 
                proxy_cmap proxy_dict=proxy_cmap(), 
                cbool global_interceptor=False, 
                dict interceptor_kwargs={}
                ):
        """
            proxy_dict must be a unordered_map of structure:
                    {   
                        'socksProxy':queue[cstr](),
                        'httpProxy':queue[cstr](),
                        'ftpProxy':queue[cstr](),
                        'sslProxy':queue[cstr]()
                    }
        """
        
        ## Predefined attributes
        self.max_tabs = 25
        self.load_timeout = 30.0
        self.load_wait = 3.0
            
        ## Shared memory

        # Create a manager to create shared objects
        self._manager = manager or Manager()

        # Create ready_to_process and ready_to_use 
        # sites' Queue
        self._unready_time = vector[time_t]()
        self._unready_sites = vector[cstr]()
        self._ready_sites = vector[cstr]()

        # and their locks, to ensure process-safety
        self.__unready_sites_lock = self._manager.Lock()
        self.__ready_sites_lock = self._manager.Lock()

        # List to store timed out links
        self._timed_out_links = self._manager.list()
        
        # Store all visited sites and how many times it was visited
        self.visited_sites_counter = self._manager.dict()

        # All proxys to be accessed
        self.proxys = cumap[cstr, queue[cstr]]()

        # Set random generator
        srand48(time(0))

        # Define all needed variables outside the nogil
        # they are needed for the shuffling of the queues
        cdef cumap[cstr,queue[cstr]].iterator proxy_pair = <cumap[cstr,queue[cstr]].iterator>proxy_dict._cmap.begin()
        cdef cumap[cstr,queue[cstr]].iterator proxy_end = <cumap[cstr,queue[cstr]].iterator>proxy_dict._cmap.end()
        cdef queue[cstr] proxy_queue, temp_queue
        cdef int _

        with nogil:
            # iterate over all entries of the unordered_map
            while(proxy_pair != proxy_end):       

                # get the queue
                proxy_queue = dereference(proxy_pair).second

                # Shuffle the list (iterate over it twice + randomly hold elements)
                for _ in range(<int>(proxy_queue.size()*2)):
                    if(proxy_queue.size() and drand48() > 0.5):
                        temp_queue.push(proxy_queue.front())
                        proxy_queue.pop()
                    elif(temp_queue.size()):
                        proxy_queue.push(temp_queue.front())
                        temp_queue.pop()

                # Push any held elements
                for _ in range(temp_queue.size()):
                    proxy_queue.push(temp_queue.front())
                    temp_queue.pop()

                # Store the resulting queue in self.proxys
                self.proxys[dereference(proxy_pair).first] = proxy_queue
                postincrement(proxy_pair) # pair++

        # An interceptor proxy that will process all browsers' data
        # If disabled it can still be set up per-browser in self.open
        if(global_interceptor):
            pass
            #self.interceptor = Interceptor(self._manager, **interceptor_kwargs)

        ### PERFORMANCE settings

        # How many tabs per process will be able to open the browser
        # This setting affects severely the ram usage and speed of the crawling
        self.max_tabs = max_tabs

        # How much time wait before releasing a timeout exception on a site.
        # This setting can have false positives on low-conn networks, but
        # it is meant to close blank urls
        self.load_timeout = load_timeout

        self.load_wait = load_wait
        
    cpdef Browser __enter__(self):
        self.open()

        return self


    cpdef __exit__(self, object _, object __, object ___):
        self.close()

    # Open a new instance of the Browser
    # Called on with Browser as
    cpdef open(self, object options=None, object profile=None, object capabilities=None, 
                    object event_listener_obj=None,
                    cbool overwrite_config=True,
                    proxy_cmap proxys=None, cbool headless=False,
                    str gecko_path=f"{'//'.join(__file__.split('/')[:-1])}//..//geckodriver"):
        print(f"\n[?] Starting the opening of a Browser{' (headless)' if headless else ''}")

        if(not proxys is None): self.proxys = dereference(proxys._cmap)

        """
        if(enable_interceptor):
            if(self.interceptor is None):
                self.interceptor = interceptor_object or Interceptor(self._manager, **interceptor_kwargs)

            # Overwrite socksProxy. Once mitmproxy has support for
            # Socks5 & Upstream, redirect the mitmproxy
            self.proxys["socksProxy"] = [self.interceptor.address]
        """

        if(options is None or profile is None or capabilities is None or not overwrite_config):
            options2, profile2, capabilities2 = get_configuration(
                                    {"proxys":self._cget_proxy(http=True, ssl=True, ftp=True, socks=True)},
                                    options=options if not overwrite_config else None, 
                                    profile=profile if not overwrite_config else None, 
                                    capabilities=capabilities if not overwrite_config else None
                                )

            if(not overwrite_config or options is None):
                options = options2
            if(not overwrite_config or profile is None):
                profile = profile2
            if(not overwrite_config or capabilities is None):
                capabilities = capabilities2

            del options2, profile2, capabilities2


        print("Configuration complete. Trying to run the drivers. This could take some time...")
        try:
            self.driver = webdriver.Firefox(
                    executable_path=gecko_path,
                    options=options, firefox_profile=profile, capabilities=capabilities) 

            #self._profile = profile
                    
            print("[+] Drivers ran succesfully!")

        except Exception as ex:
            print(f"[-] Looks like something failed. Error message: {ex}")
            self.driver = webdriver.Firefox()

        
        if(not event_listener_obj is None):
            #self.driver = EventFiringWebDriver(self.driver, event_listener_obj)

            if(True):
                pass
                #self.driver.install_addon('//'.join(__file__.split('/')[:-1])+"//Extensions//duckduckgo-privacy-extension//extension.xpi",
                #                    temporary=False)
                #self.driver.install_addon('//'.join(__file__.split('/')[:-1])+"//Extensions//scraper-extension//scraper-extension.xpi",
                #                    temporary=False)
                
        
        ### Non-shared memory
        #self._site_from_tab = cumap[int, PyObject*]()
        self.num_tabs = 0


        self.driver.get("about:config")
        self.driver.execute_script("document.querySelector('button').click();")


        ### After driver configs
        self.driver.set_page_load_timeout(0)
        #self.driver.set_page_load_timeout(self.load_timeout)


        print("[?] New Browser opened")
        #print(self.driver.window_handles)

    # Close the browser's instance, threads
    # Called on with Browser as
    cpdef close(self):
        self.driver.quit()

        if(not self.interceptor is None):
            self.interceptor.close()

    @cython.boundscheck(False)
    cpdef dict get_proxy(self, cbool http=False, cbool ssl=False, cbool ftp=False, cbool socks=False):
        cdef dict result = {}
        cdef cumap[cstr, queue[cstr]].iterator proxy_found
        cdef queue[cstr] proxy_list

        # GIL cannot be disabled

        if(http):
            proxy_found = self.proxys.find(to_cstr("httpProxy"))
            if(proxy_found != self.proxys.end()):
                proxy_list = dereference(proxy_found).second

                if(not proxy_list.empty()):
                    result["httpProxy"] = proxy_list.front()

                    proxy_list.push(proxy_list.front())
                    proxy_list.pop()

        if(ssl):
            proxy_found = self.proxys.find(to_cstr("sslProxy"))
            if(proxy_found != self.proxys.end()):
                proxy_list = dereference(proxy_found).second

                if(not proxy_list.empty()):
                    result["sslProxy"] = proxy_list.front()

                    proxy_list.push(proxy_list.front())
                    proxy_list.pop()

        if(ftp):
            proxy_found = self.proxys.find(to_cstr("ftpProxy"))
            if(proxy_found != self.proxys.end()):
                proxy_list = dereference(proxy_found).second

                if(not proxy_list.empty()):
                    result["ftpProxy"] = proxy_list.front()

                    proxy_list.push(proxy_list.front())
                    proxy_list.pop()

        if(socks):
            proxy_found = self.proxys.find(to_cstr("socksProxy"))
            if(proxy_found != self.proxys.end()):
                proxy_list = dereference(proxy_found).second

                if(not proxy_list.empty()):
                    result["socksProxy"] = proxy_list.front()

                    proxy_list.push(proxy_list.front())
                    proxy_list.pop()

        return result

    @cython.boundscheck(False)
    cdef inline dict _cget_proxy(self, 
                cbool http=False, cbool ssl=False, cbool ftp=False, cbool socks=False):
        cdef cumap[cstr, cstr] result = cumap[cstr, cstr]()
        cdef cumap[cstr, queue[cstr]].iterator proxy_found
        cdef queue[cstr] proxy_list
        
        cdef cstr httpP = to_cstr("httpProxy")
        cdef cstr sslP = to_cstr("sslProxy")
        cdef cstr ftpP = to_cstr("ftpProxy")
        cdef cstr socksP = to_cstr("socksProxy")

        with nogil:
            if(http):
                proxy_found = self.proxys.find(httpP)
                if(proxy_found != self.proxys.end()):
                    proxy_list = dereference(proxy_found).second

                    if(not proxy_list.empty()):
                        result[httpP] = proxy_list.front()

                        proxy_list.push(proxy_list.front())
                        proxy_list.pop()

            if(ssl):
                proxy_found = self.proxys.find(sslP)
                if(proxy_found != self.proxys.end()):
                    proxy_list = dereference(proxy_found).second

                    if(not proxy_list.empty()):
                        result[sslP] = proxy_list.front()

                        proxy_list.push(proxy_list.front())
                        proxy_list.pop()

            if(ftp):
                proxy_found = self.proxys.find(ftpP)
                if(proxy_found != self.proxys.end()):
                    proxy_list = dereference(proxy_found).second

                    if(not proxy_list.empty()):
                        result[ftpP] = proxy_list.front()

                        proxy_list.push(proxy_list.front())
                        proxy_list.pop()

            if(socks):
                proxy_found = self.proxys.find(socksP)
                if(proxy_found != self.proxys.end()):
                    proxy_list = dereference(proxy_found).second

                    if(not proxy_list.empty()):
                        result[socksP] = proxy_list.front()

                        proxy_list.push(proxy_list.front())
                        proxy_list.pop()

        return result


    # Opens a new tab in the webdriver. Declaring using cdef
    # would be rather useless, since almost every call is to
    # a Python object and they require string args.
    cpdef open_tab(self, str link):
        self.driver.switch_to.window(self.driver.window_handles[0])

        self.driver.execute_script(f"window.open('{link}');")

    cpdef open_tab_load(self, str link):
        self.open_tab(link)
         
        cdef object handles_iter = iter(self.driver.window_handles)
        cdef str current_handle = self.driver.current_window_handle

        # Find current window handle
        while(next(handles_iter) != current_handle): pass

        # The new window handle is the last one + 1
        self._cappend_site(to_cstr(next(handles_iter)))

    cpdef open_tabs(self, object links):
        self.driver.switch_to.window(self.driver.window_handles[0])

        cdef str link
        for link in links:
            self.driver.execute_script(f"window.open('{link}');")

    cpdef open_tabs_load(self, object links):
        self.open_tabs(links)

        cdef int tab_num = len(links)
        cdef vector[cstr] tabs = vector[cstr](tab_num)

        cdef object handles_iter = iter(self.driver.window_handles)
        cdef str current_handle = self.driver.current_window_handle  

        # Find current window handle
        while(next(handles_iter) != current_handle): pass

        # The new window handle is the last one + n
        while(tab_num > 0):
            tabs[tab_num] = next(handles_iter)
            tab_num -= 1
        
        # Pass the tabs to the loading function
        self._cextend_sites(tabs)

    # missing open_tab_log & close_tab_log

    cpdef close_current_tab(self):
        self.driver.execute_script("window.close();")

    cpdef close_tab(self, str tab):
        self.driver.switch_to.window(tab);

        self.driver.execute_script("window.close();")

    cpdef close_tabs(self, object tabs):
        for tab in tabs:
            self.driver.switch_to.window(tab);

            self.driver.execute_script("window.close();")

    # Used to access the lock and get sites to be loaded
    # There is an inline, but the size of the loop depends exclusively
    # on the arg number
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline vector[cstr]* _get_unready_sites(self, unsigned int number = 1):
        
        # define to-be-used vars to reduce the time
        # the lock is locked
        cdef vector[cstr] result = vector[cstr](number)
        cdef unsigned int site = 0 

        cdef vector[cstr] u_sites = self._unready_sites

        number = number if number < self._unready_sites.size() else self._unready_sites.size()

        # Acquire the lock to ensure safety
        self.__unready_sites_lock.acquire()

        with nogil:
            while(site != number):
                result[site] = u_sites.front()
                u_sites.pop()
                site += 1

        self.__unready_sites_lock.release()

        return &result

    cdef _check_unready_sites(self) nogil:
        #size_t step = self._unready_time.size() // 4 or 1
        #size_t ready_search_point = ((self._unready_time.size() // 2) or 1)

        size_t step = 1
        size_t ready_search_point = 1

        time_t now = time(NULL)

        # Block while we search and remove
        self.__unready_sites_lock.acquire()

        while(step):
            if(self._unready_time[ready_search_point] < now):
                ready_search_point += step
            else:
                ready_search_point -= step

            step = step // 2
    
        # Block while we add
        self.__ready_sites_lock.acquire()

        while(ready_search_point):
            self._ready_sites.push_back(self._unready_sites.front())
            self.unready_sites.pop(0)
            self.unready_time.pop(0)

        self.__ready_sites_lock.release()
        self.__unready_sites_lock.release()
        

    # Used to access the lock and get loaded sites.
    # Can be accessed from python to be used as a lib.
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline vector[cstr]* _cget_ready_sites(self, unsigned int number = 1):
        if(self._unready_time.size()):
            self._check_unready_sites()

        # define to-be-used vars to reduce the time
        # the lock is locked
        cdef vector[cstr] result = vector[cstr](number)
        cdef unsigned int site = 0 

        cdef vector[cstr] u_sites = self._ready_sites

        number = number if number < self._ready_sites.size() else self._ready_sites.size()

        # Acquire the lock to ensure safety
        self.__ready_sites_lock.acquire()

        with nogil:
            while(site != number):
                result[site] = u_sites.front()
                u_sites.pop()
                site += 1

        self.__ready_sites_lock.release()

        return &result

    # Used to access the lock and get loaded sites.
    # Can be accessed from python to be used as a lib.
    @cython.wraparound(False)
    @cython.boundscheck(False)
    cpdef list get_ready_sites(self, unsigned int number = 1):
        if(self._unready_time.size()):
            self._check_unready_sites()

        # define to-be-used vars to reduce the time
        # the lock is locked
        cdef list result = list()
        cdef unsigned int site = 0 

        cdef vector[cstr]* u_sites = &self._ready_sites

        number = number if number < self._ready_sites.size() else self._nready_sites.size()

        # Acquire the lock to ensure safety
        self.__ready_sites_lock.acquire()

        while(site != number):
            result[site] = u_sites[0].front()
            u_sites.pop()
            site += 1

        self.__ready_sites_lock.release()

        return result

    # Add one site to be opened and processed when avaliable
    # Ideally, use extend_sites
    cpdef append_site(self, str site):
        self._unready_sites.push_back(to_cstr(site))

        # Load wait is in seconds, but time in ms
        self._unready_time.push_back(time(NULL) + int(self.load_wait * 1000))

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline int _cappend_site(self, cstr site) nogil:
        self._unready_sites.push_back(site)

        # Load wait is in seconds, but time in ms
        self._unready_time.push_back(time(NULL) + int(self.load_wait * 1000))

    # Add multiple sites to be opened and processed when avaliable
    cpdef extend_sites(self, list sites):
        time_t end_time = time(NULL) + int(self.load_wait * 1000)

        str site
        for site in sites:
            self._unready_sites.push_back(to_cstr(site))
            self._unready_time.push_back(end_time)

    # Add multiple sites to be opened and processed when avaliable
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.nonecheck(False)
    cdef inline int _cextend_sites(self, vector[cstr] sites):
        cdef vector[cstr].iterator iter = sites.begin()

        time_t end_time = time(NULL) + int(self.load_wait * 1000)

        with nogil:
            while(iter != sites.end()):
                self._unready_sites.push_back(dereference(iter))
                self._unready_time.push_back(end_time)
                postincrement(iter)


    ####
    # Utility functions
    ####

    cpdef list[str] extract_hrefs(self):
        return self.driver.execute_script(
                        "var query=document.evaluate('//body[1]//@href[not(self::script)][not(self::link)][not(self::style)]',document,null,XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);"
                        "return Array.from(new Set(Array(query.snapshotLength).fill(0).map((element,index) => query.snapshotItem(index).value)"
                        ".map(x => function(e){if(e[0] == '/'){return location.origin+e;} else if(e.startsWith('http')){return e;}}(x))))"
                        )