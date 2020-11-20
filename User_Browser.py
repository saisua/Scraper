print("Starting User_Browser imports...  ")
from multiprocessing import Process, Manager
from re import search
from collections import defaultdict
from ctypes import c_bool, c_wchar_p # str
from time import sleep
from typing import Tuple
from random import shuffle
import sys
import io
import re
import json
import copy

import requests

from selenium.webdriver.support.events import AbstractEventListener
from selenium.common.exceptions import NoSuchWindowException, JavascriptException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.errorhandler import ErrorCode
from selenium.webdriver.remote import utils
from selenium.webdriver.remote.remote_connection import RemoteConnection
from urllib import parse
from validator_collection.checkers import is_url as validate_url
from argparse import ArgumentParser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from click import echo

from Analizers.Security_analizer import Security_analizer
from Browser import Browser
from Settings.Identity import Identity
from Structures.Site import Site
from Structures.Async_generator import AGenerator
from Structures.Interceptor import Interceptor
from Structures.Search import search 

import logging

print("Done (User_Browser)")

# https://www.cssscript.com/demo/device-browser-fingerprint-generator-imprint-js/#
# https://panopticlick.eff.org
# https://amiunique.org/
# http://www.popuptest.com/

# AudioContext fingerprint
# Hash of WebGL fingerprint
# Hash of canvas fingerprint



def main():

    args = __create_parser()

    if(args.ii):
        args.verbose = False
        args.headless = False
        args.interceptor = True
        args.interceptor_identity = True
        args.interceptor_disabled = False
        # To be enabled once the extension is loaded at start
        args.secondary_browser = True
        args.disable_extensions = False


    browser = Controlled_Browser(
            verbose=args.verbose,
            headless=args.headless,
            autoload_videos=args.autoload_videos,
            enable_secondary_browser=args.secondary_browser,
            http=args.http,
            ssl=args.ssl,
            ftp=args.ftp,
            socks=args.socks,
            auto_proxies=args.auto_proxies,
            auto_proxy_type=args.auto_proxy_type

            ,test=False
    )

    browser.open(
            enable_interceptor=args.interceptor, 
            interceptor_kwargs={
                "process_non_realtime":args.interceptor_passive,
                "non_realtime_interface":args.interceptor_interface,
                "verbose":args.verbose
                },
            interceptor_object=(Identitier(
                process_non_realtime=args.interceptor_passive,
                non_realtime_interface=args.interceptor_interface
                ) if args.interceptor_identity else None),
            enable_extensions=not args.disable_extensions,
            disable_javascript=args.disable_javascript
    )
    
    if(browser.interceptor):
        browser.interceptor.active.value = not args.interceptor_disabled
        print(f"[?] Browser interceptor starts {'disabled' if args.interceptor_disabled else 'enabled'}")

    browser.driver.switch_to.window(browser.driver.window_handles[0])

    lasting_link = ""
    for link in args.URLs:
        if(lasting_link):
            if(link.endswith(']')):
                link = f"{lasting_link} {link[:-1]}"
                lasting_link = ""
            else:
                lasting_link = f"{lasting_link} {link}"
                continue
        elif(link.startswith('[') and not link.endswith(']')):
            lasting_link = f"{lasting_link} {link[1:]}"
            continue

        if(validate_url(link)):
            browser.open_link(link, new_tab=True, wait_load=False)
        else:
            if(validate_url(full_link := f"https://{link}")):
                try:
                    tab = browser.open_link(full_link, new_tab=True, wait_load=False)
                    continue

                except WebDriverException:
                    browser.close_check()

            print(f"[-] {link} is not recognized as a proper url. Searching for it instead.")
            browser.open_link(f"https://duckduckgo.com/?q={link}", new_tab=True, wait_load=False)

    """
    for tab in browser.driver.window_handles:
        browser.driver.switch_to.window(tab)

        site = self._site_from_tab[tab]

        self._site_from_tab[tab] = """


    if(False):
        ### TESTS
        print("Starting the tests...")

        if(args.secondary_browser):
            #print(browser.website_security("https://peliculasonline.cloud/download.php"))
            print(browser.website_security._get_analyze("http://google.es"))
            #print(browser.website_security("https://www.cssscript.com/demo/notification-popup-notiflix"))

        print("Tests DONE")
        ### TESTS END

    browser._site_from_tab.clear()

    try:
        while(browser.is_open):
            try:
                browser._serve_all()
            except Exception as err:
                print(err)
    except Exception:
        pass
    finally:            
        browser.close()

