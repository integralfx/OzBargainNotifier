import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import sqlite3
from tqdm import tqdm

def get_ebay_sales():
    res = requests.get('https://www.ozbargain.com.au/tag/ebay-sale/feed')
    if not res:
        return []

    sales = []
    root = ET.fromstring(res.content)
    for item in root[0].findall('item'):
        sale = {}

        sale['title'] = item.find('title').text
        sale['description'] = item.find('description').text
        link = item.find('link').text
        sale['id'] = int(link[link.find('node/') + len('node/'):])
        sale['date_published'] = datetime.strptime(item.find('pubDate').text, '%a, %d %b %Y %H:%M:%S %z')

        meta = item.find('{https://www.ozbargain.com.au}meta')
        sale['link'] = meta.get('link')
        sale['expiry'] = datetime.fromisoformat(meta.get('expiry'))

        sale['creator'] = item.find('{http://purl.org/dc/elements/1.1/}creator').text

        sales.append(sale)

    return sales


def save_sales(sales):
    with sqlite3.connect('sales.db') as conn:
        sql = 'INSERT OR REPLACE INTO Sales(id, last_update, title, link, expiry, date_published, creator) VALUES'
        pbar = tqdm(sales, desc='Saving sales', unit='sales')
        for sale in pbar:
            pbar.set_postfix(id=sale['id'], title=sale['title'])
            sql += f'({sale["id"]}, "{datetime.utcnow().isoformat()}", "{sale["title"]}", "{sale["link"]}", \
                     "{sale["expiry"].isoformat()}", "{sale["date_published"].isoformat()}", "{sale["creator"]}"), '

        cur = conn.cursor()
        cur.execute(sql[:-2])


if __name__ == '__main__':
    save_sales(get_ebay_sales())