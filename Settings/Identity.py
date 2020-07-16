from random import randint, choice

class Identity():
    oscpu:tuple
    productSub:tuple
    vendor:tuple
    platform:tuple
    webdriver:tuple
    #appCodeName:tuple
    appVersion:tuple
    userAgent:tuple
    #language:tuple
    #languages:tuple
    screen_colors:tuple
    screen_pixel:tuple
    screen_width:tuple
    screen_height:tuple
    screen_availWidth:tuple
    screen_availHeight:tuple
    screen_outerWidth:tuple
    screen_outerHeight:tuple
    screen_innerWidth:tuple
    screen_innerHeight:tuple
    screen_sizeInW:tuple
    screen_availTop:tuple
    screen_availLeft:tuple


    _identity_options:dict = {"oscpu":(
                                "Intel Mac OS X", 
                                "PowerPC Mac OS X version _x._y", 
                                "macOS version _x._y", 
                                "Windows NT _x._y",
                                "Windows NT _x._y; WOW64",
                                "Windows NT _x._y; Win64; x64",
                                "WindowsCE _x._y",
                                "OS/2 Warp 3",
                                "OS/2 Warp 4",
                                "OS/2 Warp 4.5",
                                "Linux x86_64",
                                "Linux"),
                            "productSub":(
                                "20030107",
                                "20100101"
                            ),
                            "vendor":(
                                "",
                                "",
                                "",
                                "",
                                "Apple Computer, Inc.", 
                                "Google Inc."
                            ),
                            "platform":(
                                 "MacIntel", 
                                 "Win32", 
                                 "FreeBSD i386", 
                                 "WebTV OS",
                                 "Linux",
                                 "Linux x86_64"
                            ),
                            "appVersion":(
                                "_x.0",
                                "_x.0 (X11)"
                            ),
                            "screen_colors":(
                                15,
                                16,
                                18,
                                24,
                                30,
                                36,
                                48
                            ),
                            "screen_sizes":(
                                720,
                                1280,
                                1280,
                                1920,
                                1920,
                                1920,
                                3840,
                                4096,
                                7680
                            )}

    _aspect_ratios = [
        "1.85:1",
        "2.39:1",
        "4:3",
        "16:9",
        "1.6:1",
        "5:3",
        "1.9:1"
    ]

    @staticmethod
    def f_oscpu():
        Identity.oscpu = ("navigator", "oscpu", 
            choice(Identity._identity_options["oscpu"]).replace(
                '_x',str(randint(1,9))).replace(
                '_y',str(randint(1,9)))
            )

    @staticmethod
    def f_productSub():
        Identity.productSub = ("navigator", "productSub", choice(Identity._identity_options["productSub"]))

    @staticmethod
    def f_vendor():
        Identity.vendor = ("navigator", "vendor", choice(Identity._identity_options["vendor"]))

    @staticmethod
    def f_platform():
        Identity.platform = ("navigator", "platform", choice(Identity._identity_options["platform"]))

    @staticmethod
    def f_webdriver():
        Identity.webdriver = ("navigator", "webdriver", 0)

    @staticmethod
    def f_appVersion():
        Identity.appVersion = ("navigator", "appVersion", choice(Identity._identity_options["appVersion"])
            .replace('_x', str(randint(0,9))))

    @staticmethod
    def f_screen_colors():
        color_base = choice(Identity._identity_options["screen_colors"])
        Identity.screen_colors = ("screen", "colorDepth", color_base)
        Identity.screen_pixel = ("screen", "pixelDepth", color_base)

    @staticmethod
    def f_screen_size():
        width = choice(Identity._identity_options["screen_sizes"])
        w_aspect, h_aspect = map(float, choice(Identity._aspect_ratios).split(':'))

        height = int(width/w_aspect*h_aspect)


        width, height = int(width), int(height)

        Identity.screen_width = ("screen", "width", width)
        Identity.screen_availWidth = ("screen", "availWidth", width)
        Identity.screen_outerWidth = ("screen", "outerWidth", width)
        Identity.screen_innerWidth = ("screen", "innerWidth", width)
        Identity.screen_sizeInW = ("screen", "sizeInW", width)

        Identity.screen_height = ("screen", "height", height)
        Identity.screen_availHeight = ("screen", "availHeight", height)
        Identity.screen_outerHeight = ("screen", "outerHeight", height)
        Identity.screen_innerHeight = ("screen", "innerHeight", height)
        Identity.screen_sizeInH = ("screen", "sizeInH", height)

        Identity.screen_availTop = ("screen", "availTop", '0')
        Identity.screen_availLeft = ("screen", "availLeft", '0')

    @staticmethod
    def _userAgent():
        userA = "Mozilla/"

        appV = Identity.appVersion[2].replace('(','').replace(')','').split(' ')

        userA += f"{appV.pop(0)} ("
        if(len(appV)):
            userA += f"{appV[0]}; "

        vers = randint(1,99)

        userA += f"{Identity.platform[2]}; rv:{vers}.0) Gecko/{Identity.productSub[2]} Firefox/{vers}.0"

        Identity.userAgent = ("navigator", "userAgent", userA)

    @staticmethod
    def identity():
        classname = Identity.__name__.lower()

        values = []


        for var_name in dir(Identity)[::-1]:
            if(var_name.startswith('f_')):
                Identity.__getattribute__(Identity, var_name).__func__()

            elif(var_name.startswith("_")):
                break

        for var_name in dir(Identity)[::-1]:
            var = Identity.__getattribute__(Identity, var_name)

            if(var_name.startswith("_")):
                break
            elif(not var_name.startswith('f_') and not isinstance(var, staticmethod)):
                values.append(var)

            

        Identity._userAgent()
        values.append(Identity.userAgent)

        return values