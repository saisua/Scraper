# distutils: language = c++

# local imports
from Core.Browser cimport Browser


# Internal cimports
cimport cython

from libcpp cimport bool as cbool
from libcpp.string cimport string as cstr
from libcpp.unordered_map cimport unordered_map as cumap # C-unordered map
from libcpp.map cimport map as comap # C-ordered map
from libcpp.vector cimport vector
from libcpp.queue cimport queue
from libcpp.iterator cimport iterator

from cython.operator cimport dereference, postincrement

#from Utils.utils cimport to_cstring as to_cstr


cdef class Crawler(Browser):

    # Shared attributes
    # (prolly should be wrapped by locks)
    cdef list links

    # Unique per-machine
    cdef float new_link_wait

    # Strictly unique per-browser


    # Const attributes

    def __init__(self, links:list[str] = None, new_link_wait:float=1, *args, **kwargs):
        if(links is None):
            self.links = list[str]()
        else:
            self.links = links

        self.new_link_wait = new_link_wait

        super(*args, **kwargs)

    cpdef Crawler __enter__(self):
        self.open()

        return self

    def __call__(self, url:str=None):
        self.crawl(url)

    cdef crawl(self, url:str=None):
        if(url is not None):
            self.open_tab_load(url)

        cdef vector[cstr] * crawl_sites
        
        crawl_sites = self._cget_ready_sites(self.max_tabs)
        while(not crawl_sites.size()):
            crawl_sites = self._cget_ready_sites(self.max_tabs)

        cdef vector[cstr].iterator actual_site
        while(crawl_sites.size() or self._unready_sites.size()):
            actual_site = crawl_sites.begin()

            while(actual_site != crawl_sites.end()):
                self.driver.switch_to_window(dereference(actual_site))

                print(self.extract_hrefs())
                
                postincrement(actual_site)



