import discord
import os
import random
from datetime import datetime, timezone, time
from table2ascii import table2ascii as t2a, PresetStyle
from sqlhelper import *
from buttons import *
import csv
#from PIL import Image, ImageDraw, ImageFont
#import shutil
#from pathlib import Path
from discord.ext import tasks, commands
from pullhelper import *
from imgStuff import *
from events import *
from trades import *
import yaml

with open('config.yml', 'r') as f:
     CONFIG  = yaml.safe_load(f)


Collections = "/home/bramsel/pybot/collections/"
Images = "/home/bramsel/pybot/images/"
URL = " https://www.moorednd.com"

bot = discord.Bot()

def perm(ctx):
    return ctx.author.id == 1214255387193245726 or ctx.author.id == 257535802223886339

@bot.event
async def on_ready():
    leaderboard.start()
    roles.start()
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name = "gold", description = "See how much gold you have")
async def gold(ctx):
    if ctx.author.bot:
        return
    gold = getGold(ctx.author.id)
    await ctx.respond('You have {} gold'.format(str(round(gold,3))), ephemeral=True)

@bot.slash_command(name = "collection", description = "See your collection or specify a user")
async def collection(ctx, user=None):
    if ctx.author.bot:
        return
    await ctx.respond('Bot Thinking:', ephemeral=True)
    head = 'See all collections at: {}/\n'.format(URL)
    if user:
        res = getCollection(user[2:-1])
        if res:
            head += '{}\'s collection: {}/satchemon/user/{} '.format(URL,getUserName(user[2:-1])[0], user[2:-1])
        else:
            await ctx.respond('This user has no collection yet', ephemeral=True)
            return
    else:
        res = getCollection(ctx.author.id)
        head += 'Your collection:  {}/satchemon/user/{} '.format(URL,ctx.author.id)
    tmp = []
    for r in res:
        tmp += [[r[0], r[1], r[2], r[3], r[4], 'Yes' if r[5] else 'No', r[7]]]
    output = t2a(
        header=["CardID", "CR", "Card", "Expansion", "Grade", "Holo", "Value"],
        body = tmp,
        style = PresetStyle.thin_compact
    )
    out = head + f"```\n{output}\n```"
    await ctx.respond(out, ephemeral=True)

@bot.slash_command(name = "sendmsg", description = "ADMIN COMMAND to give send msg")
@discord.ext.commands.check(perm)
async def send_msg(ctx, msg):
    await ctx.respond(msg)

@bot.slash_command(name = "givetoken", description = "ADMIN COMMAND to give a token to user")
@discord.ext.commands.check(perm)
async def give_token(ctx, user):
    giveToken(user[2:-1])
    await ctx.respond('Token given', ephemeral=True)

@bot.slash_command(name = "givegold", description = "ADMIN COMMAND to give gold to user")
@discord.ext.commands.check(perm)
async def give_gold(ctx, user, gold):
    giveGold(user[2:-1], float(gold))
    await ctx.respond('Gold given', ephemeral=True)

@bot.slash_command(name = "addpromo", description = "ADMIN COMMAND to add gold promo")
@discord.ext.commands.check(perm)
async def add_promo(ctx, code, gold):
    addPromo(code, gold)
    await ctx.respond('Promo Added', ephemeral=True)


@bot.slash_command(name = "delevcol", description = "ADMIN COMMAND to delete event collection")
@discord.ext.commands.check(perm)
async def delevcol(ctx):
    delEvCollection()
    await ctx.respond('Event collection deleted', ephemeral=True)

