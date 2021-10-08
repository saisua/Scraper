from ..Core.Crawler import Crawler

def test_crawler_basic(start_url:str = "https://duckduckgo.com/?t=ffab&q=hi&atb=v1-1&ia=web"):
    with Crawler() as cr:
        cr(start_url)