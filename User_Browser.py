print("Starting User_Browser imports...  ")
from multiprocessing import Process, Manager
from re import search
from collections import defaultdict
from ctypes import c_bool
from time import sleep
from typing import Tuple
import sys
import io
import re
import json

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

from Browser import Browser
from Structures.Site import Site
from Structures.Async_generator import AGenerator
from Structures.Interceptor import Interceptor
from Structures.Search import search 
from Analizers.Security_analizer import Security_analizer

print("Done (User_Browser)")

# https://www.cssscript.com/demo/device-browser-fingerprint-generator-imprint-js/#
# https://panopticlick.eff.org
# https://amiunique.org/

# AudioContext fingerprint
# Hash of WebGL fingerprint
# Hash of canvas fingerprint

from click import echo


def main():
    args = __create_parser()

    if(args.ii):
        args.verbose = False
        args.headless = False
        args.interceptor = True
        args.interceptor_identity = True
        args.interceptor_disabled = False
        # To be enabled once the extension is loaded at start
        args.secondary_browser = False

    browser = Controlled_Browser(
            verbose=args.verbose,
            headless=args.headless,
            autoload_videos=args.autoload_videos,
            enable_secondary_browser=args.secondary_browser
    )

    browser.open(
            enable_interceptor=args.interceptor, 
            interceptor_kwargs={
                "process_non_realtime":args.interceptor_passive,
                "non_realtime_interface":args.interceptor_interface
                },
            interceptor_object=(Identitier(
                process_non_realtime=args.interceptor_passive,
                non_realtime_interface=args.interceptor_interface
                ) if args.interceptor_identity else None),
            enable_extensions=True,
            disable_javascript=False
    )
    
    if(browser.interceptor):
        browser.interceptor.active.value = not args.interceptor_disabled
        print(f"[?] Browser interceptor starts {'disabled' if args.interceptor_disabled else 'enabled'}")

    browser.driver.switch_to.window("11")
    for link in args.URLs:
        if(validate_url(link)):
            browser.open_link(link, new_tab=True)
        else:
            print(f"[-] {link} is not recognized as a proper url. Searching for it instead.")
            browser.open_link(f"https://duckduckgo.com/?q={link}", new_tab=True)


    if(False):
        ### TESTS
        print("Starting the tests...")
        browser.open_link("about:blank", new_tab=True)
        
        print(browser.website_security("https://peliculasonline.cloud/download.php"))
        print(browser.website_security("https://google.es"))
        
        print("Tests DONE")
        ### TESTS END

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
        "-ii",
        action="store_true",
        help="Enable the interceptor and the identity cloaking")
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

    receiver:"Receiver"
    _receiver_process:Process

    receiver_address:Tuple[str, int]
    receiver_address_str:str

    active:bool

    _cmd_url:str

    verbose:bool=False
    keep_record:bool=False


    stdout=sys.stdout


    def __init__(self, *args, **kwargs):
        if(not "manager" in kwargs):
            kwargs["manager"] = Manager()

        self.__is_open = False
        self.active = kwargs["manager"].Value(c_bool, True)

        self.verbose = kwargs.pop("verbose", False)
        #self.keep_record = kwargs.pop("keep_record", False)

        if(kwargs.pop("enable_secondary_browser", False)):
            print("\n[!] FOR SOME REASON, THE SCRAPER EXTENSION DOES NOT AUTOMATICALLY INSTALL."
                    " PLEASE, INSTALL IT MANUALLY IN about:addons\n")
            self.secondary_browser = Browser(*args, **{**kwargs, "headless":True})
        else:
            self.secondary_browser = None
        
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

        Browser.open(self, **{**kwargs, "event_listener_obj":event_listener_obj
                            ,"block_cookies":True, 
                            "interceptor_object":kwargs.get("interceptor_object"),
                            })

        if(not self.secondary_browser is None):
            self.secondary_browser.open(**{**kwargs, "event_listener_obj":self
                            ,"block_cookies":False,
                            "disable_javascript":False,
                            "enable_extensions":False
                            })

        self._cmd_url = self.driver.command_executor._url
        #print(f"Browser is in {self._cmd_url}/session/{self.driver.session_id}")

    def close(self):
        print(f"Shutting down the browser...")
        self.__is_open = False

        Browser.close(self)

        if(not self.secondary_browser is None):
            self.secondary_browser.close()

    def _serve_all(self):
        self.num_tabs = len(self.driver.window_handles)
        bef_tab = self.driver.current_window_handle
        self.last_tab = bef_tab
        
        while(self.__is_open):
            if(self.receiver): self.receiver.handle_request()
            try:
                # Control and update browser's state
                
                    #print("0",end='\r')
                if(len(self.driver.window_handles) < self.num_tabs):
                    self.num_tabs = len(self.driver.window_handles)

                    closed_tab = Controlled_Browser.find_unique(list(self._site_from_tab.keys()),
                                                    self.driver.window_handles)

                    self.after_close_tab(closed_tab)

                    self._site_from_tab.pop(closed_tab)
                    del closed_tab

                    self.driver.switch_to.window(self.last_tab)
                    bef_tab = self.last_tab
                    
                    self.after_switch_to_tab(bef_tab)
                elif(len(self.driver.window_handles) > self.num_tabs or
                            self.driver.execute_script("return document.visibilityState != 'visible'")):
                    self.num_tabs = len(self.driver.window_handles)
                    if(self.verbose): print(self.driver.window_handles)
                    self.driver.switch_to.window(
                            Controlled_Browser.find_unique(self.driver.window_handles, 
                                                            list(self._site_from_tab.keys()))
                            or bef_tab
                    )

                    if(self.driver.current_window_handle != bef_tab):
                        self.after_open_new_tab(self.driver.current_window_handle)

                        self.last_tab, bef_tab = bef_tab, self.driver.current_window_handle
                    
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

            except NoSuchWindowException:
                print("NoSuchWindowException")
                continue

    ### EVENTS

    def after_open_new_tab(self, tab):
        if(self.verbose): print("Opened new tab " + tab)

    def after_switch_to_tab(self, tab):
        if(self.verbose): 
            url_print = self._site_from_tab.get(tab)
            print("Switched to tab ", url_print.link if url_print else tab)

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
            print("Generated new interceptor identity")

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

        for link in search(args.get('data')):
            self.open_link(link, new_tab=True)

    def _addon_security_function(self, args):
        echo(f"security: {args.get('data')}", file=Controlled_Browser.stdout)

        echo(self.website_security(args.get('data')), file=Controlled_Browser.stdout)

    class Ensure_obj:
        def __getattribute__(self, name) -> None:
            return None

    class Receiver(SimpleHTTPRequestHandler):
        __cmd_codes = eval(re.search(r"var\s+?COMMUNICATION_CODES\s*?=\s*?(\{(.|\n)*?\})",
                open(f"{'//'.join(__file__.split('/')[:-1])}//Extensions//Scraper-src//scripts//scraper.js",'r').read())
                    .groups()[0])
        __cmd_functions = {
            __cmd_codes["crawl"]:lambda self,args: echo(f"crawl order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["text"]:lambda self,args: echo(f"text order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["text sel"]:lambda self,args: echo(f"text order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["image"]:lambda self,args: echo(f"image order: {args.get('data')}", file=sys.stdout),
            __cmd_codes["security"]:lambda self, args: self.server.user_browser._addon_security_function(args),
            __cmd_codes["lookup"]:lambda self, args: self.server.user_browser._addon_lookup_function(args)
        }

        stdout=sys.stdout

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))

            if(cmd:= self.__cmd_functions.get(data.get("command"))):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                cmd(self, data)
            else:
                self.send_error(400, "Wrong message")



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