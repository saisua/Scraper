from Browser import Browser
from threading import Thread
from multiprocessing import Process, Manager
from operator import attrgetter
import time

from os import chdir
from sys import argv
if(len(argv) > 1):
    chdir(argv[1])

from Video_Scrapper import multi_in_operator

try:
    from Structures.Sockets.Servers.RPC import RPC
except ImportError as err:
    print("Please run setup.py before running/importing Distributed_Browser.py")
    raise err

def main():
    raise NotImplementedError("Not tackled security issues regarding of serializing shared data")

    browser = Browser(["google.com"])
    serv = RPC('1',ip=input("ip > ")or"localhost",port=12412,start_on_connect=False)

    keywords = ["elecciones","debate","electoral","directo","iglesias","casado"]
    video_urls_result = Manager().list()

    serv.to_run = custom_run
    serv.args_parall = [[browser, video_urls_result, multi_in_operator(keywords)]]

    serv.open()

    input("\nPress enter to start\n")
    serv.run_parall()

    while(not all(map(attrgetter("ready"), serv._result))): time.sleep(.5)

    res = RPC.flatten(serv.result)
    print(res)


def custom_run(browser, video_urls_result, keywords):
    from Video_Scrapper import scrapping
    import Browser
    
    browser.open()
    scrapping(browser, video_urls_result, keywords)

    return 1


if __name__ == "__main__":
    main()