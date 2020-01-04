from OzBargain import *
import discord
from discord.ext import commands, tasks

MY_USER_ID = 206640727797530624
bot = commands.Bot(command_prefix='!')

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