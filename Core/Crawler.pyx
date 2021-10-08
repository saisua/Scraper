# local imports
from Browser import Browser


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

from ..utils.utils cimport to_cstring to to_cstr

cdef class Crawler(Browser):

    # Shared attributes
    # (prolly should be wrapped by locks)
    cdef queue[str] links

    # Unique per-machine
    cdef float new_link_wait

    # Strictly unique per-browser


    # Const attributes

    def __init__(self, links:queue[str] = None, new_link_wait:float=1, *args, **kwargs):
        if(links is None):
            self.links = queue[str]()
        else:
            self.links = links

        self.new_link_wait = new_link_wait

        super(*args, **kwargs)

    cpdef Crawler __enter__(self):
        self.open()

        return self

    cpdef __exit__(self, object _, object __, object ___):
        self.close()

    cpdef open(self):
        super().open()

        return self

    cpdef close(self):
        super().close()

    cpdef __call__(self, url:string=None):s
        self.crawl(url)

    cdef crawl(self, url:string=None):
        if(url is not None):
            self.open_tab_load(url)

        vector[cstr] crawl_sites
        
        crawl_sites = self._cget_ready_sites(self.max_tabs)
        while(not crawl_sites.length()):
            crawl_sites = self._cget_ready_sites(self.max_tabs)

        cstr vector[cstr].iterator actual_site
        while(crawl_sites.length() or self._unready_sites.length()):
            actual_site = crawl_sites.begin()

            while(actual_site != crawl_sites.end()):
                self.driver.switch_to_window(actual_site)

                print(self.extract_hrefs())
                
                postincrement(actual_site)



