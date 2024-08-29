import random
from datetime import datetime, timezone, time
from sqlhelper import *
from pullhelper import *

async def mp(ctx, uid, member):
    await ctx.defer()
    mon, g, holo, v, combine, CR = puller(random.choice(['Monsters','Item']))
    eventCollectMon(uid, mon[0], g, holo, v, datetime.now(timezone.utc))
    response = '{} pulled a {} with a grade of {}'.format(member, mon[1] if mon[2] == 'BS' or mon[2] == 'IBS' else '{}[{}]'.format(mon[1],mon[2]) , g)
    if holo: 
        response += ' and it was a HOLOGRAPHIC!!!!'
    response += ' it has a value of {}'.format(v)
    await ctx.followup.send(response,file=combine)

async def gv(ctx, value, uid, member):
    if not value:
        await ctx.respond('You have to enter a guess in the event', ephemeral=True)
        return
    await ctx.defer()
    mon, g, holo, v, combine, CR = puller(random.choice(['Monsters','Item']))
    eventCollectMon(uid, mon[0], g, holo, v, datetime.now(timezone.utc))
    response = '{} pulled a {} with a grade of {}'.format(member, mon[1] if mon[2] == 'BS' or mon[2] == 'IBS' else '{}[{}]'.format(mon[1],mon[2]) , g)
    if holo: 
        response += ' and it was a HOLOGRAPHIC!!!!'
    response += ' it has a value of {}'.format(v)
    await ctx.followup.send(response,file=combine)
    tmp = cur + v
    await ctx.followup.send('You have a event collection value of {} which is {} under the goal value but don\'t go over'.format(tmp, getOption('pir') - tmp), ephemeral=True)

async def pir(ctx, uid, member):
    pir = int(getOption('pir'))
    cur = 0
    try:
        cur = float(getEvColValue(ctx.author.id)[0])
    except:
        pass
    if cur > pir:
         await ctx.respond('You\'ve pulled too much value' , ephemeral=True)
         return
    await ctx.defer()
    mon, g, holo, v, combine, CR = puller(random.choice(['Monsters','Item']))
    eventCollectMon(uid, mon[0], g, holo, v, datetime.now(timezone.utc))
    response = '{} pulled a {} with a grade of {}'.format(member, mon[1] if mon[2] == 'BS' else '{}[{}]'.format(mon[1],mon[2]) , g)
    if holo: 
        response += ' and it was a HOLOGRAPHIC!!!!'
    response += ' it has a value of {}'.format(v)
    await ctx.followup.send(response,file=combine)
    tmp = cur + float(v)
    if tmp > pir:
        await ctx.followup.send('You have a event collection value of {} which is over.  Better luck next time'.format(round(tmp,3)), ephemeral=True)
    else:
        await ctx.followup.send('You have a event collection value of {} which is {} under the goal value but don\'t go over'.format(round(tmp,3), round(int(getOption('pir')) - tmp,3)), ephemeral=True)

async def raid(ctx, uid, member):
    await ctx.defer()
    name = getOption('bbeg')
    hp = int(getOption('bbegavghp'))
    pulls = int(getOption('bbegpulls'))
    cnt = int(getOption('raidcnt'))
    tothp = hp * pulls * cnt
    try:
        cur = float(getBBEGdmg()[0])
    except:
        cur = 0 
    if cur >= tothp:
         await ctx.respond('{} has already been defeated...Stop! Stop! He\'s already dead'.format(name) , ephemeral=True)
         return
    mon, g, holo, v, combine, CR = puller(random.choice(['Item']))
    TC = getTreasureChance(mon[1])
    if random.random() < 1/(TC[1]+1):
        T = getTreasure(TC[0]) 
        addTreasure(uid,T[3])
        response = '{} pilfered a {}'.format(member, T[2])
        v = 0
    else:
        eventCollectMon(uid, mon[0], g, holo, v, datetime.now(timezone.utc))
        response = '{} used a {} with a power level of {}'.format(member, mon[1] if mon[2] == 'BS' or mon[2] == 'IBS' else '{}[{}]'.format(mon[1],mon[2]) , g)
        if holo: 
            response += ' and it was a CRITICAL HIT!!!!'
        response += ' to deal {} damage'.format(v)
    await ctx.followup.send(response,file=combine)
    tmp = cur + float(v)
    if tmp >= tothp:
        await ctx.followup.send('{} has defeated {} Huzzah!'.format(member,name).upper())
    else:
        await ctx.followup.send('You have dealt {} damage to {} and has {} hp remaining'.format(getEvColValue(ctx.author.id)[0], name, round(tothp - tmp,3)), ephemeral=True)
    


async def doEvent(ctx, value=None):
    ev = getActiveEvent()
    uid = getUserID(ctx.author.id)
    member = ctx.author.display_name
    e = ''
    if ev:
        e = ev[0]
    if e == 'mp':
        await mp(ctx, uid, member)
    elif e == 'gv':
        await gv(ctx, value, uid, member)
    elif e == 'pir':
        await pir(ctx, uid, member)
    elif e == 'raid':
        await raid(ctx, uid, member)
    else:
        await ctx.respond('No current event', ephemeral=True)
