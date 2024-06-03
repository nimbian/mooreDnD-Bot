import discord
from sqlhelper import *
from datetime import datetime, timezone
from pullhelper import *
from audit import *
from table2ascii import table2ascii as t2a, PresetStyle 
import random

async def buyPulls(sf, cl):
    gp = float(getGold(sf.did))
    uid = getUserID(sf.ctx.author.id)
    member = sf.ctx.author.display_name
    if sf.cost > gp:
        await sf.ctx.respond('You do not have enough gold', ephemeral=True)
        return
    for p in range(sf.pulls):
        mon, g, holo, v, combine = puller(random.choice(cl))
        collectMon(uid, mon[0], g, holo, v, datetime.now())
        response = '{} bought a pack containing a {} with a grade of {}'.format(member, mon[1] if mon[2] == 'BS' or mon[2] == 'IBS' else '{}[{}]'.format(mon[1],mon[2]) , g)
        if holo:
            response += ' and it was a HOLOGRAPHIC!!!!'
        response += ' it has a value of {}'.format(v)

        await sf.ctx.respond(response, file=combine)
    spendGold(sf.ctx.author.id, sf.cost)
    return

async def useToken(sf, cl):
    uid = getUserID(sf.ctx.author.id)
    member = sf.ctx.author.display_name
    ps = getPulls(sf.did)
    if ps <= 0:
        await sf.ctx.respond('No more pulls', ephemeral=True)
        return
    usePull(sf.did)
    for p in range(sf.pulls):
        mon, g, holo, v, combine = puller(random.choice(cl))
        collectMon(uid, mon[0], g, holo, v, datetime.now())
        response = '{} pulled a {} with a grade of {}'.format(member, mon[1] if mon[2] == 'BS' or mon[2] == 'IBS' else '{}[{}]'.format(mon[1],mon[2]) , g)
        if holo:
            response += ' and it was a HOLOGRAPHIC!!!!'
        response += ' it has a value of {}'.format(v)

        await sf.ctx.respond(response, file=combine)
    return

class a_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, tradeID, tmpview, bot):
        super().__init__(label="Accept!", style=discord.ButtonStyle.green)
        self.tradeID=tradeID
        self.tmpview=tmpview
        self.bot=bot
        
    #TODO add message to trade_channel
    async def callback(self, interaction: discord.Interaction):
        self.tmpview.disable_all_items()
        pid, rid, resp = acceptTrade(self.tradeID,self.bot)
        await interaction.response.send_message("Trade Accepted!", ephemeral=True)
        await auditPost(self.bot,resp,'trade')
        return

class r_button(discord.ui.Button):

    def __init__(self, tradeID, tmpview):
        super().__init__(label="Reject!",style=discord.ButtonStyle.red)
        self.tradeID = tradeID
        self.tmpview=tmpview
        

    async def callback(self, interaction: discord.Interaction):
        self.tmpview.disable_all_items()
        deleteTrade(self.tradeID)
        await interaction.response.send_message("Trade Rejected!", ephemeral=True)
        return


class w_button(discord.ui.Button):

    def __init__(self, tradeID):
        super().__init__(label="Withdraw!", style=discord.ButtonStyle.blurple)
        self.tradeID = tradeID

    async def callback(self, interaction: discord.Interaction):
        deleteTrade(self.tradeID)
        await interaction.response.send_message("Trade Withdrawn!", ephemeral=True)
        return

class c_button(discord.ui.Button):

    def __init__(self, uid, ouid, mcards, wcards, mmoney, wmoney):
        super().__init__(label="Confirm!", style=discord.ButtonStyle.green)
        self.uid = uid
        self.ouid = ouid
        self.mcards = mcards
        self.wcards = wcards
        self.mmoney = mmoney
        self.wmoney = wmoney

    async def on_timeout(self):
        self.disable_all_items()


    async def callback(self, interaction: discord.Interaction):

        uid = self.uid
        mcards = self.mcards
        wcards = self.wcards
        mmoney = self.mmoney
        wmoney = self.wmoney
        gp = float(getGold(self.uid))
        if mmoney > gp:
            await ctx.respond("You do not have that much gold", ephemeral=True)
            return
        for c in mcards:
            res = yourCard(c, uid)
            if res is None:
                await interaction.response.send_message("This is not your card(s)", ephemeral=True)
                return
        for c in wcards:
            res = cardExists(c)
            if res is None:
                await interaction.response.send_message("Wanted card does not exist", ephemeral=True)
                return
        res = sameOwner(wcards)
        if len(res) > 1:
            await interaction.response.send_message("Wanted cards not owned by same collector", ephemeral=True)
            return
        else:
            ouid = res[0][0]
        for c in wcards:
            res = yourCard(c, uid)
            if res:
                await interaction.response.send_message("You can't trade for your own card", ephemeral=True)
                return


        createTrade(getUserID(uid), ouid, mcards, wcards, mmoney, wmoney, datetime.now(timezone.utc))
        await interaction.response.send_message("Trade Submitted!", ephemeral=True)
        return


