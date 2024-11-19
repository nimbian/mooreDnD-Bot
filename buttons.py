import discord
from sqlhelper import *
from datetime import datetime, timezone
from pullhelper import *
from audit import *
from table2ascii import table2ascii as t2a, PresetStyle 
import random
import yaml

with open('godspeak.yml', 'r') as f:
    GODS = yaml.safe_load(f)

async def buyPulls(sf, cl):
    gp = float(getGold(sf.did))
    uid = getUserID(sf.ctx.author.id)
    member = sf.ctx.author.display_name
    if sf.cost > gp:
        await sf.ctx.respond('You do not have enough gold', ephemeral=True)
        return
    cr_list = []
    for p in range(sf.pulls):
        mon, g, holo, v, combine, CR = puller(random.choice(cl))
        cr_list.append(CR)
        collectMon(uid, mon[0], g, holo, v, datetime.now())
        response = '{} bought a pack containing a {} with a grade of {}'.format(member, mon[1] if mon[2] in ['BS', 'IBS', 'LBS'] else '{}[{}]'.format(mon[1],mon[2]) , g)
        if holo:
            response += ' and it was a HOLOGRAPHIC!!!!'
        response += ' it has a value of {}'.format(v)

        await sf.ctx.respond(response, file=combine)
    spendGold(sf.ctx.author.id, sf.cost)
    #await sf.ctx.respond('{} "{}"'.format(random.choice(GODS['voices']), random.choice(GODS[max(cr_list)]))) 
    return

async def useToken(sf, cl):
    uid = getUserID(sf.ctx.author.id)
    member = sf.ctx.author.display_name
    ps = getPulls(sf.did)
    if ps <= 0:
        await sf.ctx.respond('No more pulls', ephemeral=True)
        return
    usePull(sf.did)
    cr_list = []
    for p in range(sf.pulls):
        mon, g, holo, v, combine, CR = puller(random.choice(cl))
        cr_list.append(CR)
        collectMon(uid, mon[0], g, holo, v, datetime.now())
        response = '{} pulled a {} with a grade of {}'.format(member, mon[1] if mon[2] in ['BS', 'IBS', 'LBS'] else '{}[{}]'.format(mon[1],mon[2]) , g)
        if holo:
            response += ' and it was a HOLOGRAPHIC!!!!'
        response += ' it has a value of {}'.format(v)

        await sf.ctx.respond(response, file=combine)
    #await sf.ctx.respond('{} "{}"'.format(random.choice(GODS['voices']), random.choice(GODS[max(cr_list)]))) 
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
        try:
            pid, rid, resp = acceptTrade(self.tradeID,self.bot)
            await interaction.response.send_message("Trade Accepted!", ephemeral=True)
            await auditPost(self.bot,resp,'trade')
        except:
            pass
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
        super().__init__(label="Buy {} Creature Cards!".format(pulls), style=discord.ButtonStyle.green)
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

class bl_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls, cost):
        super().__init__(label="Buy {} Location Cards!".format(pulls), style=discord.ButtonStyle.grey)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls
        self.cost = cost


    async def callback(self, interaction: discord.Interaction):
        await buyPulls(self, ['Locations'])
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
        await buyPulls(self, ['Monsters','Item','Locations'])

class pm_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls):
        super().__init__(label="Use token for {} Creature Cards!".format(pulls), style=discord.ButtonStyle.green)
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

class pl_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls):
        super().__init__(label="Use token for {} Location Cards!".format(pulls), style=discord.ButtonStyle.grey)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls


    async def callback(self, interaction: discord.Interaction):
        await useToken(self, ['Locations'])
        return


class pr_button(discord.ui.Button):
	#TODO add protection
    def __init__(self, ctx, did, pulls):
        super().__init__(label="Use token for {} Random Cards!".format(pulls), style=discord.ButtonStyle.red)
        self.ctx = ctx
        self.did = did
        self.pulls = pulls

    async def callback(self, interaction: discord.Interaction):
        await useToken(self, ['Monsters','Item','Locations'])
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

c = 0

class dview(discord.ui.View):



    bnum = random.sample(range(0,25),4)
    def set(self):
        global bnum 
        bnum = random.sample(range(0,25),4)
   


    c1 = 0
    c2 = 0
    c = 0
    #tmpview = discord.ui.View(timeout=60)
    for i in range(0,5):
        for j in range(0,5):
            if (i*5 + j) in bnum:
                if c1 == 0:
                    @discord.ui.button(label="O", row=i, style=discord.ButtonStyle.green)
                    async def b1_callback(self, button, interaction):
                        button.disabled = True
                        await interaction.response.edit_message(view=self)
                        if len(['x' for i in self.children if i.disabled]) == 4:
                            await interaction.followup.send("Dice retrieved", ephemeral=True)
                elif c1 == 1:
                    @discord.ui.button(label="O", row=i, style=discord.ButtonStyle.green)
                    async def b2_callback(self, button, interaction):
                        button.disabled = True
                        await interaction.response.edit_message(view=self)
                        if len(['x' for i in self.children if i.disabled]) == 4:
                            await interaction.followup.send("Dice retrieved", ephemeral=True)
                elif c1 == 2:
                    @discord.ui.button(label="O", row=i, style=discord.ButtonStyle.green)
                    async def b3_callback(self, button, interaction):
                        button.disabled = True
                        await interaction.response.edit_message(view=self)
                        if len(['x' for i in self.children if i.disabled]) == 4:
                            await interaction.followup.send("Dice retrieved", ephemeral=True)
                elif c1 == 3:
                    @discord.ui.button(label="O", row=i, style=discord.ButtonStyle.green)
                    async def b4_callback(self, button, interaction):
                        button.disabled = True
                        await interaction.response.edit_message(view=self)
                        if len(['x' for i in self.children if i.disabled]) == 4:
                            await interaction.followup.send("Dice retrieved", ephemeral=True)
                c1 += 1
            else:
                if c2 == 0:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b5_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 1:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b6_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 2:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b7_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 3:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b8_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 4:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b9_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 5:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b10_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 6:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b11_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 7:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b12_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 8:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b13_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 9:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b14_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 10:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b15_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 11:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b16_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 12:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b17_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 13:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b18_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 14:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b19_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 15:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b20_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 16:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b21_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 17:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b22_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 18:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b23_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 19:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b24_callback(self, button, interaction):
                        await interaction.response.send_message("")
                if c2 == 20:
                    @discord.ui.button(label="x", row=i, style=discord.ButtonStyle.red)
                    async def b25_callback(self, button, interaction):
                        await interaction.response.send_message("")
                c2 += 1

class g_button(discord.ui.Button):
    def __init__(self,c=1):
        super().__init__(label="", style=discord.ButtonStyle.green)
        self.c = c

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        if self.c == 4:
            await interaction.response.send_message("Done", ephemeral=True)
            return -1
        await interaction.response.edit_message(view=super())
        await interaction.response.send_message(self.c, ephemeral=True)
        return self.c+1


class x_button(discord.ui.Button):
    def __init__(self):
        super().__init__(label="", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        return 1

