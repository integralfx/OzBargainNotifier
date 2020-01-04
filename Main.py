import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import sqlite3
import discord
from discord.ext import commands, tasks

SALES_DB = 'sales.db'
conn = sqlite3.connect(SALES_DB)

MY_USER_ID = 206640727797530624
bot = commands.Bot(command_prefix='!')

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
    if len(sales) == 0:
        return

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


def delete_sale(sale_id):
    with conn:
        cur = conn.cursor()
        cur.execute(f'DELETE FROM Sales WHERE id=?', (sale_id,))
        conn.commit()


def has_expired(sale):
    return datetime.now(tz=pytz.UTC) > sale['expiry']


def sale_exists(sale_id, sales):
    for sale in sales:
        if int(sale_id) == int(sale['id']):
            return True

    return False


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print_sales.start()


@bot.command()
async def quit(ctx):
    if ctx.author.id == MY_USER_ID:
        print('Quitting...')
        await ctx.send('Bye! 👋')
        print_sales.cancel()
        await bot.close()


@bot.command()
async def delete(ctx, sale_id):
    if ctx.author.id != MY_USER_ID:
        return

    if sale_id.isdigit():
        if sale_exists(sale_id, load_sales()):
            delete_sale(sale_id)
            await ctx.send(f'Sale {sale_id} successfully deleted')
            return

    await ctx.send('Invalid sale ID')



@tasks.loop(minutes=1.0)
async def print_sales():
    db_sales = [x for x in load_sales() if not has_expired(x)]
    # Get the eBay sales from OzBargain that haven't expired.
    ozb_sales = [x for x in get_ebay_sales() if not has_expired(x)]
    # Sales that haven't been added to the database haven't been sent yet.
    new_sales = [x for x in ozb_sales if not sale_exists(x['id'], db_sales)]

    if len(new_sales) > 0:
        # Add the new sales to the database.
        save_sales(new_sales)

        # Send the sales, mentioning the role.
        channel = bot.get_channel(578867046587301889)
        msg = '<@&662906994969280533>\n'
        for sale in new_sales:
            msg += f'https://www.ozbargain.com.au/node/{sale["id"]}\n'

        await channel.send(msg)


bot.run('NTc4ODY2Njk0OTQxMDQ4ODMy.XN51vQ.Z2KmxPrgoPP3IT-U5gHxXUAjBM4')