def __create_parser():
    ### Any functionality will be added as needed

    description = """
        Create new instances of Firefox, with custom controllers and security measures.
        """

    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Launch this browser with no Graphical User Interface")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show data captured by the browser")
    parser.add_argument(
        "--autoload_videos",
        action="store_true",
        help="Auto-load the videos as soon as websites are loaded")
    parser.add_argument(
        "--interceptor", "-i",
        action="store_true",
        help="Start the interceptor tool, a proxy to capture browser's traffic")
    parser.add_argument(
        "--interceptor_disabled",
        action="store_true",
        help="If the interceptor should be disabled at start (can be enabled/disabled later too)")
    parser.add_argument(
        "--interceptor_passive",
        action="store_true",
        help="Wether to launch a pyshark (wireshark) instance")
    parser.add_argument(
        "--interceptor_interface",
        action="store",
        type=str,
        default="any",
        help="Interface where to capture browser's traffic")
    parser.add_argument(
        "--interceptor_identity",
        action="store_true",
        help="Dinamically change js-accessible tracking data")
    parser.add_argument(
        "-2",
        "--secondary_browser",
        action="store_true",
        help="Enable a secondary browser for extended capabilities")
    parser.add_argument(
        "--disable_extensions",
        action="store_true",
        help="Disable extensions for extended user interaction")
    parser.add_argument(
        "--disable_javascript",
        action="store_true",
        help="Disable javascript to evade running web scripts")
    parser.add_argument(
        "-ii",
        action="store_true",
        help="Enable the interceptor and the identity cloaking")
    parser.add_argument(
        "--http",
        type=str,
        help="List of http proxies to change while browsing (comma separated)")
    parser.add_argument(
        "--ssl",
        type=str,
        help="List of ssl proxies to change while browsing (comma separated)")
    parser.add_argument(
        "--ftp",
        type=str,
        help="List of ftp proxies to change while browsing (comma separated)")
    parser.add_argument(
        "--socks",
        type=str,
        help="List of socks5 proxies to change while browsing (comma separated)")
    parser.add_argument(
        "--auto_proxies",
        action="store_true",
        help="Use automatic rotating proxies. WARN: Using this with personal/private data is DANGEROUS")
    parser.add_argument(
        "--auto_proxy_type",
        type=str,
        help="Type of proxies to scrape (socks/http/ssl) [default auto : socks]"
    )
    parser.add_argument(
        dest="URLs",
        nargs='*',
        type=str,
        help="Websites to open after loading"
    )
    

    return parser.parse_args()


