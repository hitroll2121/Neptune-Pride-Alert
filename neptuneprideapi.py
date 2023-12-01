import requests
from typing import Optional
import discord
from discord import app_commands
import threading
import asyncio
import json
import copy
import pickle
import time
import math
from discord.ext import commands
global usedumydata
usedumydata = True
if usedumydata == True:
    with open('testingdata.pkl', 'rb') as file:
        dumydata = pickle.load(file)
global alltrackedgames
global discorduser
global discorduserlock
global colors

colors = ["blue:1168715144780587148","light_blue:1168715148136042497","green:1168715147158769735","yellow:1168715154146471936","orange:1168715149448843344","red:1168715152892375101","pink:1168715151160127560","purple:1168715151596326954"]

deafult_message_turn_based = "<@{scandata['discord_id']}> A turn has happened in game {scandata['scanning_data']['name']} the new deadline for submitting your turn is in <t:{int(scandata['scanning_data']['turn_based_time_out']/1000)}:R>"
deafult_message = "<:{colors[pcolor_number]}><@{rawscaningdata['discord_id']}> you are being attacked on planet: {star['n']} In game: {scaningdata['name']} by, <:{colors[color_number]}> {scaningdata['players'][str(fleet['puid'])]['alias']} it will be there in <t:{timestamp}:R> at <t:{timestamp}:t>"

alltrackedgames = []
discorduser = {}
discorduserlock = {}



MY_GUILD = discord.Object(id=1164343949536800789)  # replace with your guild id


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        await self.tree.sync()
        #self.tree.copy_global_to(guild=MY_GUILD)
        #await self.tree.sync(guild=MY_GUILD)



intents = discord.Intents.all()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print('\n------\n')
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    await on_reboot()


@client.tree.command(name='add-game')
@app_commands.describe(
    apikey='your api key',
    gameid='your game id',
)
async def add_a_game_to_be_tracked(interaction: discord.Interaction, apikey: str, gameid: str):
    await interaction.response.send_message(await add_data_to_logged_list(gameid,apikey, interaction.user.id, interaction.channel_id), ephemeral=True)


@client.tree.command(name='reset-messages-to-default')

async def reset_message(interaction: discord.Interaction, ):
    discorduser[interaction.user.id]["turnbased"] = deafult_message_turn_based
    discorduser[interaction.user.id]["realtime"] = deafult_message

    with open('test.pkl', 'wb') as file:
        pickle.dump(discorduser, file)


    interaction.response.send_message("reset all messages to default",ephemeral=True)


@client.tree.command(name='view-current-message')

async def view_message(interaction: discord.Interaction, ):
    msg=""
    if "turnbased" in discorduser[interaction.user.id].keys:
        msg = f"{discorduser[interaction.user.id]['turnbased']}\n"
    if "realtime" in discorduser[interaction.user.id].keys:
        msg = msg + discorduser[interaction.user.id]["realtime"]
    interaction.response.send_message(msg,ephemeral=True)



@client.tree.command(name='change-message')
@app_commands.describe(
    message='notification message',
    msgtype="turn based, real time"
)
async def change_message(interaction: discord.Interaction, message: str,msgtype: str):
    global discorduser
    print("changing msg")
    if msgtype == "turn based":
        discorduser[interaction.user.id]["turnbased"] = message
        await interaction.response.send_message("changed message successfully make sure you test it!",ephemeral=True)
    if msgtype == "real time":
        discorduser[interaction.user.id]["realtime"] = message
        await interaction.response.send_message("changed message successfully make sure you test it!",ephemeral=True)


@client.tree.command(name='refresh-game')
@app_commands.describe(
)
async def refresh_game(interaction: discord.Interaction):
    user_id = interaction.user.id
    thread_id = interaction.channel_id
    await interaction.response.send_message(await findapifromthreadforrefresh(user_id, thread_id)
)

@client.tree.command(name='remove-game')
@app_commands.describe(
)
async def remove_a_game_to_be_tracked(interaction: discord.Interaction):
    user_id = interaction.user.id
    thread_id = interaction.channel_id
    #alltrackedgames.append(["remove", int(time.time())+10, user_id, thread_id])
    await remove_game(user_id, thread_id)
    #await interaction.response.send_message("game removed from tracking thread will be deleted in a minute or two")



