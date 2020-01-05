from OzBargain import OzBargain
import discord
from discord.ext import commands, tasks

MY_USER_ID = 206640727797530624
bot = commands.Bot(command_prefix='!')
ozb = OzBargain()
token = ''
with open('token.txt') as file:
    token = file.read()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    send_sales.start()


@bot.command()
async def quit(ctx):
    if ctx.author.id == MY_USER_ID:
        print('Quitting...')
        await ctx.send('Bye! 👋')
        send_sales.cancel()
        await bot.close()


@bot.command()
async def delete(ctx, sale_id):
    if ctx.author.id != MY_USER_ID:
        return

    if sale_id.isdigit():
        if ozb.sale_exists(sale_id, ozb.load_sales()):
            ozb.delete_sale(sale_id)
            await ctx.send(f'Sale {sale_id} successfully deleted')
            return

    await ctx.send('Invalid sale ID')


@tasks.loop(minutes=1.0)
async def send_sales():
    db_sales = [x for x in ozb.load_sales() if not ozb.has_expired(x)]
    # Get the eBay sales from OzBargain that haven't expired.
    ozb_sales = [x for x in ozb.get_ebay_sales() if not ozb.has_expired(x)]
    # Sales that haven't been added to the database haven't been sent yet.
    new_sales = [x for x in ozb_sales if not ozb.sale_exists(x['id'], db_sales)]

    if len(new_sales) > 0:
        # Add the new sales to the database.
        ozb.save_sales(new_sales)

        # Send the sales, mentioning the role.
        channel = bot.get_channel(662929547427315722)
        await channel.send('<@&662906994969280533>')
        for sale in new_sales:
            msg = f'{sale["link"].replace("goto", "node")}\n'
            await channel.send(msg)


bot.run(token)