class Controlled_Browser(Browser, AbstractEventListener):
    secondary_browser:Browser = None
    website_security:Security_analizer
    used_browser:Browser

    receiver:"Receiver"
    _receiver_process:Process

    receiver_address:Tuple[str, int]

    receiver_address_str:str
    active:bool

    _cmd_url:str

    ## private attr to exchange info between init and open
    __auto_proxies:bool

    verbose:bool=False
    keep_record:bool=False
    change_proxies:bool=False


    stdout=sys.stdout

    console_msg:str
    _run_after_msg:str=""

    def __init__(self, *args, **kwargs):
        if(not "manager" in kwargs):
            kwargs["manager"] = Manager()

        self.__is_open = False
        self.active = kwargs["manager"].Value(c_bool, True)
        self.console_msg = kwargs["manager"].Value(c_wchar_p, "")
        
        if(kwargs.pop("verbose", False)):
            self.verbose = True
            print("[?] Browser started with verbosity:\n"
                    "\t[+] Good: The program keeps its flow as expected.\n"
                    "\t[-] Bad: Something bad happened, but the program detected it. May be fixed later.\n"
                    "\t[?] Info: The program shows info that can be valuable to keep track of the progress.\n"
                    "\t[#] Fix: The program detected a strange behaviour, but fixed it.\n")
        #self.keep_record = kwargs.pop("keep_record", False)

        self.__auto_proxies = kwargs.pop("auto_proxy_type") or kwargs.pop("auto_proxies")

        self.proxys = {
            "socksProxy":list(filter(None, (kwargs.pop("socks") or '').split(','))),
            "httpProxy":list(filter(None, (kwargs.pop("http") or '').split(','))),
            "ftpProxy":list(filter(None, (kwargs.pop("ftp") or '').split(','))),
            "sslProxy":list(filter(None, (kwargs.pop("ssl") or '').split(',')))
        }

        if(self.__auto_proxies or any(self.proxys.values())): self.change_proxies = True

        for proxy_list in self.proxys.values():
            shuffle(proxy_list)


        if(kwargs.pop("enable_secondary_browser", False)):
            #print("\n[!] FOR SOME REASON, THE SCRAPER EXTENSION DOES NOT AUTOMATICALLY INSTALL."
            #        " PLEASE, INSTALL IT MANUALLY IN about:addons\n")
            self.secondary_browser = Browser(*args, **{**kwargs, "headless":not kwargs.pop("test",False)})

            self.secondary_browser.proxys = copy.deepcopy(self.proxys)

            for proxy_list in self.secondary_browser.proxys.values():
                shuffle(proxy_list)
        else:
            self.secondary_browser = None
            kwargs.pop("test")
        
        if(kwargs.get("enable_extensions", True)):
            self.receiver = HTTPServer(kwargs.pop("receiver_address", ('127.0.0.1',0)),
                                        self.Receiver)
            self.receiver.timeout = 0.15
            # Surpress error handling
            self.receiver.handle_timeout = lambda : None
            # Add reference for handler object to access
            self.receiver.user_browser = self

            self.receiver_address = self.receiver.server_address
            self.receiver_address_str = f"{self.receiver_address[0]}:{self.receiver_address[1]}"

            self.website_security = Security_analizer(self.secondary_browser)
            print(f"[?] Created scraper extension command receiver in {self.receiver_address_str}")

        self.disable_event_listener = kwargs.pop("disable_event_listener", False)
        

        Browser.__init__(self, *args, **kwargs)

    def __enter__(self):
        self.open()

        return self

    def __exit__(self, _, __, ___):
        return self.close()

    def open(self, **kwargs):
        self.__is_open = True

        if(self.disable_event_listener or kwargs.pop("disable_event_listener", False)):
            event_listener_obj = None
        else:
            event_listener_obj = self

        if(self.__auto_proxies and kwargs.get("interceptor_object")):
            print("[-] Both socks proxy and interceptor are enabled. This is not possible yet, disabled interceptor.")
            del kwargs['interceptor_object']

        Browser.open(self, **{**kwargs, "event_listener_obj":event_listener_obj
                            ,"block_cookies":True, 
                            "interceptor_object":kwargs.get("interceptor_object"),
                            "enable_proxies":self.__auto_proxies
                            })

        if(not self.secondary_browser is None):
            ### THIS IS A TEMPORARY UGLY SOLUTION, I hope I can remove this in the future
            self.driver.install_addon('//'.join(__file__.split('/')[:-1])+"//Extensions//scraper-extension//scraper-extension.xpi")
            self.__private_extension("Scraper")

            self.secondary_browser.open(**{**kwargs, "event_listener_obj":self
                            ,"block_cookies":False,
                            "disable_javascript":False,
                            "enable_extensions":False,
                            "enable_proxies":self.__auto_proxies
                            })

            self.secondary_browser.driver.switch_to.window(self.secondary_browser.driver.window_handles[0])

        self.used_browser = self.secondary_browser or self

        self._cmd_url = self.driver.command_executor._url
        #print(f"Browser is in {self._cmd_url}/session/{self.driver.session_id}")

        if(proxy_type := self.__auto_proxies or kwargs.pop("auto_proxies", False) and kwargs.pop("auto_proxy_type", False)):
            # Can be added options for country or anonimity

            if(proxy_type not in {'socks', 'ssl', 'http'}): 
                print("[?] Auto proxy type was not set. Setting it to 'socks' by default")
                proxy_type = 'socks'

            self.proxys = Identity._get_proxies(self.used_browser, **{proxy_type:True})
            
            for proxy_list in self.proxys.values():
                shuffle(proxy_list)
        
            self.new_proxy()


            if(self.secondary_browser):
                self.secondary_browser.proxys = copy.deepcopy(self.proxys)
            
            for proxy_list in self.used_browser.proxys.values():
                shuffle(proxy_list)

            print("[+] Auto proxies set and ready")

    def close(self):
        print(f"Shutting down the browser...")
        self.__is_open = False

        Browser.close(self)

        if(not self.secondary_browser is None):
            self.secondary_browser.close()

    def _serve_all(self):
        sleep_time = 0

        bef_tab = self.driver.current_window_handle
        self.last_tab = bef_tab
        
        self.num_tabs = len(self.driver.window_handles)

        for tab in self.driver.window_handles:
            self.driver.switch_to.window(tab)

            self._site_from_tab[tab] = Site(self.driver.current_url, tab=tab)

        print("\n[+] User_browser is operative and running\n")

        while(self.__is_open):
            if(self.receiver): self.receiver.handle_request()
            try:
                # Control and update browser's state
                
                    #print("0",end='\r')
                if(len(self.driver.window_handles) < self.num_tabs):
                    self.num_tabs = len(self.driver.window_handles)

                    closed_tab = Controlled_Browser.find_unique(list(self._site_from_tab.keys()),
                                                    self.driver.window_handles)


                    self._site_from_tab.pop(closed_tab)
                    #del closed_tab

                    self.driver.switch_to.window(self.last_tab)
                    self.after_close_tab(closed_tab)
                    bef_tab = self.last_tab
                    
                    self.after_switch_to_tab(bef_tab)
                elif(len(self.driver.window_handles) > self.num_tabs or
                            self.driver.execute_script("return document.visibilityState != 'visible'")):
                    self.num_tabs = len(self.driver.window_handles)
                    
                    #print(f"{self.driver.window_handles=}\n{list(self._site_from_tab.keys())=}")
                    #print(Controlled_Browser.find_unique(self.driver.window_handles, 
                    #                                        list(self._site_from_tab.keys()))
                    #)       

                    if(undetected_tab := Controlled_Browser.find_unique(self.driver.window_handles, 
                                                            list(self._site_from_tab.keys()))):
                        sleep_time = 0
                        iterations = 0
                        num_tabs = len(self.driver.window_handles)
                        while(True):
                            sleep(sleep_time)
                            self.driver.switch_to.window(
                                    undetected_tab
                            )

                            # Unknown website, to be fixed later
                            self._site_from_tab[undetected_tab] = None
                        
                            self.after_open_new_tab(undetected_tab)

                            self.last_tab, bef_tab = bef_tab, undetected_tab
                        
                            if(not (undetected_tab := Controlled_Browser.find_unique(self.driver.window_handles, 
                                                                list(self._site_from_tab.keys())))
                                        or iterations >= num_tabs):
                                break
                            sleep_time = max(10, sleep_time * 2 + (1/num_tabs))
                            iterations += 1

                    else:
                        hidden_sites = 0

                        sleep(sleep_time)
                        for wrong_tab in self.driver.window_handles:
                            self.driver.switch_to.window(wrong_tab)

                            if(self.driver.execute_script("return document.onvisibilitychange == null;")):
                                self.add_onvisibilitychange()
                         
                                if(self.verbose): print(f"[#] Synchronized tab {wrong_tab}")
                            elif(self.driver.execute_script("return document.onvisibilitychange == 'hidden';")):
                                hidden_sites += 1                        
                        
                        if(hidden_sites == len(self.driver.window_handles)):
                            sleep_time = max(10, sleep_time * 2 + 0.5)
                        else:
                            sleep_time = 0

                elif(bef_tab != self.driver.current_window_handle):
                    self.last_tab, bef_tab = bef_tab, self.driver.current_window_handle
                    self.after_switch_to_tab(bef_tab)

                tab = self._site_from_tab.get(self.driver.current_window_handle)

                #print(f"tab: {tab.link} {self.driver.current_url}                    ", end='\r')


                # If opened new unknown tab
                # If new tab
                if(tab is None):
                    #self.after_navigated_to(self.driver.current_url, self.driver)
                    self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url)                    

                # If same tab, new site
                elif(self.driver.execute_script("return document.onvisibilitychange == null;")):
                    self.after_navigated_to(self.driver.current_url, self.driver)

                    if(self.keep_record):
                        self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url, 
                                                    parent=tab)
                    else:
                        self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url)
                        del tab
                                        
                    self.add_onvisibilitychange()

                # Same tab, same site, new directory
                elif(tab.link != self.driver.current_url and 
                        self._site_from_tab.get(self.driver.current_window_handle, 
                                                self.Ensure_obj()).link == tab.link):
                    if(self.keep_record):
                        self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url, 
                                                    parent=tab)
                    else:
                        self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url)
                        del tab

                    self.after_navigated_to(self.driver.current_url, self.driver)


                ## Print messages in browser javascript console (temporal)
                if(self.console_msg.value):
                    run_after_eval = self.driver.execute_script("return window.scraper_run_after_msg;")
                    if(run_after_eval):
                        self._run_after_msg.value = run_after_eval

                    self.driver.execute_script(f"window.scraper_last_msg = \"{self.console_msg.value}\";"
                                                "console.info(window.scraper_last_msg);"
                                                f"eval(\"{self._run_after_msg.value}\");")
                                                # window.scraper_run_after_msg = "for(var a of window.scraper_last_msg.split(', ').filter(e=>e.endsWith('.pdf'))){window.open(a);}"
                    self.console_msg.value = ""
                    echo(f"[?] Printed info in tab {self.driver.current_window_handle}", file=self.stdout)

            except NoSuchWindowException:
                continue

    def add_onvisibilitychange(self):
        self.driver.execute_script("""
                document.onvisibilitychange = function() { 
                    if(document.visibilityState == 'visible'){
                        var xhr = new window.XMLHttpRequest();"""

                        f"xhr.open('post',  '{self._cmd_url}/session/{self.driver.session_id}/window', true);"

                        "var data = JSON.stringify({"
                            f"'handle': '{self.driver.current_window_handle}'"
                        """ 
                        });
                        xhr.send(data);
                        
                    }
                };
                var interval__ = setInterval(function(){if(document.body && document.body.children.length > 0){
                    var scrapernode = document.createElement('scraperip');
                    scrapernode.hidden = true;"""
                    f"scrapernode.innerText = '{self.receiver_address_str}';"
                    """document.body.appendChild(scrapernode);
                    console.log(scrapernode);
                    clearInterval(interval__);
                } }, 300);"""
            ) ### window.scraper_extension_ip should be encrypted

    ### EVENTS

    def after_open_new_tab(self, tab):
        if(self.verbose): print("Opened new tab " + tab)

    def after_switch_to_tab(self, tab):
        if(self.verbose): 
            url_print = self._site_from_tab.get(tab)
            print("Switched to tab ", url_print.link if url_print else tab)

        if(self.change_proxies):
            self.new_proxy()
            print("[+] Swapped proxies")

    def before_navigate_to(self, url, driver):
        if(self.verbose): print("(Driver) before_navigate_to ", url) 

    def after_navigate_to(self, url, driver):
        if(self.verbose): print("(Driver) after_navigate_to ", url)

    def after_navigated_to(self, url, driver):
        if(self.verbose): 
            print("Got ", url)

        self.driver.delete_all_cookies()
        #self.driver.execute(Command.CLEAR_APP_CACHE)
        #self.driver.execute(Command.CLEAR_LOCAL_STORAGE)
        #self.driver.execute(Command.CLEAR_SESSION_STORAGE)

        if(not self.interceptor is None):
            self.interceptor.new_identity()
            print("[+] Generated new interceptor identity")


    def after_close_tab(self, tab):
        if(self.verbose): 
            print(f"Closed tab  {tab} ({self._site_from_tab[tab].link})")

    def before_navigate_back(self, driver):
        if(self.verbose): print("(Driver) before_navigate_back ", driver.current_url)

    def after_navigate_back(self, driver):
        if(self.verbose): print("(Driver) after_navigating_back ", driver.current_url)

    def before_navigate_forward(self, driver):
        if(self.verbose): print("(Driver) before_navigating_forward ", driver.current_url)

    def after_navigate_forward(self, driver):
        if(self.verbose): print("(Driver) after_navigating_forward ", driver.current_url)

    def before_find(self, by, value, driver):
        if(self.verbose): print("(Driver) before_find")

    def after_find(self, by, value, driver):
        if(self.verbose): print("(Driver) after_find")

    def before_click(self, element, driver):
        if(self.verbose): print("(Driver) before_click")

    def after_click(self, element, driver):
        if(self.verbose): print("(Driver) after_click")

    def before_change_value_of(self, element, driver):
        if(self.verbose): print("(Driver) before_change_value_of")

    def after_change_value_of(self, element, driver):
        if(self.verbose): print("(Driver) after_change_value_of")

    def before_execute_script(self, script, driver):
        pass #print("(Driver) before_execute_script")

    def after_execute_script(self, script, driver):
        pass #print("(Driver) after_execute_script")

    def before_close(self, driver):
        if(self.verbose): print("(Driver) before_close")

    def after_close(self, driver):
        if(self.verbose): print("(Driver) after_close")

    def before_quit(self, driver):
        if(self.verbose): print("(Driver) before_quit")

    def after_quit(self, driver):
        if(self.verbose): print("(Driver) after_quit")


    def on_exception(self, exception, driver):
        if(isinstance(exception, WebDriverException) or 
                    isinstance(exception, NoSuchWindowException)):
            try:
                driver.window_handles
            except:
                print("\nThe browser has been closed by the user")
                exit(0)

        elif(not isinstance(exception, JavascriptException)):
            print("(Driver) on_exception")
            print(exception)

    # Properties

    @property
    def is_open(self):
        return self.__is_open

    ### Static methods
    @staticmethod
    def find_unique(list1:list, list2:list) -> object:
        for el in set(list1+list2):
            if(not el in list2):
                return el

    def _addon_lookup_function(self, args):
        echo(f"lookup: {args.get('data')}", file=Controlled_Browser.stdout)

        if(link := args.pop('data')):
            tab = self.secondary_browser.open_link(link)
            hrefs = self.secondary_browser.extract_hrefs()

            echo('\n'.join(hrefs), file=Controlled_Browser.stdout)

            self.secondary_browser.close_tab(tab)
            self.secondary_browser.driver.switch_to.window(self.secondary_browser.driver.window_handles[0])
        else:
            hrefs = self.extract_hrefs()

            echo('\n'.join(hrefs), file=Controlled_Browser.stdout)

        
        self.console_msg.value = f"{self.console_msg.value} {', '.join(hrefs)}"
        echo(file=Controlled_Browser.stdout)


    def _addon_search_function(self, args):
        echo(f"search: {args.get('data')}", file=Controlled_Browser.stdout)

        for link in search(args.get('data')):
            self.open_link(link, new_tab=True)

    def _addon_security_function(self, args):
        echo(f"security: {args.get('data')}", file=Controlled_Browser.stdout)

        data = self.website_security(args.get('data'))
        echo(data, file=Controlled_Browser.stdout)
        self.console_msg.value = f"{self.console_msg.value} {data}"

        self.website_security.browser.new_proxy()

    def _addon_set_after_run_function(self, args):
        echo(f"Set after run: {args.get('data')}", file=Controlled_Browser.stdout)

        self._run_after_msg.value = args.get('data')
        self.console_msg.value = self.console_msg.value + " set after run set successfully!"

    class Ensure_obj:
        def __getattribute__(self, name) -> None:
            return None

    class Receiver(SimpleHTTPRequestHandler):
        __cmd_codes = eval(re.search(r"var\s+?COMMUNICATION_CODES\s*?=\s*?(\{(.|\n)*?\})",
                open(f"{'//'.join(__file__.split('/')[:-1])}//Extensions//Scraper-src//scripts//scraper.js",'r').read())
                    .groups()[0])
        __cmd_functions = {
            __cmd_codes["crawl"]:lambda self,args: echo(f"crawl order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["lookup"]:lambda self,args: self.server.user_browser._addon_lookup_function(args),
            __cmd_codes["text"]:lambda self,args: echo(f"text order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["text sel"]:lambda self,args: echo(f"text order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["image"]:lambda self,args: echo(f"image order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["security"]:lambda self, args: self.server.user_browser._addon_security_function(args),
            __cmd_codes["search"]:lambda self, args: self.server.user_browser._addon_search_function(args),
            __cmd_codes["set afrun"]:lambda self, args: self.server.user_browser._addon_set_after_run_function(args)
        }

        stdout=sys.stdout

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))

            if(cmd := self.__cmd_functions.get(data.get("command"))):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                cmd(self, data)
            else:
                self.send_error(400, "Wrong message")


    ## TMP
    def __private_extension(self, extension_name:str) -> None:
        print("Enabling the extension... ", end='')
        self.open_link("about:addons", new_tab=True)
        self.driver.execute_script("async function a(){"
                    "document.querySelector('browser').contentDocument.body.querySelectorAll('categories-box button')[1].click();"
                    "return new Promise(resolve => setTimeout(resolve, 100));"
                "}"
                "a().then(()=>{"
                    "document.querySelector('browser').contentDocument.body.querySelector(\"addon-card[aria-labelledby='"+extension_name.lower()+"-heading']\").click();"
                    "return new Promise(resolve => setTimeout(resolve, 100));"
                "}).then(()=>{"
					"document.querySelector('browser').contentDocument.body.querySelector(\"label input[type='radio'][name='private-browsing'][value='1']\").click();"
                    "return new Promise(resolve => setTimeout(resolve, 100));"
                "}).then(()=>(window.close()));")

        self.driver.switch_to.window(self.driver.window_handles[0])  
        print("DONE")

class Identitier(Interceptor):
    def __init__(self, *args, **kwargs):
        print("[+] Interceptor set as Identity cloak")
        super().__init__(*args, **kwargs)

    response_regex = re.compile(b"(<head|<body)")

    def response(self, flow):
        """
            The full HTTP response has been read.
        """
        
        #echo("response", file=self.stdout)
        #echo(f"response {flow.response.headers.get('content-type','')}", file=self.stdout)
        #echo(f"response {flow.server_conn.address} -> {flow.client_conn.address}", file=self.stdout)

        #flow.intercept()

        if(self.active.value):
            if('text/html' in flow.response.headers.get("content-type")):

                b = self.response_regex.search(flow.response.content)
                if(b):
                    index = flow.response.content.find(b"<", b.start()+5)

                    #echo(index, file=self.stdout)
                    
                    flow.response.content = (flow.response.content[:index] +
                                            self.identity_script +
                                            flow.response.content[index:])

                    #echo(flow.response.content, file=self.stdout)

                    
                    

        #flow.resume()


if __name__ == "__main__":
    main()