class s_button(discord.ui.Button):

    def __init__(self, uid, card, bot):
        super().__init__(label="Confirm!", style=discord.ButtonStyle.green)
        self.uid = uid
        self.card = card
        self.bot = bot

    async def on_timeout(self):
        self.disable_all_items()


    async def callback(self, interaction: discord.Interaction):

        uid = self.uid
        card = self.card
        for c in card:
            res = yourCard(c, uid)
            if res is None:
                await interaction.response.send_message("This is not your card(s)", ephemeral=True)
                return

        sellCards(uid, card)
        tmp = []
        for c in card:
            t = getCard(c)
            tmp += [t]
        out = t2a(
                header=['Card','Grade','Holo','Value'],
                body = tmp,
                style = PresetStyle.thin_compact
        )
        user = getUserName(uid)[0]
        resp = f"{user} sold these cards ```\n{out}\n```"
        await interaction.response.send_message("Cards Sold", ephemeral=True)
        await auditPost(self.bot,resp,'sell')
        return

class bm_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls, cost):
        super().__init__(label="Buy {} Monster Cards!".format(pulls), style=discord.ButtonStyle.green)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls
        self.cost = cost
        

    async def callback(self, interaction: discord.Interaction):
        await buyPulls(self, ['Monsters'])
        return

class bi_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls, cost):
        super().__init__(label="Buy {} Item Cards!".format(pulls), style=discord.ButtonStyle.blurple)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls
        self.cost = cost
        

    async def callback(self, interaction: discord.Interaction):
        await buyPulls(self, ['Item'])
        return


class br_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls, cost):
        super().__init__(label="Buy {} Random Cards!".format(pulls), style=discord.ButtonStyle.red)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls
        self.cost = cost
        return
        

    async def callback(self, interaction: discord.Interaction):
        await buyPulls(self, ['Monsters','Item'])

class pm_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls):
        super().__init__(label="Use token for {} Monster Cards!".format(pulls), style=discord.ButtonStyle.green)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls
        

    async def callback(self, interaction: discord.Interaction):
        await useToken(self, ['Monsters'])
        return

class pi_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls):
        super().__init__(label="Use token for {} Item Cards!".format(pulls), style=discord.ButtonStyle.blurple)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls
        

    async def callback(self, interaction: discord.Interaction):
        await useToken(self, ['Item'])
        return


class pr_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls):
        super().__init__(label="Use token for {} Random Cards!".format(pulls), style=discord.ButtonStyle.red)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls

    async def callback(self, interaction: discord.Interaction):
        await useToken(self, ['Monsters','Item'])
        return

class bs_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, did, sid, bot):
        super().__init__(label="Buy!", style=discord.ButtonStyle.green)
        self.did = did
        self.sid = sid
        self.bot = bot
        

    async def callback(self, interaction: discord.Interaction):
        gp = float(getGold(self.did))
        card = getShopCard(self.sid)
        if gp < float(card[6]):
            await self.ctx.respond('You do not have enough gold', ephemeral=True)
            return
        if card and int(self.sid) < 11:
            collectMon(getUserID(self.did), card[8], card[4], card[5], card[7], datetime.now())
        spendGold(self.did, float(card[6]))
        delFromShop(self.sid, self.did)
        resp = '{} purchased {} from the shop'.format(getUserName(self.did)[0], card[2])
        await interaction.response.send_message("Card Purchased!", ephemeral=True)
        await auditPost(self.bot,resp,'buy')
        return