async def remove_game(user_id, thread_id):
    try:
        #msg = "a error occurred"


        user_game = copy.deepcopy(discorduser[user_id])

        for data in user_game:
            data = user_game[data]
            if data[2] == thread_id:
                await stoptracking(user_id, data[0])
                discorduser[user_id].pop(data[0])
                await client.get_channel(thread_id).delete()

                with open('test.pkl', 'wb') as file:
                    # A new file will be created
                    pickle.dump(discorduser, file)
    except:
        print("a error occurred in remove game")





#async def gettimetillatack(px,py,cx,cy):


async def findapifromthreadforrefresh(user_id, thread_id):
    user_game = discorduser[user_id]

    for data in user_game:
        data = user_game[data]
        if data[2] == thread_id:
            returnmsg = await removeschedualedcheck(user_id,data[0])
            return returnmsg
    return "a error occurred"
async def stoptracking(user_id, apikey):
    global alltrackedgames

    for game in alltrackedgames:
        if user_id == game[3]:
            gamedata=game[2]
            if gamedata[0] == apikey:
                alltrackedgames.remove(game)


async def removeschedualedcheck(user_id, apikey):
    global alltrackedgames

    for game in alltrackedgames:
        if user_id == game[3]:
            gamedata=game[2]
            if gamedata[0] == apikey:

                game2 = copy.deepcopy(game)
                alltrackedgames.remove(game)
                await checkgames(game2[2])
                return "getting api data"
    return "couldn't find game"

async def on_reboot():
    global discorduser
    global discorduserlock
    loop = asyncio.get_event_loop()
    loop.create_task(checkforactivegame())
    try:
        with open('test.pkl', 'rb') as file:
            data = pickle.load(file)

    except:
        with open('test.pkl', 'wb') as file:
            pickle.dump(discorduser, file)

        with open('test.pkl', 'rb') as file:
            data = pickle.load(file)

    discorduser = copy.deepcopy(data)
    discorduserlock = copy.deepcopy(data)
    for userid in data:
        for apikey in data[userid]:
            game_data = data[userid][apikey]
            gapikey = game_data[1]
            gameid = game_data[0]
            scandata = getapidata(gapikey, gameid)
            if "scanning_data" in scandata.keys():
                nextick = timetillnexttick(scandata)

                run_function_after_time(data[userid][apikey], nextick)
            else:
                print(scandata)


async def add_data_to_logged_list(gameid, apikey, discordid, channel_id):
    global discorduser

    if discordid not in discorduser.keys():
        discorduser[discordid] = {}

    discord_user_data = discorduser[discordid]

    if apikey in discord_user_data.keys():
        return "error already tracked"

    else:
        payload = getapidata(gameid, apikey)
        if "scanning_data" in payload.keys():



            #print(timetillnexttick(payload))

            #print(discorduser[discordid])

            newthread = await client.get_channel(int('1129257693790609470')).create_thread(name=payload["scanning_data"]["name"], message=None,
                                                                                           type=discord.ChannelType.private_thread,
                                                                                           reason=None, invitable=True,
                                                                                           slowmode_delay=None)



            channel_id = newthread.id

            #print(discordid)

            userobj = client.get_user(discordid)

            #print(userobj)

            await newthread.add_user(userobj)

            payload["channel_id"] = channel_id
            payload["discord_id"] = discordid
            payload["api_key"] = apikey
            payload["game_id"] = gameid

            time_till_next_turn = -1

            if payload["scanning_data"]["turn_based"] == 1:
                time_till_next_turn = payload["scanning_data"]["turn_based_time_out"]


            discorduser[discordid][apikey] = [apikey, gameid, channel_id, discordid,payload["scanning_data"]["name"],payload["scanning_data"]["started"],time_till_next_turn,[]]
            # apikey, game id, channel id, user id, name, started, time till next turn, locked planets
            usergamedata = discorduser[discordid][apikey]
            print(apikey)
            with open('test.pkl', 'wb') as file:
                # A new file will be created
                pickle.dump(discorduser, file)

            run_function_after_time(usergamedata, timetillnexttick(payload))

            return f"started tracking {payload['scanning_data']['name']}"
        else:
            return payload


