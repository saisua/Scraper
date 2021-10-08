from Core.Browser import Browser
from Tests.crawling_basic import test_crawler_basic

from time import sleep

test_by_id:dict = {1:test_crawler_basic}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-t', '--test', help="The id of the test to perform.",
                        type=int, default=0)
    args = parser.parse_args()

    if(args.test):
        test_function = test_by_id.get(args.test)

        if(test_function is not None):
            print(f"Running function {test_function.__name__}")
            test_function()
        else:
            print(f"Wrong id detected. Please select one in range 1-{max(test_by_id.keys())}")
    else:
        with Browser() as br:
            print(br)
            input("Press enter to exit")
else:
    raise Exception("Wrong usage: scraper.py is just a user-oriented package,"
                    " and should not be imported.\n"
                    "Please, import the other files, such as Browser, User_browser or Crawler.")
