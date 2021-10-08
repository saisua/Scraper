# Local cimports
from Utils.utils cimport to_cstring as to_cstr

# Internal imports
import json
from random import choice

# External imports
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium import webdriver

# Internal cimports
from libcpp cimport bool as cbool
from libcpp.string cimport string as cstr
from libcpp.unordered_map cimport unordered_map as cumap # C-unordered map
from libcpp.vector cimport vector
from libcpp.queue cimport queue

cdef vector[cstr] DOWNLOAD_MIME_TYPES = iter((
    b'application/epub+zip',
    b'application/gzip',
    b'application/java-archive',
    b'application/json',
    b'application/ld+json',
    b'application/msword',
    b'application/octet-stream',
    b'application/ogg',
    b'application/pdf',
    b'application/rtf',
    b'application/vnd.amazon.ebook',
    b'application/vnd.apple.installer+xml',
    b'application/vnd.mozilla.xul+xml',
    b'application/vnd.ms-excel',
    b'application/vnd.ms-fontobject',
    b'application/vnd.ms-powerpoint',
    b'application/vnd.oasis.opendocument.presentation',
    b'application/vnd.oasis.opendocument.spreadsheet',
    b'application/vnd.oasis.opendocument.text',
    b'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    b'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    b'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    b'application/vnd.rar',
    b'application/vnd.visio',
    b'application/x-7z-compressed',
    b'application/x-abiword',
    b'application/x-bzip',
    b'application/x-bzip2',
    b'application/x-csh',
    b'application/x-freearc',
    b'application/x-httpd-php',
    b'application/x-sh',
    b'application/x-shockwave-flash',
    b'application/x-tar',
    b'application/xhtml+xml',
    b'application/xml ',
    b'application/zip',
    b'audio/3gpp',
    b'audio/3gpp2',
    b'audio/aac',
    b'audio/midi',
    b'audio/mpeg',
    b'audio/ogg',
    b'audio/opus',
    b'audio/wav',
    b'audio/webm',
    b'audio/x-midi',
    b'font/otf',
    b'font/ttf',
    b'font/woff',
    b'font/woff2',
    b'image/bmp',
    b'image/gif',
    b'image/jpeg',
    b'image/png',
    b'image/svg+xml',
    b'image/tiff',
    b'image/vnd.microsoft.icon',
    b'image/webp',
    b'text/calendar',
    b'text/css',
    b'text/csv',
    b'text/html',
    b'text/javascript',
    b'text/plain',
    b'text/xml',
    b'video/3gpp',
    b'video/3gpp2',
    b'video/mp2t',
    b'video/mpeg',
    b'video/ogg',
    b'video/webm',
    b'video/x-msvideo'
))

