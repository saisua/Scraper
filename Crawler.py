print("Starting Crawler imports... ")
from io import TextIOWrapper
from os.path import isfile
from typing import Union, Iterable
from datetime import datetime
from time import sleep
from timeit import timeit
from sys import argv
from multiprocessing import Process, Manager

from xml.etree import ElementTree as ET

from Browser import Browser
from Analizers.Text_analizer import analize_text, find, words_related, _color_sent
from Structures.Site import Site, parse_sites_arg
from Structures.Order import OrderedList
from Structures.Search import search
from Structures.Async_generator import AGenerator, do_async
print("Done (Crawler)")

"""
n = function(e){e.innerHTML="{open('jQuery.js','r').read()}";e.onload=function(){jQuery.noConflict();console.log('jQuery injected')};document.head.appendChild(e);}(document.createElement('script'))
var _ = document.evaluate("//*", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
(jQuery(Array.from(new Set(Array(_.snapshotLength).fill(0).map((element, index) => _.snapshotItem(index).nodeName))).filter(function(value,_,_){return value!="IFRAME"}).join(", ")).contents().filter(function() {return jQuery._data(this, 'events') != undefined})).toArray()
"""

def main(proc_num = int(argv[1]) if len(argv) > 1 else 1):
    sites = search(input("Keyword: ") or "cork material", input("Search_in: ") or "general")
    #sites = ["https://twitter.com/search?q=Hidden"]
    
    c1 = Crawler(sites=sites, headless=False, max_tabs=15, load_images=False)

    if(proc_num == 1):
        test(c1)
    else:
        process = []

        for _ in range(proc_num):
            new_proc = Process(target=test, args=(c1,_))
            process.append(new_proc)

        for p in process:
            p.start()

        for p in process: p.join()

    while(input("Search for something? ")):
        ### Search params
        to_search = input("Search: ").lower() or "thing"
        tag = {'1':'n','2':'v','3':'a','4':'r'}.get(input(f"\nWhat '{to_search}'?\n"
                                                "[1]: Noun\n"
                                                "[2]: Verb\n"
                                                "[3]: Adjective\n"
                                                "[4]: Adverb\n\n"
                                                "> ") or '1', None)
        #syn = not 'n' in input("\nFind related words too? ").lower()
        syn = False
        #exact = not 'n' in input("\nFind exact word? ").lower()
        print()

        if(syn): rel_words = words_related(to_search, tag)
        else: rel_words = to_search

        result = []

        while(len(c1.scrapped_text)):
            #found = c1.scrapped_text(all=True)
            found = c1.scrapped_text

            for _,s_dict,sentences in list(filter(None, found)): # filters are tmp fix
                result.extend([sentences[n] for n in find(rel_words,s_dict)])
            break

        print(f"\n\nFound {len(result)} phrases containing words related to {to_search}\n")

        num = 0
        keep = False
        print()

        per_print = 6
        while(not keep and num < len(result)):
            for _ in range(per_print if len(result)-num > (per_print-1) else len(result)-num):
                print(result[num],end="\n\n")
                print("-----")

                num += 1
                
            keep = input("### Stop?")
            print()

def test(c1, proc_num:int=0):
    with c1 as crawler:
        try:
            crawler.crawl(forbidden_domains=["duckduckgo.com",
                                        #"twitter.com", "facebook.com", "www.reddit.com", "reddit.com",
                                        "accounts.google.com", "spreadprivacy.com", "donttrack.us",  "disqus.com", 
                                        "google.com","help.duckduckgo.com","support.google.com","www.google.com",
                                        "www.pinterest.es","www.pinterest.com","pinterest.es","pinterest.com",
                                        "translate.google.com","webcache.googleusercontent.com","about.google"
                                        "policies.google.com"],max_depth=1)
        except KeyboardInterrupt: pass
    print(f"Process-{proc_num} ended")

class Crawler():
    def __init__(self, file:Union[str, ET.ElementTree, TextIOWrapper, None]=None, 
                sites:Iterable[Union[str, Site]]=[], load_wait:float=3, load_timeout:float=20, 
                info_as_node_xml:bool=False, disable_downloads:bool=True,
                max_tabs:int=25, headless:bool=False, load_images:bool=True):
        
        # Check file type and convert it to ET.ElementTree
        # It accepts None, str, file and ET.ElementTree
        
        if(isinstance(file, ET.ElementTree)):
            self.xml_tree = file
        elif(isinstance(file, TextIOWrapper) or (file and isfile(file))):
            self.xml_tree = ET.parse(file)
        else:
            self.xml_tree = ET.ElementTree()

        self.xml_root = ET.Element("root")

        self.max_tabs = max_tabs

        self.browser = Browser(sites, load_timeout, max_tabs, headless, load_images,
                                load_wait, disable_downloads)

        ### Shared memory
        self.scrapped_text = Manager().list()

    def __enter__(self):
        self.browser.open()
        return self

    def __exit__(self,_,__,___):
        self.browser.close()

    def crawl(self, max_depth:int=1, site:str=None,*, initial_depth:int=0, recrawl:bool=False,
                    forbidden_domains=[], lemmatize_words:bool=False):
        if(not site is None):
            if(isinstance(site, Site)): site = site.link
            self.browser._links.append((site,0))
        
        counter = 0

        started_at = datetime.now()
        
        while(not(len(self.browser._links))): sleep(.2)

        print("\nStarting text crawling...\n")
        while(len(self.browser._links)): # or open but not loaded
            print(f"\n\n###\n\nRemaining: {len(self.browser._links)} sites.\n\n###\n")
            
            self.browser.switch_to_window(self.browser.driver.window_handles[0])

            while(len(self.browser._links) and counter < self.max_tabs):
                site = self.browser._get_sites()

                if(site is None):
                    break
                
                self.browser.open_link(site.link, new_tab=True, site=site)
                counter += 1

                print(f"Got {site}\n")

            sites = list(self.browser._get_loaded_sites(wait=True))
            
            print(f"Number of sites waiting to load:")
            while(counter > 0):
                print(counter, end='      \r')
                counter -= 1
                actual_site = sites[0]
                tab = actual_site.tab
                depth = actual_site.depth
                self.browser.switch_to_window(tab)
                
                actual_site.hrefs.update(self.browser.extract_hrefs())
                
                #self.scrapped_text.append(do_async(analize_text, self.browser.extract_text(), exact_words=not lemmatize_words))
                self.scrapped_text.append(analize_text(self.browser.extract_text(), exact_words=not lemmatize_words))

                if(depth < max_depth):
                    depth += 1
                    parent = actual_site.xml_node

                    if(recrawl):
                        self.browser._links.extend([(Site(link,parent=parent,depth=depth),depth) for link in actual_site.hrefs
                                                    if self.browser.domain_from_link(link) not in forbidden_domains])
                    else:
                        self.browser._links.extend([(Site(link,parent=parent,depth=depth),depth) for link in actual_site.hrefs 
                                                    if self.browser._visited_sites_counter.get(link,None) is None and
                                                    self.browser.domain_from_link(link) not in forbidden_domains])
                
                self.browser.close_tab(tab)
                if(len(sites)):
                    sites.pop(0)
                    continue

                browser.restore_timed_out()

                sites = list(self.browser._get_loaded_sites(wait=False))

        print(f"\n\nCrawling (max_depth: {max_depth}) ended after {str(datetime.now()-started_at)}")

        print(f"\nFound and analyzed {len(self.scrapped_text)} websites")

if __name__ == "__main__":
    main()