async def checkgames(usergamedata):
    global discorduser
    scandata = getapidata(usergamedata[1], usergamedata[0])
    if "scanning_data" not in scandata.keys():
        print("api data failed most likely due to a regenerated api key reminder add checking to auto remove this in the future")
        run_function_after_time(usergamedata, 3600)
        return
    scandata["channel_id"] = usergamedata[2]
    scandata["discord_id"] = usergamedata[3]
    scandata["api_key"] = usergamedata[0]
    scandata["game_id"] = usergamedata[1]
    # apikey, game id, channel id, user id, name, started, time till next turn, planet lock
    #    0        1        2          3       4      5           6                  7
    checkattack = analyze_data(scandata)

    channel_id = usergamedata[2]
    channel = client.get_channel(channel_id)


    if checkattack != "no attacks":
        print(usergamedata)
        channel_id = usergamedata[2]

        channel = client.get_channel(channel_id)
        await channel.send(checkattack)


    if usergamedata[5] == True:
        if scandata["scanning_data"]["started"] == False:
            usergamedata[5] = True
            channel_id = usergamedata[2]
            channel = client.get_channel(channel_id)
            await channel.send(f"<@{scandata['discord_id']}> Your game {scandata['scanning_data']['name']} has started")


    if scandata["scanning_data"]["turn_based"] == 1:
        if scandata["scanning_data"]["turn_based_time_out"] != usergamedata[6]:
            usergamedata[6] = scandata["scanning_data"]["turn_based_time_out"]
            #theres a bug here since this is not saved a restart might clear the value if a game is not added or rmeoved but its fine for now
            await channel.send(f"<@{scandata['discord_id']}> A turn has happened in game {scandata['scanning_data']['name']} the new deadline for submitting your turn is in <t:{int(scandata['scanning_data']['turn_based_time_out']/1000)}:R>")

        run_function_after_time(usergamedata, 3600)
        return


    if (scandata["scanning_data"]["production_counter"] == 0) and (scandata["scanning_data"]["started"] == True and scandata["scanning_data"]['tick_fragment'] < 1 and scandata["scanning_data"]["turn_based"] == 0):
        channel_id = usergamedata[2]
        channel = client.get_channel(channel_id)
        await channel.send(f"<@{scandata['discord_id']}> There was a production cycle in {scandata['scanning_data']['name']}")



    next_tick = timetillnexttick(scandata)

    run_function_after_time(usergamedata, next_tick)



def timetillnexttick(data):
    global usedumydata
    if usedumydata == True:
        return 5
    scandata = data["scanning_data"]

    #print(f"calculating time till next tick in game {scandata['name']}")
    tick_fragment = scandata["tick_fragment"]
    tick_rate = scandata["tick_rate"]
    #print(f"tick fragment {tick_fragment}")
    #print(f"tick rate{tick_rate}")
    time_in_sec = ((tick_rate - (tick_fragment * tick_rate)) * 60) + (60 * 10)
    #print(f"time in min {(((tick_rate - (tick_fragment * tick_rate)) * 60) + (60 * 10)) / 60}")

    if scandata["turn_based"]==1:
        print(f"calculating time till next tick in game {scandata['name']}: 3600")
        return 3600

    if tick_fragment > 1:
        print("ghost tick detected checking again in 10 min to see if anyone has logged in")
        print(f"calculating time till next tick in game {scandata['name']}: 600")



        return 600
    elif time_in_sec < 300:
        print(f"calculating time till next tick in game {scandata['name']}: 300")
        return 300
    else:
        print(f"calculating time till next tick in game {scandata['name']}: {time_in_sec}]")
        return time_in_sec