cpdef get_configuration(dict kwargs={}, 
                        object capabilities=None, object options=None, object profile=None,
                        str json_file_name="default.json"):

    # Keep as python string since it will be concat later for open()
    cdef str path = '//'.join(__file__.split('/')[:-1])

    if(capabilities is None):
        # https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities
        capabilities = DesiredCapabilities.FIREFOX.copy()

    if(options is None):
        options = webdriver.firefox.options.Options()
    options.set_preference("browser.popups.showPopupBlocker",False)

    cdef object download_no_prompt
    cdef cbool headless, block_cookies, disable_downloads, autoload_videos
    cdef cbool enable_drm, load_images, disable_javascript, enable_extensions

    cdef int tabs_per_window
    cdef dict proxys
    cdef str http_proxy, ssl_proxy, ftp_proxy, socks_proxy
    cdef dict json_dict

    with open(f"{path}//config_files//{json_file_name}", 'r') as file:
        json_dict = json.load(file)

    cdef dict def_args = json_dict["arguments"]

    # definition of variables, either from the dict or from the json
    headless = kwargs.get("headless", def_args.get("headless"))
    load_images = kwargs.get("load_images", def_args.get("load_images"))
    disable_downloads = kwargs.get("disable_downloads", def_args.get("disable_downloads"))
    disable_javascript = kwargs.get("disable_javascript", def_args.get("disable_javascript"))
    autoload_videos = kwargs.get("autoload_videos", def_args.get("autoload_videos"))
    proxys = kwargs.get("proxys", def_args.get("proxys"))
    block_cookies = kwargs.get("block_cookies", def_args.get("block_cookies")) 
    enable_drm = kwargs.get("enable_drm", def_args.get("enable_drm"))
    enable_proxies = kwargs.get("enable_proxies", def_args.get("enable_proxies")) 
    download_no_prompt = kwargs.get("download_no_prompt", def_args.get("download_no_prompt"))
    enable_extensions = kwargs.get("enable_extensions", def_args.get("enable_extensions")) 
    extensions = kwargs.get("extensions", def_args.get("extensions"))
    tabs_per_window = kwargs.get("tabs_per_window", def_args.get("tabs_per_window"))
    ###



    if(headless):
        #DeprecationWarning: use setter for headless property instead of options.set_headless()
        options.headless = True

    if(profile is None):
        profile = webdriver.FirefoxProfile()


    cdef dict preferences = profile.DEFAULT_PREFERENCES["frozen"]
    cdef list to_remove = json_dict["frozen"] 
    # Remove frozen configuration settings defined in the json
    
    for option in to_remove:
        preferences.pop(option)
    ###

    cdef dict profile_preferences = json_dict["profile"]

    #http://kb.mozillazine.org/About:config_entries  #profile
    #http://kb.mozillazine.org/Categorhttps://stackoverflow.com/qhttps://stackoverflow.com/questions/20884089/dynamically-changing-proxy-in-firefox-with-selenium-webdriveruestions/20884089/dynamically-changing-proxy-in-firefox-with-selenium-webdrivery:Preferences

    for preference, value in profile_preferences.items():
        profile.set_preference(preference, value)
    profile.set_preference("dom.popup_maximum", tabs_per_window)
    profile.set_preference("browser.search.region",choice([
                "AF","AL","DZ","AS","AD","AO","AQ","AG","AR","AM",
                "AW","AU","AT","AZ","BS","BH","BD","BB","BY","BE",
                "BZ","BJ","BM","BT","BO","BA","BW","BV","BR","IO",
                "BN","BG","BF","BI","KH","CM","CA","CV","KY","CF",
                "CF","TD","CL","CN","CX","CC","CO","KM","CG","CD",
                "CK","CR","CI","HR","CU","CY","CZ","DK","DJ","DM",
                "DO","EC","EG","SV","GQ","ER","EE","ET","FK","FO",
                "FJ","FI","FR","GF","PF","TF","GA","GM","GE","DE",
                "GH","GI","GR","GL","GD","GP","GU","GT","GN","GW",
                "GY","HT","HM","HK","HU","IS","IN","ID","IR","IQ",
                "IE","IL","IT","JM","JP","JO","KZ","KE","KI","KP",
                "KR","KW","KG","LA","LB","LS","LR","LY","LI","LT",
                "LU","MO","MK","MG","MW","MY","MV","ML","MT","MH",
                "MQ","MT","MU","YT","MX","FM","MD","MC","ME","MS",
                "MA","MZ","MM","NA","NR","NP","NL","AN","NC","NZ",
                "NI","NE","NG","NU","NF","MP","NO","OM","PK","PW",
                "PS","PA","PG","PY","PE","PH","PN","PL","PT","PR",
                "QA","RE","RO","RU","RW","SH","KN","LC","PM","VC",
                "WS","SM","ST","SA","SN","RS","SC","SL","SG","SK",
                "SI","SB","SO","ZA","GS","ES","LK","SD","SR","SJ",
                "SZ","SE","CH","SY","TW","TJ","TZ","TH","TZ","TH",
                "TL","TG","TK","TO","TT","TN","TR","TM","TC","TV",
                "UG","UA","AE","GB","US","UM","UY","UZ","VU","VE",
                "VN","VG","VI","WF","EH","YE","ZM","ZW"]))
    
    if(isinstance(block_cookies, str) and "all" in block_cookies.lower()):
        profile.set_preference("network.cookie.cookieBehavior", 2)
        print("Cookies are disabled. This may cause some websites to not work")
    else:
        #print(int(block_cookies))
        profile.set_preference("network.cookie.cookieBehavior", int(block_cookies))

    if(disable_downloads):
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.panel.shown", False)
        profile.set_preference("browser.download.useDownloadDir", False)
        profile.set_preference("services.sync.prefs.sync.browser.download.useDownloadDir", False)
        profile.set_preference("pdfjs.disabled", True)
    #profile.set_preference("browser.translation.neverForLanguages", "*")

    if(autoload_videos):
        profile.set_preference("dom.media.autoplay.autoplay-policy-api", True)
        profile.set_preference("media.autoplay.enabled.user-gestures-needed", False)
        profile.set_preference("media.block-autoplay-until-in-foreground", False)
        profile.set_preference("media.autoplay.default", 0)
        profile.set_preference("dom.require_user_interaction_for_beforeunload", False)
        profile.set_preference("browser.preferences.defaultPerformanceSettings.enabled", True)
    else:
        profile.set_preference("dom.media.autoplay.autoplay-policy-api", False)
        profile.set_preference("media.autoplay.enabled.user-gestures-needed", True)
        profile.set_preference("media.block-autoplay-until-in-foreground", True)
        profile.set_preference("media.autoplay.default", 1)
        profile.set_preference("browser.preferences.defaultPerformanceSettings.enabled", False)

    if(enable_drm):
        profile.set_preference("media.eme.enabled", True)

    if(download_no_prompt):
        if(download_no_prompt == "all"):
            download_no_prompt = ';'.join(DOWNLOAD_MIME_TYPES)+';'

        profile.set_preference("browser.download.useDownloadDir", True)
        profile.set_preference("browser.download.dir", path+"//downloads//")
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", download_no_prompt)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("pdfjs.disabled", True)


    #Test
    profile.set_preference("network.manage-offline-status", True)
    profile.set_preference("browser.offline", True)

    options.add_argument("--lang=en")

    capabilities['marionette'] = True
    capabilities["dom.popup_maximum"] = tabs_per_window
    capabilities['browserName'] = choice(["android", "chrome", "firefox", "htmlunit",
                                        "internet explorer", "iPhone", "iPad", "opera", "safari"])
    capabilities['version'] = ""
    capabilities['platform'] = ""
    capabilities["locationContextEnabled"] = False
    capabilities["databaseEnabled"] = False
    capabilities["applicationCacheEnabled"] = False
    capabilities["browserConnectionEnabled"] = False
    capabilities["webStorageEnabled"] = False

    # Not tested
    #if(max_cache_RAM_KB): profile.set_preference("browser.cache.memory.capacity",max_cache_RAM_KB)

    if(not load_images):
        profile.set_preference("permissions.default.image", 2)

    if(disable_javascript):
        capabilities["javascriptEnabled"] = False
        profile.set_preference("javascript.enabled", False)

    #breakpoint()
    if(enable_extensions):
        import os

        ext_path = path+"//..//Extensions//"

        if(True):
            print("[?] Compiling scraper extension. If this instance is not for debugging purposes,"+
                    " this should not be happening.")

            import zipfile

            with zipfile.ZipFile(ext_path+"scraper-extension//scraper-extension.xpi", 'w') as file:
                for root, dirs, files in os.walk(ext_path+"Scraper-src//"):
                    for source in files:
                        file.write(f"{root}//{source}", 
                            arcname=f"{root[root.find('Scraper-src//')+len('Scraper-src//')-1:]}/{source}"
                        )

        for root, dirs, files in os.walk(ext_path):
            for name in files:
                if(name.endswith(".xpi")):
                    print(f"Added extension \"{name}\"")
                    profile.add_extension(f"{root}//{name}")


        for extension in extensions:
            profile.add_extension(extension)


    http_proxy = proxys.pop("httpProxy", '')
    ssl_proxy = proxys.pop("sslProxy", '')
    ftp_proxy = proxys.pop("ftpProxy", '')
    socks_proxy = proxys.pop("socksProxy", '')

    if(enable_proxies or len(http_proxy) or len(ssl_proxy) or len(ftp_proxy) or len(socks_proxy)):
        profile.set_preference("network.proxy.type", 1)

    if(len(http_proxy)): 
        http_proxy, http_port = http_proxy.split(':')
        profile.set_preference("network.proxy.http", http_proxy)
        profile.set_preference("network.proxy.http_port", int(http_port)) 
    if(len(ssl_proxy)): 
        ssl_proxy, ssl_port = ssl_proxy.split(':')
        profile.set_preference("network.proxy.ssl", ssl_proxy)
        profile.set_preference("network.proxy.ssl_port", int(ssl_port)) 
    if(len(ftp_proxy)): 
        ftp_proxy, ftp_port = ftp_proxy.split(':')
        profile.set_preference("network.proxy.ftp", ftp_proxy)
        profile.set_preference("network.proxy.ftp_port", int(ftp_port)) 
    if(len(socks_proxy)):
        socks_proxy, socks_port = socks_proxy.split(':')
        profile.set_preference("network.proxy.socks", socks_proxy)
        profile.set_preference("network.proxy.socks_port", int(socks_port)) 

    return options, profile, capabilities