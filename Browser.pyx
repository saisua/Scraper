# Internal imports
from multiprocessing import Manager
from multiprocessing.queues import Queue
from random import shuffle, randint

# External imports
from selenium import webdriver

# Internal cimports
from libcpp cimport bool as cbool
from libcpp.string cimport string as cstr
from libcpp.unordered_map cimport unordered_map as cumap # C-unordered map
from libcpp.map cimport map as comap # C-ordered map
from libcpp.vector cimport vector
from libcpp.queue cimport queue

from cpython.ref cimport PyObject
from cython.operator cimport dereference, postincrement

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

    cdef object _ready_sites # multiprocessing.Queue
    cdef vector[cstr] _timed_out_links

    cdef dict _flush_sites_counter

    cdef cumap[cstr, queue[cstr]] proxys

    # Strictly unique per-browser
    cdef object driver # webdriver.Firefox
    cdef object interceptor # Interceptor

    cdef cmap[int, object] _site_from_tab # [ int, Site ]

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

        # Check sites to be an OrderedList of {Site:depth}
        # Workaround. Improvement needed
        # self._links = parse_sites_arg(sites, _manager=self._manager)

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

    cpdef open(self, object options=None, object profile=None, object capabilities=None, cbool overwrite_config=True,
                    proxy_cmap proxys=None, cbool headless=False):
        print(f"\n[?] Starting the opening of a Browser{' (headless)' if headless else ''}")

        if(not proxys is None): self.proxys = dereference(proxys._cmap)

        """"
        if(enable_interceptor):
            if(self.interceptor is None):
                self.interceptor = interceptor_object or Interceptor(self._manager, **interceptor_kwargs)

            # Overwrite socksProxy. Once mitmproxy has support for
            # Socks5 & Upstream, redirect the mitmproxy
            self.proxys["socksProxy"] = [self.interceptor.address]

        if(options is None or profile is None or capabilities is None or not overwrite_config):
            options2, profile2, capabilities2 = get_configuration(tabs_per_window=1000,
                                            headless=self.headless,
                                            load_images=self.load_images,
                                            autoload_videos=self.autoload_videos,
                                            disable_downloads=self.disable_downloads,
                                            enable_drm=enable_drm, block_cookies=block_cookies,
                                            enable_extensions=enable_extensions, enable_proxies=enable_proxies,
                                            download_no_prompt=download_no_prompt,
                                            proxys=self.get_proxy(http=True, ssl=True, ftp=True, socks=True),
                                            options=options if not overwrite_config else None, 
                                            profile=profile if not overwrite_config else None, 
                                            capabilities=capabilities if not overwrite_config else None,
                                            disable_javascript=disable_javascript)

            if(not overwrite_config or options is None):
                options = options2
            if(not overwrite_config or profile is None):
                profile = profile2
            if(not overwrite_config or capabilities is None):
                capabilities = capabilities2

            del options2, profile2, capabilities2
        """

        print("Configuration complete. Trying to run the drivers. This could take some time...")
        try:
            self.driver = webdriver.Firefox(
                    executable_path=f"{'//'.join(__file__.split('/')[:-1])}//geckodriver",
                    options=options, firefox_profile=profile, capabilities=capabilities) 

            #self._profile = profile
                    
            print("[+] Drivers ran succesfully!")

        except Exception as ex:
            print(f"Looks like something failed. Error message: {ex}")
            self.driver = webdriver.Firefox()

        """
        if(not event_listener_obj is None):
            self.driver = EventFiringWebDriver(self.driver, event_listener_obj)

            if(True):
                pass
                #self.driver.install_addon('//'.join(__file__.split('/')[:-1])+"//Extensions//duckduckgo-privacy-extension//extension.xpi",
                #                    temporary=False)
                #self.driver.install_addon('//'.join(__file__.split('/')[:-1])+"//Extensions//scraper-extension//scraper-extension.xpi",
                #                    temporary=False)
        """
                
        
        ### Non-shared memory
        #self._site_from_tab = {}


        #self.open_link("about:config")
        self.driver.get("about:config")
        self.driver.execute_script("document.querySelector('button').click();")

        #breakpoint()

        ### After driver configs
        #self.driver.set_page_load_timeout(0)
        self.driver.set_page_load_timeout(self.load_timeout)


        print("[?] New Browser opened")
        #print(self.driver.window_handles)

    cpdef close(self):
        self.driver.quit()

        if(not self.interceptor is None):
            self.interceptor.close()