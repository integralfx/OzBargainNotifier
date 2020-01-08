import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import sqlite3
import codecs

def escape(s, errors="strict"):
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return "\"" + encodable.replace("\"", "\"\"") + "\""


'''
TODO: Use PostgreSQL
'''
class OzBargain():
    SALES_DB = 'sales.db'
    conn = sqlite3.connect(SALES_DB)

    def get_ebay_sales(self):
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
            sale['link'] = link
            sale['id'] = int(link[link.find('node/') + len('node/'):])
            sale['date_published'] = datetime.strptime(item.find('pubDate').text, '%a, %d %b %Y %H:%M:%S %z')
            
            sale['categories'] = []
            for cat in item.findall('category'):
                sale['categories'].append({
                    'name': cat.text,
                    'link': cat.get('domain')
                })

            meta = item.find('{https://www.ozbargain.com.au}meta')
            expiry = meta.get('expiry')
            sale['expiry'] = datetime.fromisoformat(expiry) if expiry else None

            sale['creator'] = item.find('{http://purl.org/dc/elements/1.1/}creator').text

            sales.append(sale)

        return sales


    def save_sales(self, sales):
        if len(sales) == 0:
            return

        with self.conn:
            sql = 'INSERT OR REPLACE INTO Sales(id, last_update, title, link, expiry, date_published, creator) VALUES'
            for sale in sales:
                if len(sale['categories']) > 0:
                    cat_sql = 'INSERT OR IGNORE INTO Category(name, link) VALUES'
                    map_sql = f'INSERT OR IGNORE INTO SalesCategory(sales_id, category_id) SELECT {sale["id"]}, id from Category WHERE '
                    for category in sale['categories']:
                        cat_sql += f'({escape(category["name"])}, "{category["link"]}"), '
                        map_sql += f'name={escape(category["name"])} OR '
                    cur = self.conn.cursor()
                    cur.execute(cat_sql[:-2])
                    cur.execute(map_sql[:-4])

                expiry = f'"{sale["expiry"].isoformat()}"' if sale['expiry'] else 'NULL'
                sql += f'({sale["id"]}, "{datetime.utcnow().isoformat()}", {escape(sale["title"])}, "{sale["link"]}", '
                sql += f'{expiry}, "{sale["date_published"].isoformat()}", "{sale["creator"]}"), '
            
            cur = self.conn.cursor()
            cur.execute(sql[:-2])


    def load_sales(self):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute('SELECT * FROM Sales')
            sales = []
            for row in cur.fetchall():
                # Get the categories
                sql = f'SELECT c.name, c.link FROM Category c, SalesCategory sc WHERE sc.sales_id={int(row[0])} AND '
                sql += 'c.id=sc.category_id'
                cur.execute(sql)

                sale = {
                    'id': int(row[0]),
                    'last_update': datetime.fromisoformat(row[1]),
                    'title': row[2],
                    'link': row[3],
                    'expiry': datetime.fromisoformat(row[4]) if row[4] else None,
                    'date_published': datetime.fromisoformat(row[5]),
                    'creator': row[6],
                    'categories': [{ 'name': r[0], 'link': r[1] } for r in cur.fetchall()]
                }
                sales.append(sale)

            return sales


    def delete_sale(self, sale_id):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(f'DELETE FROM Sales WHERE id=?', (sale_id,))
            self.conn.commit()


    def has_expired(self, sale):
        if not sale or not sale['expiry']:
            return False
        return datetime.now(tz=pytz.UTC) > sale['expiry']


    def sale_exists(self, sale_id, sales=[]):
        if len(sales) == 0:
            sales = self.load_sales()

        for sale in sales:
            if int(sale_id) == int(sale['id']):
                return True

        return False


    def load_categories(self):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute('SELECT * FROM Category')
            categories = []
            for row in cur.fetchall():
                category = {
                    'id': int(row[0]),
                    'name': row[1],
                    'link': row[2]
                }
                categories.append(category)

            return categories


    def save_categories(self, categories):
        if len(categories) == 0:
            return

        with self.conn:
            sql = 'INSERT OR REPLACE INTO Category(name, link) VALUES'
            for category in categories:
                sql += f'({escape(category["name"])}, {category["link"]}), '
            
            cur = self.conn.cursor()
            cur.execute(sql[:-2])