import json
import aiohttp
import nbt
import io
import base64
import requests


def decode_inventory_data(raw):
    data = nbt.nbt.NBTFile(fileobj=io.BytesIO(base64.b64decode(raw)))
    # print(data)
    return data

async def IGN2UUID(ign):  # takes the username of the player and returns the UUID
    try:

        uuidurl = f"https://api.mojang.com/users/profiles/minecraft/{ign}"

        async with aiohttp.ClientSession() as session:
            async with session.get(uuidurl) as resp:
                ans = await resp.json()
                return (ans['id'])
    except KeyError:
        return ign

async def UUID2IGN(uuid):
    try:
        url = f'https://api.mojang.com/user/profiles/{uuid}/names'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                ans = await resp.json()
                return (ans[len(ans) - 1]['name'])
    except KeyError:
        return uuid


async def canuse(user):  # Returns true if the user has the required perms to run the function
    with open("Roles_DB.json") as file:  # there's probably a better way to do this. TBD
        permlist = json.load(file)  # makes file into a dict
    RL = permlist.get(str(user.guild.id))
    for Grole in RL:
        for role in [i.id for i in user.roles]:
            if role == Grole:
                return True
    return False


async def getLowestBIN(name, data):  # Note, the only works for normal items. Does not work on enchanted books or pets
    lowest = None
    k = len(data)
    for i in range(k):
        for auction in data[i]:
            try:
                if name.upper() in auction["item_name"].upper() and auction["bin"] and \
                        (lowest is None or auction["starting_bid"] < lowest["starting_bid"]):
                    lowest = auction
            except KeyError:
                pass
    return (lowest)


async def getLowestBook(lore, data):
    lowest = None
    name = "ENCHANTED BOOK"
    k = len(data)
    for i in range(k):
        for auction in data[i]:
            try:
                if name in auction["item_name"].upper() and lore.upper() in auction["item_lore"].upper() and \
                        " " + lore.upper() not in auction["item_lore"].upper() \
                        and lore.upper() in auction["item_lore"].upper() \
                        and auction["bin"] \
                        and (lowest is None or auction["starting_bid"] < lowest["starting_bid"]):
                    lowest = auction
            except KeyError:
                pass
    return (lowest)


async def getLowestPet(name, rarity, data):
    lowest = None
    k = len(data)
    for i in range(k):
        for auction in data[i]:
            try:
                if (name.upper().replace(" ", "") in auction["item_name"].upper().replace(" ", "")
                        and "LVL" in auction["item_name"].upper()
                        and rarity.upper().replace(" ", "") in auction["tier"].upper().replace(" ", "")
                        and auction["bin"]
                        and (lowest is None or auction["starting_bid"] < lowest["starting_bid"])):
                    lowest = auction
            except KeyError:
                pass
    return (lowest)


async def getlowestMidas(name,price, data):
    lowest = None
    k = len(data)
    for i in range(k):
        for auction in data[i]:
            try:
                if name.upper() in auction["item_name"].upper() and auction["bin"]:
                    paid = decode_inventory_data(auction['item_bytes'])['i'][0]['tag']['ExtraAttributes']['winning_bid'].value
                    if lowest is None or auction["starting_bid"] < lowest["starting_bid"] and paid >= price:
                        lowest = auction
            except KeyError:
                pass
    return (lowest)


async def getbazaarprice(item):
    url = "https://api.hypixel.net/skyblock/bazaar?"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            db = await resp.json()
            return db['products'][item]["sell_summary"][0]['pricePerUnit']




def getbazaarprice(item):
  url="https://api.hypixel.net/skyblock/bazaar?"

  db=requests.get(f'{url}').json()['products']
  return(db[item]["sell_summary"][0]['pricePerUnit'])



def getpriceof(name,data):
    lowest="None on BIN"
    k=len(data)
    for i in range(k):
        for auction in data[i]:

            try:
                if(name.upper() in auction["item_name"].upper() and auction["bin"] and (lowest=="None on BIN" or auction["starting_bid"]<lowest )):
                    lowest=auction["starting_bid"]
            except KeyError:
                pass
    return(lowest)

def getpriceofbook(lore,data):
    lowest="None on BIN"
    name="ENCHANTED BOOK"
    k=len(data)
    for i in range(k):
        for auction in data[i]:
            try:
                if name in auction["item_name"].upper() and lore.upper() in auction["item_lore"].upper() and \
                        " " + lore.upper() not in auction["item_lore"].upper() \
                        and lore.upper() in auction["item_lore"].upper() \
                        and auction["bin"] \
                        and (lowest == "None on BIN" or auction["starting_bid"] < lowest):
                    lowest=auction["starting_bid"]
            except KeyError:
                pass
    return(lowest)
def getpriceofpet(name,rarity,data):
    lowest="None on BIN"
    k=len(data)
    for i in range(k):
        for auction in data[i]:
            try:
                if(name.upper().replace(" ","") in auction["item_name"].upper().replace(" ","")
                        and rarity.upper().replace(" ","") in auction["tier"].upper().replace(" ","")
                        and auction["bin"]
                        and (lowest == "None on BIN" or auction["starting_bid"] < lowest)
                        and not ("Upgrade Stone" in auction["item_name"])):
                    lowest=auction["starting_bid"]
            except KeyError:
                pass
    return(lowest)