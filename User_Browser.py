print("Starting User_Browser imports...  ")
from multiprocessing import Process, Manager
from re import search
from collections import defaultdict
import sys
import io

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

from Browser import Browser
from Structures.Site import Site
from Structures.Async_generator import AGenerator

print("Done (User_Browser)")

def main():
    browser = Controlled_Browser(
            verbose=True,
            headless=False
            )

    browser.open(
            #enable_interceptor=True, 
            interceptor_kwargs={"process_non_realtime":True}
            )
    
    browser.driver.switch_to.window("11")
    for link in sys.argv[1:]:
        if(validate_url(link)):
            browser.open_link(link, new_tab=True)
        else:
            browser.open_link(f"https://duckduckgo.com/?q={link}", new_tab=True)
    
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


class Controlled_Browser(Browser, AbstractEventListener):
    secondary_browser:Browser = None

    _cmd_url:str

    verbose:bool=False
    keep_record:bool=False

    def __init__(self, *args, **kwargs):
        self.__is_open = False

        self.verbose = kwargs.pop("verbose", False)
        self.keep_record = kwargs.pop("keep_record", False)

        if(kwargs.pop("enable_secondary_browser", False)):
            self.secondary_browser = Browser(*args, **{**kwargs, "headless":True})

        Browser.__init__(self, *args, **kwargs)

    def open(self, **kwargs):
        self.__is_open = True

        Browser.open(self, **{**kwargs, "event_listener_obj":self
                            ,"block_cookies":False
                            })

        if(not self.secondary_browser is None):
            self.secondary_browser.open(self, **{**kwargs, "event_listener_obj":self
                            ,"block_cookies":False
                            })

        self._cmd_url = self.driver.command_executor._url
        print(f"Browser is in {self._cmd_url}/session/{self.driver.session_id}")

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
            try:
                if(len(self.driver.window_handles) > self.num_tabs):
                    self.num_tabs = len(self.driver.window_handles)
                    if(self.verbose): print(self.driver.window_handles)
                    self.driver.switch_to.window(
                            Controlled_Browser.find_unique(self.driver.window_handles, 
                                                            list(self._site_from_tab.keys())))
                    self.after_open_new_tab(self.driver.current_window_handle)
                    
                    self.last_tab, bef_tab = bef_tab, self.driver.current_window_handle

                    #print("0",end='\r')
                elif(len(self.driver.window_handles) < self.num_tabs):
                    self.num_tabs = len(self.driver.window_handles)

                    closed_tab = Controlled_Browser.find_unique(list(self._site_from_tab.keys()),
                                                    self.driver.window_handles)

                    self.after_close_tab(closed_tab)

                    self._site_from_tab.pop(closed_tab)
                    del closed_tab

                    self.driver.switch_to.window(self.last_tab)
                    bef_tab = self.last_tab
                    
                    self.after_switch_to_tab(bef_tab)
                
                    
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
                        """)
                # Same tab, same site, new directory
                elif(tab.link != self.driver.current_url and self._site_from_tab.get(self.driver.current_window_handle).link == tab.link):
                    if(self.keep_record):
                        self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url, 
                                                    parent=tab)
                    else:
                        self._site_from_tab[self.driver.current_window_handle] = Site(self.driver.current_url)
                        del tab

                    self.after_navigated_to(self.driver.current_url, self.driver)

            except NoSuchWindowException:
                continue

    ### EVENTS

    def after_open_new_tab(self, tab):
        if(self.verbose): print("Opened new tab ", tab)

    def after_switch_to_tab(self, tab):
        if(self.verbose): 
            url_print = self._site_from_tab.get(tab)
            print("Switched to tab ", url_print.link if url_print else tab)

    def before_navigate_to(self, url, driver):
        if(self.verbose): print("(Driver) before_navigate_to ", url) 

    def after_navigate_to(self, url, driver):
        if(self.verbose): print("(Driver) after_navigate_to ", url)

    def after_navigated_to(self, url, driver):
        if(self.verbose): print("Got ", url)

        self.driver.delete_all_cookies()
        #self.driver.execute(Command.CLEAR_APP_CACHE)
        #self.driver.execute(Command.CLEAR_LOCAL_STORAGE)
        #self.driver.execute(Command.CLEAR_SESSION_STORAGE)

    def after_close_tab(self, tab):
        if(self.verbose): print(f"Closed tab  {tab} ({self._site_from_tab[tab].link})")

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

if __name__ == "__main__":
    main()