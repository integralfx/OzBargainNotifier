import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import sqlite3

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

        meta = item.find('{https://www.ozbargain.com.au}meta')
        sale['link'] = meta.get('link')
        sale['expiry'] = datetime.fromisoformat(meta.get('expiry'))

        sales.append(sale)

    return sales


if __name__ == '__main__':
    sales = get_ebay_sales()
    with sqlite3.connect('sales.db') as conn:
        sql = 'INSERT OR REPLACE INTO SalesUpdate(id, last_update) VALUES'
        for sale in sales:
            print(f'{sale["id"]} - {sale["title"]}')
            sql += f'({sale["id"]}, "{datetime.utcnow().isoformat()}"), '

        cur = conn.cursor()
        cur.execute(sql[:-2])