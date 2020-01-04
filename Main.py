import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import sqlite3

SALES_DB = 'sales.db'
conn = sqlite3.connect(SALES_DB)

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
    with conn:
        sql = 'INSERT OR REPLACE INTO Sales(id, last_update, title, link, expiry, date_published, creator) VALUES'
        for sale in sales:
            sql += f'({sale["id"]}, "{datetime.utcnow().isoformat()}", "{sale["title"]}", "{sale["link"]}", \
                     "{sale["expiry"].isoformat()}", "{sale["date_published"].isoformat()}", "{sale["creator"]}"), '

        cur = conn.cursor()
        cur.execute(sql[:-2])


def load_sales():
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sales')
        sales = []
        for row in cur.fetchall():
            sale = {
                'id': int(row[0]),
                'last_update': datetime.fromisoformat(row[1]),
                'title': row[2],
                'link': row[3],
                'expiry': datetime.fromisoformat(row[4]),
                'date_published': datetime.fromisoformat(row[5]),
                'creator': row[6]
            }
            sales.append(sale)

        return sales


if __name__ == '__main__':
    for sale in load_sales():
        if datetime.now(tz=pytz.UTC) > sale['expiry']:
            print(f'{"[Expired]"} {sale["id"]}')
        #print(f'{"Expired " if datetime.utcnow() > sale["expiry"] else ""}{sale["id"]}')