def analyze_data(rawscaningdata):
    global discorduser
    global colors
    global discorduserlock
    allattacks = []
    scaningdata = rawscaningdata["scanning_data"]
    fleets = scaningdata["fleets"]
    pid = scaningdata["player_uid"]
    for fleetid in fleets.keys():
        fleet = fleets[fleetid]
        if fleet["puid"] != pid:
            starkey = scaningdata["stars"]
            for starid in scaningdata["stars"].keys():
                star = starkey[starid]
                if star["puid"] == pid:
                    if "ouid" not in fleet.keys():
                        fleetorderlist = fleet["o"]
                        fleetorder = fleetorderlist[0]
                        if int(fleetorder[1]) == int(starid):

                            color_number = int(fleet['puid'] % 8)
                            pcolor_number = int(pid % 8)
                            timestamp = getattacktimestamp(fleet, star, scaningdata)
                            print(discorduser)

                            discord_id = rawscaningdata['discord_id']
                            print(discorduser)
                            if "realtime" in discorduser[discord_id].keys():
                                message = discorduser[discord_id]["realtime"]
                                #way better add this later formated_msg = message.format(rawscaningdata=rawscaningdata,colors=colors,pcolor_number=int(pcolor_number),star=star,scaningdata=scaningdata,fleet=fleet,timestamp=timestamp,color_number=color_number)

                                self_color = f"<:{colors[int(pcolor_number)]}>"
                                color = f"<:{colors[color_number]}>"
                                ping = f"<@{rawscaningdata['discord_id']}>"
                                star_name = star['n']
                                game_name = scaningdata['name']
                                player_name = scaningdata['players'][str(fleet['puid'])]['alias']
                                time_r = f"<t:{timestamp}:R>"
                                time_a = f"<t:{timestamp}:t>"
                                ship_num = fleet["st"]
                                your_ship_num = star["st"]

                                match = {
                                "%self_color%": self_color,
                                "%color%": color,
                                "%ping%": ping,
                                "%star%": star_name,
                                "%star_ships%": your_ship_num,
                                "%time%": time_a,
                                "%eta%": time_r,
                                "%player%": player_name,
                                "%game%": game_name,
                                "%ships%":ship_num
                                }
                                formated_message = message
                                for m in match:

                                    formated_message=str(match[m]).join(formated_message.split(m))

                                formated_msg_and_id = [formated_message,fleetid,starid]
                                allattacks.append(formated_msg_and_id)
                            else:
                                allattacks.append([f"<:{colors[int(pcolor_number)]}><@{rawscaningdata['discord_id']}> you are being attacked on planet: {star['n']} In game: {scaningdata['name']} by, <:{colors[color_number]}> {scaningdata['players'][str(fleet['puid'])]['alias']} it will be there in <t:{timestamp}:R> at <t:{timestamp}:t>", fleetid, starid])
    if len(allattacks) > 0:
        discord_id = rawscaningdata["discord_id"]
        api_key = rawscaningdata["api_key"]
        print(discorduser)
        gameforlock=discorduser[discord_id][api_key][7]
        newgameforlock = []
        new_allattacks = []
        for data in allattacks:

            if str(data[1])+str(data[2]) in gameforlock:
                print("notification suppressed")
            else:
                 new_allattacks.append(data)

            newgameforlock.append(str(data[1])+str(data[2]))

        allattacks = copy.deepcopy(new_allattacks)
        discorduser[discord_id][api_key][7] = copy.deepcopy(newgameforlock)
        allatckstext=[]
        for attacks in allattacks:
            allatckstext.append(attacks[0])
        newlinejoin = "\n"
        if len(allattacks) <= 0:
            return "no attacks"


        #print("your being attacked")
        #print(newlinejoin.join(allatckstext))
        return newlinejoin.join(allatckstext)
    else:
        return "no attacks"

def getattacktimestamp(ship, planet, data):
    x1 = float(ship["x"])
    y1 = float(ship["y"])
#convert to int
    if ship["w"] == 0:
        wm = 0.33
    else:
        wm = 1

    x2 = float(planet["x"])
    y2 = float(planet["y"])

    # it's time for those useless math equations I thought I was never going to use again

    d = (math.sqrt(((x1 - x2)**2) + ((y1 - y2)**2)))

    ticks = math.ceil((d*8)/wm)

    game_time = ticks*data["tick_rate"]
    real_time = game_time-(data["tick_fragment"]*data["tick_rate"])

    time_in_sec = real_time*60

    unix_timestamp = time.time()+time_in_sec

    return int(unix_timestamp)

def getapidata(game_id,api_key):
    if usedumydata == True:
        return dumydata
    root = "https://np.ironhelmet.com/api"
    params = {"game_number": game_id,
              "code": api_key,
              "api_version": "0.1"}
    payload = requests.post(root, params).json()

    return payload



def run_function_after_time(data, time_in_seconds):
    global alltrackedgames
    alltrackedgames.append([data[4], int(time.time()+time_in_seconds), data, data[3]])
    #print("game added to tracked list "+ str(time.time())+ " trigger: " + str(time.time()+time_in_seconds)+" name: "+str(data[4]))

async def checkforactivegame():
    global alltrackedgames
    while True:
        if usedumydata == True:
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(60)

        copyalltrackedgames = copy.deepcopy(alltrackedgames)
        print(alltrackedgames)
        for game in copyalltrackedgames:


            if int(game[1]) <= int(time.time()):
                #print("game added " + str(time.time()) + "    " + str(game[1])+" name: "+str(game[0]))
                #try:
                await checkgames(game[2])
                #except:
                #print("a error occurred")
                alltrackedgames.remove(game)


# name, next update time, data, user_id

client.run('disocrd_bot_api_key')