@bot.slash_command(name = "getevcol", description = "ADMIN COMMAND to export event collection")
@discord.ext.commands.check(perm)
async def getevcol(ctx):
    res = getEvCollection()
    res2 = getEvTreCol()
    f = os.path.join(Collections, "EV.csv" )
    f2 = os.path.join(Collections, "EVT.csv" )
    try:
        os.remove(f)
    except:
        pass
    try:
        os.remove(f2)
    except:
        pass
    with open(f, 'w+') as csvfile:
        sw = csv.writer(csvfile)
        sw.writerow(["User","Card","Grade","Holo","Value"])
        for r in res:
            sw.writerow(r)
    file = discord.File(f)
    await ctx.respond(file=file, ephemeral=True)
    with open(f2, 'w+') as csvfile:
        sw = csv.writer(csvfile)
        sw.writerow(["User","Treasure","Value"])
        for r in res2:
            sw.writerow(r)
    file = discord.File(f2)
    await ctx.respond(file=file, ephemeral=True)

@bot.slash_command(name = "trade", description = "Propose a trade /trade (your card id(s)) (wanted card id(s) comma seperated")
async def trade(ctx, wantedcard, mycard=None, mymoney=0, wantedmoney=0):
    await tradeIt(ctx, wantedcard, mycard, mymoney, wantedmoney)

@bot.slash_command(name = "active_trades", description = "List all trades you're involved in")
async def atrades(ctx):
    if ctx.author.bot:
        return
    await ptrades(ctx)
    await rtrades(ctx,bot)

@bot.slash_command(name = "promo", description = "Enter a promo code")
async def promo(ctx,promo):
    if ctx.author.bot:
        return
    uid = getUserID(ctx.author.id)
    if uid is None:
        createUser(user,ctx.author.id)
        uid = getUserID(ctx.author.id)
    res = getPromos(promo.upper())
    print(res)
    if res:
        if res[5] == 'N':
            response = "This Promo has expired please tune in next time!"
            await ctx.respond(response, ephemeral=True)
            return
        else:
            if usedPromo(uid, res[6]):
                response = "You have already used this promo"
                await ctx.respond(response, ephemeral=True)
                return
            else:
                pTracker(uid, res[6])
                if res[0] == 0:
                    print(res[2])
                    giveGold(ctx.author.id, res[2])
                    response = "You have been given {} gold".format(res[2])
                    await ctx.respond(response, ephemeral=True)
                    return

                else:
                    collectMon(uid, res[0], res[4], res[3], res[2], datetime.now())
                    response = "The promo card has been added to your collection"
                    await ctx.respond(response, ephemeral=True)
                    return
    else:
        response = 'Invalid Promo'
        await ctx.respond(response, ephemeral=True)
        return

