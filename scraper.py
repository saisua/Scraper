from Browser import Browser

from time import sleep

if __name__ == "__main__":
    with Browser() as br:
        print(br)
        sleep(2)
else:
    raise Exception("Wrong usage: scraper.py is just a user-oriented package,"
                    " and should not be imported.\n"
                    "Please, import the other files, such as Browser, User_browser or Crawler.")