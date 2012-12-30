import urllib
import re
import time
import database

posted_count_regex = re.compile("strong[>](\d+) For Sale[<][/]strong")
posted_price_regex = re.compile("from [<]span class=[\"]price[\"][>][$](.*)[<][/]span[>]")

def fetch_release_posted(releaseid):
    x = database.get_last_posted(releaseid, 3)
    if x:
        return (int(x["count"]), float(x["price"]))
    url = "http://www.discogs.com/release/" + str(releaseid)
    count = 0
    price = 0.0
    data = urllib.urlopen(url).read()
    time.sleep(1)
    count_result = posted_count_regex.search(data)
    price_result = posted_price_regex.search(data)
    if count_result and price_result:
        count = int(count_result.group(1))
        price = float(price_result.group(1))
    database.put_posted(releaseid, price, count, 0.0, 0.0, 0.0, 0.0)
    return (count, price)

    

def fetch_release_sales(releaseid):
    pass