@bot.slash_command(name = "pull", description = "Pull a Card")
async def pull(ctx):
    if ctx.author.bot:
        return
    uid = getUserID(ctx.author.id)
    if uid is None:
        user = ctx.author.name
        createUser(user,ctx.author.id)
        uid = getUserID(ctx.author.id)
    member = ctx.author.display_name
    ps = getPulls(ctx.author.id)
    if ps <= 0:
        n = datetime.now()
        t = n + timedelta(days=1)
        x = datetime.combine(t, time.min) - n
        await ctx.respond('Out of pulls a new one will be given in {} hours and {} minutes'.format(int(x.seconds // 3600), int(x.seconds % 3600 // 60)), ephemeral=True)
        return
    if str(datetime.strftime(datetime.now(), '%m-%d')) == '04-01':
        gd20 = os.path.join(Images, createD20img(20,'g'))
        bd20 = os.path.join(Images, createD20img(20,'b'))
        td10 = os.path.join(Images, createD10img(100,'t'))
        sd10 = os.path.join(Images, createD10img(100,'s'))
        tmp = combineImgs(gd20, bd20, td10, sd10)
        combine = discord.File(tmp)
        response = 'APRIL FOOLS!!!!'
        await ctx.respond(response,file=combine, ephemeral=True)

    pulls = 3
    tmpview = discord.ui.View(timeout=60)
    tmpview.add_item(pm_button(ctx, ctx.author.id, pulls))
    tmpview.add_item(pi_button(ctx, ctx.author.id, pulls))
    tmpview.add_item(pr_button(ctx, ctx.author.id, pulls))
    resp = "Use a token for {} cards?".format(pulls)
    await ctx.respond(resp, view=tmpview, ephemeral=True)
    return

@tasks.loop(minutes=10)
async def leaderboard():
    lc = bot.get_channel(int(getOption('leaderchannel')))
    res = mostValuableCollection() 
    c = createLeader(res,'c')
    await lc.send('', file=c, delete_after=600)
    res = getBestCards()
    at = createLeader(res[0],'at')
    await lc.send('', file=at, delete_after=600)
    m = createLeader(res[1],'m')
    await lc.send('', file=m, delete_after=600)
    d7 = createLeader(res[2],'d7')
    await lc.send('', file=d7, delete_after=600)
    t = createLeader(res[3],'t')
    await lc.send('', file=t, delete_after=600)
    

@tasks.loop(minutes=10)
async def roles():
    sets = hasSets()
    cs = flattenRoles(getCompletedSets())
    for s in sets:
        for did in sets[s]:
            try:
                if s in cs:
                    if not did in cs[s]:
                        addToCS(did, s)
                        await addRole(did, s)
                else:
                    addToCS(did, s)
                    await addRole(did, s)
            except:
                pass

    for c in cs:
        for tmp in cs[c]:
            if not tmp in sets[c]:
                try:
                    delFromCS(tmp, c)
                    await delRole(tmp, c)
                except:
                    pass
            

def flattenRoles(cs):
    tmp = {}
    for c in cs:
        if c[0] not in tmp:
            tmp[c[0]] = []
        tmp[c[0]] += [c[1]]
    return tmp


@bot.slash_command(name = "endevent", description = "ADMIN ONLY COMMAND to stop event")
@discord.ext.commands.check(perm)
async def endEvent(ctx):
    deactivateEvent()
    await ctx.respond('Event ended', ephemeral=True)


@bot.slash_command(name = "startevent", description = "ADMIN ONLY COMMAND to stop event")
@discord.ext.commands.check(perm)
async def startEvent(ctx,event):
    activateEvent(event)
    await ctx.respond('Event started', ephemeral=True)


@bot.slash_command(name = "event", description = "Command to participate in current event")
@discord.ext.commands.cooldown(1,10, type=discord.ext.commands.BucketType.user)
async def event(ctx, value=None):
    await doEvent(ctx, value)

@bot.slash_command(name = "shop", description = "Buy Cards from shop")
async def shop(ctx, shopcardid=None):
    if ctx.author.bot:
        return
    if not shopcardid:
        res = shopCards()
        tmp = []
        for r in res:
            tmp += [[r[0], r[1], r[2], r[3], r[4], 'Yes' if r[5] else 'No', r[6]]]
        output = t2a(
                header=["ShopID", "CR", "Card", "Expansion", "Grade", "Holo", "Sell Price"],
            body = tmp,
            style = PresetStyle.thin_compact
        )
        head = "Current stock:"
        out = head + f"```\n{output}\n```"
        await ctx.respond(out, ephemeral=True)
    else:
        card = getShopCard(shopcardid)
        if not card:
            await ctx.respond("No card for that", ephemeral=True)
            return
        gp = float(getGold(ctx.author.id))
        if gp < float(card[6]):
            await ctx.respond('You do not have enough GP', ephemeral=True)
            return
        card = card[0:7]
        output = t2a(
            header=["ShopID", "CR", "Card", "Expansion", "Grade", "Holo", "Value"],
            body = [card],
            style = PresetStyle.thin_compact
        )
        out = f"```\n{output}\n```"
        tmpview = discord.ui.View(timeout=60)
        tmpview.add_item(bs_button(ctx.author.id, shopcardid, bot))
        resp = f"Buy this card ?:\n```\n{output}\n```"
        await ctx.respond(resp, view=tmpview, ephemeral=True)

@bot.slash_command(name = "buypulls", description = "Buy a pack for cards")
async def buypulls(ctx):
    if ctx.author.bot:
        return
    pulls = int(getOption('buypulls'))
    cost = float(getOption('buycost'))
    did = ctx.author.id
    gp = float(getGold(did))
    if cost > gp:
        await ctx.respond('You do not have enough gold', ephemeral=True)
        return
    tmpview = discord.ui.View(timeout=60)
    tmpview.add_item(bm_button(ctx, ctx.author.id, pulls, cost))
    tmpview.add_item(bi_button(ctx, ctx.author.id, pulls, cost))
    tmpview.add_item(br_button(ctx, ctx.author.id, pulls, cost))
    resp = "Buy {} cards for {}?".format(pulls, cost)
    await ctx.respond(resp, view=tmpview, ephemeral=True)
    return
        

@bot.slash_command(name = "sell", description = "Sell your cards")
async def sell(ctx, cards):
    if ctx.author.bot:
        return
    uid = getUserID(ctx.author.id)
    card = set(cards.split(','))
    for c in card:
        res = yourCard(c, ctx.author.id)
        if res is None:
            await ctx.respond("This is not your card(s)", ephemeral=True)
            return
    tmpview = discord.ui.View(timeout=60)
    tmpview.add_item(s_button(ctx.author.id, card, bot))
    cs = list(card)
    tmp = []
    tv = 0
    for c in cs:
        t = getCard(c)
        tmp += [t]
        tv += t[3]

    output = t2a(
        header=["Card", "Grade", "Holo", "Value"],
        body = tmp,
        style = PresetStyle.thin_compact
    )
    tv = round(tv,3) 
    resp = f"Sell these for {tv}?:\n```\n{output}\n```"
    await ctx.respond(resp, view=tmpview, ephemeral=True)


async def addRole(did, role):
    guild = await bot.fetch_guild(int(getOption('guild')))
    user = await guild.fetch_member(did)
    trole = discord.utils.get(guild.roles, name=role)
    resp = '{} was given the title {}'.format(getUserName(did)[0], role)
    await auditPost(bot, resp, 'add')
    await user.add_roles(trole)

async def delRole(did, role):
    guild = await bot.fetch_guild(int(getOption('guild')))
    user = await guild.fetch_member(did)
    trole = discord.utils.get(guild.roles, name=role)
    resp = '{} lost the title {}'.format(getUserName(did)[0], role)
    await auditPost(bot, resp, 'del')
    await user.remove_roles(trole)

@event.error
async def on_command_error(ctx, error):
    if ctx.author.bot:
        return
    if isinstance(error, discord.ext.commands.CommandOnCooldown):
        await ctx.respond('Event timer cooldown {} second(s)'.format(int(error.retry_after % 60)), ephemeral=True)
        return
    raise error

#@bot.slash_command(name = "test", description = "List all commands")
#async def test(ctx,c=1):
#    #bnum = random.randint(1,25)
#    #tmpview = discord.ui.View(timeout=60)
#    #for i in range(0,5):
#    #    for j in range(0,5):
#    #        if (i*5 + j) == bnum:
#    #            t = g_button(c)
#    #            t.label = "O"
#    #        else:
#    #            t = x_button()
#    #            t.label = "X"
#    #        t.row = i
#    #        tmpview.add_item(t)
#    tmp = dview()
#    tmp.set()
#    await ctx.respond(view=tmp, ephemeral=True)

@bot.slash_command(name = "help", description = "List all commands")
async def help(ctx):
    helptext = "```"
    embed = discord.Embed(
        colour = discord.Colour.orange()
    )
    embed.add_field(name='Link to all collections', value='{}/satchemon/'.format(URL))
    embed.set_author(name='DnD Bot Help Page')
    for c in bot.commands:
        if 'ADMIN' not in c.description:
            embed.add_field(name='/{}'.format(c.name), value=c.description, inline=False)
    await ctx.respond(embed=embed, ephemeral=True)


bot.run(CONFIG['bot']['token'])
