from typing import Set, Pattern, Union, List, Callable, Dict, Tuple

import re
import requests
import datetime
from time import sleep


ANALYSIS_CODE:Dict[str, int] = {
    "is url shortened" : 1,
    "iswebsitesafe danger level" : 2,
    "norton safety level" : 3,
    "get and load website" : 4
}
ANALYSIS_CODE_REVERSE:Dict[int, str] = {value:key for key,value in ANALYSIS_CODE.items()}

class Security_analizer:
    store_domain:bool = True
    seen_domains:Set[str]
    redirect_timeout:float = 3.0 # Works ok with mid-low conn speed 
    redirect_sleep:float = 0.1

    _domain_from_url:Pattern = re.compile(r"(https?://)?([\w\d]+(\.[\w\d]+)+)(\/|[^\w.]|$)")
    _xml_innerText:Pattern = re.compile(r"<.+?>")

    _shortUrl_regex:Pattern = re.compile(rb"\"destination\".+?>((https?://)?[\w\d]+\.[\w\d]+?.*?)\<\/")
    _safety_iswebsitesafe_regex:Pattern = re.compile(rb"Safe score:.*?>(\d+(\.\d+)?)")
    _safety_norton_regex:Pattern = re.compile(rb"big_rating_wrapper.*?<b.*?>(\w+).*?community-text.*?>(\d(\.\d+)?)", flags=re.S)

    __temp_url:str

    def __init__(self, browser:"Browser"=None, store_websites:str="domain"):
        self.seen_domains = set()

        self.browser = browser
        self.store_domain = store_websites.lower() == "domain"

    def __call__(self, url:str, domain:str=None, check_seen:bool=True) -> List[str]:
        if(not (check_seen and (domain or (domain := self._domain_from_url.search(url).groups()[1]) 
                if self.store_domain else url) in self.seen_domains)):
            self.__temp_url = url

            report = [self._check_shortUrl(url, check_seen=False)]

            print(f"URL: {self.__temp_url}")

            if(self.browser):
                report.append(self._get_analyze(self.__temp_url, check_seen=False))

            print(f"URL: {self.__temp_url}")

            for name in dir(self)[::-1]:
                if(name.startswith('_')): break
                elif(not ((local_var := self.__getattribute__(name)) and isinstance(local_var, Callable))): continue
                
                report.append(local_var(self.__temp_url, domain=domain, check_seen=False) or "")
            

            return report
        return []

    def _get_analyze(self, url:str, *, domain:str=None, check_seen:bool=True) -> Tuple[int, bool, str]:
        self.browser.open_link(url)
        self.browser.driver.execute_script(
            "setTimeout(window.onload = function(){window.readySTATE = true;}, "
                f"{self.redirect_timeout*1000});"
        )

        traceback = [url]

        while(self.browser.driver.execute_script("window.onload = function(){window.readySTATE = true;}; return !window.readySTATE;")):
            new_url = self.browser.driver.current_url
            if(url != new_url):
                traceback.append(url := new_url)

        timeout = datetime.datetime.now() + datetime.timedelta(seconds=self.redirect_timeout)

        while(datetime.datetime.now() < timeout):
            new_url = self.browser.driver.current_url
            if(url != new_url):
                traceback.append(url := new_url)
                timeout = datetime.datetime.now() + datetime.timedelta(seconds=self.redirect_timeout)

            sleep(self.redirect_sleep)

        self.browser.open_link("about:blank")
        self.browser.driver.delete_all_cookies()

        if(len(traceback) == 1):
            return (ANALYSIS_CODE["get and load website"], False, "Website doesn't have any redirects")

        self.__temp_url = url

        return (ANALYSIS_CODE["get and load website"], True, f"Website redirects through {' -> '.join(traceback)}")

    def _check_shortUrl(self, url:str, *, domain:str=None, check_seen:bool=True) -> Tuple[int, bool, str]:
        if(not (check_seen and (domain or (domain := self._domain_from_url.search(url).groups()[1]) 
                if self.store_domain else url) in self.seen_domains)):
            resp = requests.get(
                        f"https://unshorten.link/check?url={url}"
                    ).content
            unshortened = self._shortUrl_regex.search(
                    resp)

            if(unshortened is None):
                unshortened = url
            else:
                unshortened = unshortened.groups()[0].decode("utf-8")

            #print(f"shortUrl {unshortened}")

            if(url in unshortened):
                self.seen_domains.add(domain if self.store_domain else url)

                return (ANALYSIS_CODE["is url shortened"], False, unshortened)

            self.__temp_url = unshortened

            return (ANALYSIS_CODE["is url shortened"], True, unshortened)


    def check_safe_iswebsitesafe(self, url:str, *, domain:str=None, check_seen:bool=True) -> Tuple[int, bool, str]:
        if(not (check_seen and (domain or (domain := self._domain_from_url.search(url).groups()[1]) 
                if self.store_domain else url) in self.seen_domains)):

            resp = self._safety_iswebsitesafe_regex.search(
                    requests.get(
                        f"https://www.iswebsitesafe.net/search?search={url}"
                    ).content)

            if(resp is None):
                return (ANALYSIS_CODE["iswebsitesafe danger level"], True, f"Unknown website")

            received = float(resp.groups()[0].decode("utf-8"))
            
            if(received <= 1):
                self.seen_domains.add(domain if self.store_domain else url)
                return (ANALYSIS_CODE["iswebsitesafe danger level"], False, f"Safe website ({received})")

            return (ANALYSIS_CODE["iswebsitesafe danger level"], True, f"Unsafe website (danger level: {received})")


    def check_safe_norton(self, url:str, *, domain:str=None, check_seen:bool=True) -> Tuple[int, bool, str]:
        if(not (check_seen and (domain or (domain := self._domain_from_url.search(url).groups()[1]) 
                if self.store_domain else url) in self.seen_domains)):
            resp = requests.get(
                        f"https://safeweb.norton.com/report/show?url={url}"
                    ).content
            
            received, score = map(bytes.decode, self._safety_norton_regex.search(
                    resp).groups()[0:2])
            
            if(received == "SAFE" and float(score) >= 3):
                self.seen_domains.add(domain if self.store_domain else url)
                return (ANALYSIS_CODE["norton safety level"], False, f"Website is safe ({score}/5)")
            elif(received in {"SAFE", "UNTESTED"}):
                return (ANALYSIS_CODE["norton safety level"], True, "Website is "+(
                                                    f"untrusted ({score}/5)" if float(score) else 'unknown'))    

            return (ANALYSIS_CODE["norton safety level"], True, f"Website is unsafe ({score}/5)")

    def __example_function(self, url:str, *, domain:str=None, check_seen:bool=True) -> Tuple[int, bool, str]:
        raise NotImplementedError

        if(not (check_seen and (domain or (domain := self._domain_from_url.search(url).groups()[1]) 
                if self.store_domain else url) in self.seen_domains)):
            received = self._catch_received_info_regex.search(
                    requests.get(
                        f"https://url.example/check?url={url}"
                    ).content).groups()[0].decode("utf-8")
            
            if("safe" in received):
                self.seen_domains.add(domain if self.store_domain else url)
                return (ANALYSIS_CODE["example description"], False, "Everything is ok")

            return (ANALYSIS_CODE["example description"], True, "Something is actually wrong")

if __name__ == "__main__":
    main()