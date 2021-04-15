import discord
from discord.ext import commands, tasks
from Supporting_Module import *
from time import perf_counter
from datetime import datetime

with open("Important_stuff.json") as f:  # opens up the json file with the bot key and API key
    data = json.load(f)  # converts from JSON to a dict object
    bot_key = data.get("Bot Key")
    api_key = data.get("API Key")

Global_Database = []
bot = commands.Bot(command_prefix='da!')
bot.remove_command('help')



@tasks.loop(minutes=5)
async def updateDB():
    try:
        await bot.wait_until_ready()  # waits until the bot is on
        game = discord.Game(
            f"with {sum([i.member_count for i in bot.guilds])} discord users on {len(bot.guilds)} different servers")
        await bot.change_presence(status=discord.Status.online, activity=game)
        global Global_Database
        Global_Database.clear()  # clears the old database
        t = perf_counter()  # starts a timer
        url = 'https://api.hypixel.net/skyblock/auctions?page=1'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                pages = await resp.json()  # This whole section pulls how many pages of data there are
                if (pages['success'] == True):
                    pages = pages['totalPages']
        for i in range(pages):
            url = f'https://api.hypixel.net/skyblock/auctions?page={i}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:  # Grabs all the auction data
                    pages = await resp.json()
                    Global_Database.append(pages['auctions'])
                    # NOTE you could make a specific search faster by filtering off non BINS first
                    # This could also (probably) be multi processed if you know how to do that
        print(f"Finished in {perf_counter() - t} seconds")
    except:
        pass


@bot.event
async def on_ready():
    #The following code is here just to create a base json file where all current servers are stored
    permlist=dict()
    for guild in bot.guilds:
        permlist.update({guild.id:[guild.default_role.id]})
    with open("Roles_DB.json",'w') as f:
        json.dump(permlist, f, indent=3)
    print("Ready")


@bot.event
async def on_guild_join(guild):
    with open("Roles_DB.json") as file:  # there's probably a better way to do this. TBD
        permlist = json.load(file)  # makes file into a dict
    try:
        with open("Roles_DB.json", 'w') as file:
            permlist.update({guild.id: [guild.default_role.id]})  # adds the new guild to the permlist
            json.dump(permlist, file, indent=3)  # dumps the whole permlist into the file deleting the previous one
        print(f'{guild.name} has added Sirius')
    except KeyError:
        with open("Roles_DB.json", 'w') as file:
            json.dump(permlist, file, indent=3)  # dumps the whole permlist into the file deleting the previous one
        print(f'{guild.name} has added Sirius')


@bot.event
async def on_guild_remove(guild):
    with open("Roles_DB.json") as file:  # there's probably a better way to do this. TBD
        permlist = json.load(file)  # makes file into a dict
    with open("Roles_DB.json", 'w') as file:
        permlist.pop(str(guild.id))  # adds the new guild to the permlist
        json.dump(permlist, file, indent=3)  # dumps the whole permlist into the file deleting the previous one
        print(f'{guild.name} has removed Sirius')


@bot.command()
async def help(ctx, cmd=None):
    if (not cmd):
        embed = discord.Embed(
            title="Sirius bot commands, for more details on a specific command, type DA!help (command name)",
            description="General commands\n``prices``, ``priceof``, ``bitprofit``, ``auctions``,``support``. ``bazaar``,``floor``\n Administrator commands\n ``setroles``, ``clearroles``",
            colour=discord.Colour.dark_gold()
        )
        await ctx.send(embed=embed)
    else:
        command = bot.get_command(name=cmd)
        embed = discord.Embed(
            title=cmd,
            description=command.help,
            colour=discord.Colour.blurple()
        )
        await ctx.send(embed=embed)

@bot.command(help="Sets roles which can access the bot \nExamples\n da!setroles @role1 @role1 @role3 ... ")
@commands.has_permissions(administrator=True)
async def setroles(ctx, *args: discord.Role):
    # print(ctx.guild.id)
    ids = [i.id for i in args]  # makes the list of discord roles into a list a discord role IDs
    with open("Roles_DB.json") as file:  # Opens the JSON file
        permlist = json.load(file)  # makes file into a dict
        permlist.update({str(ctx.guild.id): ids})  # changes the perms of the server to the new ones
    with open('Roles_DB.json', 'w') as f:
        json.dump(permlist, f, indent=3)  # updates the JSON file
    await ctx.send(f"Roles updated!\n"
                   f"Now only user with these roles can use commands\n"
                   f"`{['@' + i.name for i in args]}`")  # sends a kind message


@bot.command(help="Resets all roles so that anyone can access the command\nExamples\n da!clearroles ")
@commands.has_permissions(administrator=True)
async def clearroles(ctx):
    print(ctx.guild.id)
    with open("Roles_DB.json") as file:  # Opens the JSON file
        permlist = json.load(file)  # makes file into a dict
        permlist.update(
            {str(ctx.guild.id): [ctx.guild.default_role.id]})  # changes the perms of the server to the new ones
    with open('Roles_DB.json', 'w') as f:
        json.dump(permlist, f, indent=3)  # updates the JSON file
    await ctx.send(f"Roles updated!\n"
                   f"Now all users can use commands\n")


@bot.command(help="Returns the lowest BIN price of whatever item is requested\n Here is how to input the item type\n"
                  "``da!priceof aspect of the end``\n``da!priceof sharpness VI`` \n``da!priceof tiger : legendary``")
async def priceof(ctx, *args):
    if await canuse(ctx.author):
        args = " ".join(args)
        print(args)
        auction = await getLowestBook(args, Global_Database)  # tries to see if this is a book

        if auction is None and ":" in args:  # if its not a book, check if its pet
            args2 = args.split(":")
            print(args2)
            auction = await getLowestPet(args2[0].strip(), args2[1].strip(), Global_Database)

        if auction is None:  # if its not a pet, its a normal item
            auction = await getLowestBIN(args, Global_Database)
        print(auction)
        if auction is None:  # in this case, there are no items on the auction house of this kind
            await ctx.send(f'There are no {args} up for sale atm')
            return
        name = await UUID2IGN(auction['auctioneer'])
        embed = discord.Embed(
            title=f"The lowest priced {args} is {auction['starting_bid']:,d}",
            description=f"Seller: `{name}`\n",
            colour=discord.Colour.gold()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("Sorry! You don't have access to this bot.\n"
                       "If you dont feel this is correct, contact the owner of the server")


@bot.command(aliases=["price"], help="Returns all the prices for DA items")
async def prices(ctx):
    if await canuse(ctx.author):
        swords = ["Midas' sword", "Midas staff", ]
        swordemotes = ['<:midas_sword:809084375152590880>', "<:Golden_Shovel:769366749308256317>", ]
        prices = [50_000_000, 100_000_000]
        itemprices = ""
        for i, sword in enumerate(swords):
            auction = await getlowestMidas(sword, prices[i], Global_Database)
            if auction is None:
                itemprices += f'{swordemotes[i]} {sword}: {"None on BIN"} \n'
            else:
                itemprices += f'{swordemotes[i]} {sword}: {auction["starting_bid"]:,d} \n'
        items = ["Spirit Mask", "Ender Artifact", "Wither Artifact",
                 "Travel Scroll to Dark Auction", "Hegemony Artifact", "Plasma Nucleus"]
        emotes = ['<:Spirit_Mask:809082742310436922>',
                  '<:enderartifact:809081452129943602>', '<:Wither_Artifact:809081451726372886>',
                  '<:Empty_Map:809083118782644225>', "<:Hegemony_Artifact:769365767027163146>",
                  "<:Plasma_Nucleus:769367279044526100>"]

        for i, item in enumerate(items):
            auction = await getLowestBIN(item, Global_Database)
            if auction is None:
                itemprices += f'{emotes[i]} {item}: {"None on BIN"} \n'
            else:
                itemprices += f'{emotes[i]} {item}: {auction["starting_bid"]:,d} \n'

        books = ["Sharpness VI", "Sharpness VII", "Giant Killer VI", "Giant Killer VII", "Power VI", "Power VII",
                 "Growth VI", "Growth VII",
                 "Protection VI", "Protection VII",
                 "Counter-Strike V", "Vicious V", "Big Brain III"]
        bookemote = '<:Enchanted_Book:809081448371191818>'
        bookprices = ""
        for i, book in enumerate(books):
            auction = await getLowestBook(book, Global_Database)
            if auction is None:
                bookprices += f'{bookemote} {book}: {"None on BIN"} \n'
            else:
                bookprices += f'{bookemote} {book}: {auction["starting_bid"]:,d} \n'

        pets = ["Parrot Epic", "Parrot Legendary", "Turtle Epic", "Turtle Legendary", "Jellyfish Epic",
                "Jellyfish Legendary"]
        petemotes = ["<:epic_parrot:809081452083937371>", "<:legendary_parrot:809081452163235861>",
                     "<:epic_turtle:809081452116705370>", "<:legendary_turtle:809081452095340564>",
                     "<:epic_jellyfish:809081451805933609>", "<:legendary_jellyfish:809081451936743434>"]
        petprices = ""
        for i, pet in enumerate(pets):
            pet = pet.split(" ")
            auction = await getLowestPet(pet[0], pet[1], Global_Database)
            if auction is None:
                petprices += f'{petemotes[i]} {pet[0]}: {"None on BIN"} \n'
            else:
                petprices += f'{petemotes[i]} {pet[0]}: {auction["starting_bid"]:,d} \n'
        embed = discord.Embed(
            title="These are the lowest BINS of all the DA items",
            colour=discord.Colour.blue()
        )
        embed.add_field(name="Items:", value=itemprices, inline=True)
        embed.add_field(name="Pets:", value=petprices, inline=True)
        embed.add_field(name="Books:", value=bookprices, inline=False)
        embed.timestamp=datetime.now()
        embed.set_footer(
            text="The following bot was made by Mattynmax\nTo support the development of the bot, consider donating\n https://ko-fi.com/dabot")
        await ctx.send(embed=embed)


@bot.command(help= "Calculates the coins/bit ratio for every item")
async def bitprofit(ctx):
    if await canuse(ctx.author):
        items = {"God Potion": 1500, "Kat Flower": 500, "Heat Core": 3000, "Hyper Catalyst Upgrade": 300,
                 "Ultimate Carrot Candy Upgrade": 8000, "Colossal Experience Bottle Upgrade": 1200,
                 "Jumbo Backpack Upgrade": 4000,
                 "Minion Storage X-pender": 1500, "Hologram": 2000, "Dungeon sack": 10000,
                 "Builder's Wand": 12000, "Bits Talisman": 15000, 'Block Zapper': 5000, "Rune Sack": 10000,
                 "Autopet Rules 2-Pack": 21000, "Kismet Feather": 1350}
        B2CratioI = []
        l = []
        for item in items:
            l.append(item)
            price = await getLowestBIN(item, Global_Database)
            if (type(price) is not dict):
                B2CratioI.append(0)
            else:
                B2CratioI.append(int(price['starting_bid'] / items.get(item)))
        s = ''
        for i in range(len(l)):
            s += f"{l[i]}: {B2CratioI[i]}\n"

        Enrichments = {"Speed enrichment": 5000,
                       "Intelligence enrichment": 5000, "Critical damage enrichment": 5000,
                       "Critical chance enrichment": 5000, "Strength enrichment": 5000, "Defence enrichment": 5000,
                       "Health enrichment": 5000, "Magic find enrichment": 5000, "Accessory enrichment swapper": 200}
        B2CratioE = []
        e = []
        for Enrichment in Enrichments:
            e.append(Enrichment)
            price = await getLowestBIN(Enrichment, Global_Database)
            if (type(price) is not dict):
                B2CratioE.append(0)
            else:
                B2CratioE.append(int(price['starting_bid'] / Enrichments.get(Enrichment)))
        ER = ''
        for i in range(len(e)):
            ER += f"{e[i]}: {B2CratioE[i]}\n"

        embed = discord.Embed(
            title="This is the amount of coins per bit based on the lowest BINS for each item",
            colour=discord.Colour.blurple()
        )
        try:
            b1 = await getLowestBook('Expertise', Global_Database)
            b1 = b1['starting_bid']
        except:
            b1 = 0
        try:
            b2 = await getLowestBook('Compact', Global_Database)
            b2 = b2['starting_bid']
        except TypeError:
            b2 = 0
        try:
            b3 = await getLowestBook('Cultivating', Global_Database)
            b3 = b3['starting_bid']
        except TypeError:
            b3 = 0
        embed.add_field(name="General items", value=s, inline=True)
        embed.add_field(name="Enrichments", value=ER, inline=True)
        embed.add_field(name="Books", value=f"Expertise: {int(b1 / 4000)}"
                                            f"\nCompact: {int(b2 / 4000)}"
                                            f"\nCultivating: {int(b3 / 4000)}", inline=False)
        embed.timestamp=datetime.now()
        embed.set_footer(
            text="The following bot was made by Mattynmax\nTo support the development of the bot, consider donating\n https://ko-fi.com/dabot")
        await ctx.send(embed=embed)
    else:
        await ctx.send("Sorry! You don't have access to this bot.\n"
                       "If you dont feel this is correct, contact the owner of the server")


@bot.command(aliases=['ah','auction'],help= "given a minecraft ign, tells you all the individuals auctions and current price" )
async def auctions(ctx, name=None):
    if await canuse(ctx.author):
        embed = discord.Embed(
            title=f"{name}'s auctions",
            colour=discord.Colour.dark_purple()
        )
        if (name == None):
            await ctx.send("Please include an IGN for this command to work\n ex: ``da!auctions mattynmax``")
            return

        try:
            name = await IGN2UUID(name)
            # print(name)
        except Exception as t:
            # print(t)
            await ctx.send("This player has no active auctions")  # if the player doesent exist
            return
        auctions = []

        url = f"https://api.hypixel.net/skyblock/auction?key=73e158d5-a27c-4fb9-bb49-ba2196af5fe8&player={name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                Tauctions = await resp.json()
        Tauctions = Tauctions["auctions"]

        for auction in Tauctions:
            if (datetime.fromtimestamp(auction['end'] // 1000.0) > datetime.now()):
                try:
                    t = auction['bin']
                    embed.add_field(name=auction["item_name"],
                                    value=f"BIN price: {auction['starting_bid']:,d}\n{auction['tier']}")
                    auctions.append(auction)
                except KeyError as p:
                    # print(p)
                    if (auction['highest_bid_amount'] == 0):
                        embed.add_field(name=auction["item_name"],
                                        value=f"Current price: {auction['starting_bid']:,d}\n{auction['tier']}")
                    else:
                        embed.add_field(name=auction["item_name"],
                                        value=f"Current price: {auction['highest_bid_amount']:,d}\n{auction['tier']}")
                    auctions.append(auction)
        if not auctions:
            await ctx.send("This player has no active auctions")
        else:
            await ctx.send(embed=embed)
        return

@bot.command(alises=["bz"], help="Return the current buy and sell offers for an item\nExamples:\n`da!bazaar enchanted redstone`"
                                 "\n`da!bazaar recombobulator 3000`")
async def bazaar(ctx, *item):
    if await canuse(ctx.author):
        if item == ():
            await ctx.send("Invalid command, no item name given\n `da!bazaar (item name)`")
            return
        sitem = "_".join([i.upper() for i in item])
        url = "https://api.hypixel.net/skyblock/bazaar"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                t = await resp.json()
        try:
            data = t['products'][sitem]['quick_status']
            embed = discord.Embed(
                title=f"Information about {' '.join(item)}",
                colour=discord.Colour.blurple()
            )
            embed.add_field(name="Sell price", value=round(data['sellPrice'], 1))
            embed.add_field(name="Buy price", value=round(data['buyPrice'], 1))
            await ctx.send(embed=embed)
        except KeyError:
            await ctx.send("This item does not exist, check for typos and try again")


@bot.command(help="Returns some information about the bot developer")
async def support(ctx):
    embed = discord.Embed(
        title="Bot support",
        description="If you are still having troubles with the bot after looking at da!help, please join the support server https://discord.gg/E8uMswC or try contacting me in game at mattynmax\n\n"
                    "If you would like to support the development of this bot. Consider donating https://ko-fi.com/dabot\n\n"
                    "If you would like to watch the development of this bot in real time, consider following/subbing to me on twitch https://twitch.tv/mattynmax",
        colour=discord.Colour.purple()
    )
    await ctx.send(embed=embed)


@bot.command(help= "Returns the lowest BIN/Bazaar price for all chests for that Floor\nFormat: `da!floor (floor number)`")
async def floor(ctx, Efloor=None):
    if await canuse(ctx.author):
        if(not Efloor):
            await ctx.send("Error: No floor provided `da!floor (floor number)`")
        elif int(Efloor) == 1:
            Nb=format(getpriceof("Necromancer's Brooch", Global_Database), ",d")
            Bs=format(getpriceof("Bonzo's Staff", Global_Database), ",d")
            Bm = format(getpriceof("Bonzo's mask", Global_Database), ",d")
            embed=discord.Embed(title= f"Floor {Efloor} prices",
                                description=
                                f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                f"Necromancer's Brooch : {Nb}\n"
                                f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                f'No Pain No Gain I : {getpriceofbook("No Pain No Gain I", Global_Database):,d}\n'
                                f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                f'Red Nose: {getpriceof("Red Nose", Global_Database)}\n'
                                f'Bonzo Staff : {Bs}\n'
                                f'Bonzo Mask : {Bm}\n'
                                f'Fuming Potato Book : {int(getbazaarprice("FUMING_POTATO_BOOK")):,d}\n'
                                f'Recombobulator 3000 : {int(getbazaarprice("RECOMBOBULATOR_3000")):,d}'
                                , colour=discord.Colour.red()
                                )
            await ctx.send(embed=embed)
        elif int(Efloor) == 2:
            Ss = format(getpriceof("Scarf's Studies", Global_Database), ",d")
            embed=discord.Embed(title= f"Floor {Efloor} prices",
                                description=
                                f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                f'Ultimate Wise I : {getpriceofbook("Ultimate Wise I", Global_Database):,d}\n'
                                f'Ultimate Jerry I {getpriceofbook("Ultimate Jerry I", Global_Database):,d}\n'
                                f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                f'Combo I : {getpriceofbook("Combo I", Global_Database):,d}\n'
                                f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                f'Scarfs Studies : {Ss}\n'
                                f'Adaptive Blade : {getpriceof("Adaptive Blade",Global_Database):,d}\n'
                                f'Fuming Potato Book : {int(getbazaarprice("FUMING_POTATO_BOOK")):,d}\n'
                                f'Recombobulator 3000 : {int(getbazaarprice("RECOMBOBULATOR_3000")):,d}'
                                , colour=discord.Colour.red()
                                )
            await ctx.send(embed=embed)
        elif int(Efloor) == 3:
            embed=discord.Embed(title= f"Floor {Efloor} prices",
                                description=
                                f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                f'Ultimate Wise I : {getpriceofbook("Ultimate Wise I", Global_Database):,d}\n'
                                f'Wisdom I : {getpriceofbook("Wisdom I", Global_Database):,d}\n'
                                f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                f'Combo I : {getpriceofbook("Combo I", Global_Database):,d}\n'
                                f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                f'Adaptive Helm : {getpriceof("Adaptive Helm",Global_Database):,d}\n'
                                f'Adaptive Chestplate : {getpriceof("Adaptive Chestplate",Global_Database):,d}\n'
                                f'Adaptive Leggings : {getpriceof("Adaptive Leggings",Global_Database):,d}\n'
                                f'Adaptive Boots : {getpriceof("Adaptive Boots",Global_Database):,d}\n'
                                f'Adaptive Blade : {getpriceof("Adaptive Blade",Global_Database):,d}\n'
                                f'Fuming Potato Book : {int(getbazaarprice("FUMING_POTATO_BOOK")):,d}\n'
                                f'Recombobulator 3000 : {int(getbazaarprice("RECOMBOBULATOR_3000")):,d}'
                                , colour=discord.Colour.red()
                                )
            await ctx.send(embed=embed)
        elif int(Efloor) == 4:
            embed = discord.Embed(title=f"Floor {Efloor} prices",
                                  description=
                                  f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                  f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                  f'Ultimate Wise I : {getpriceofbook("Ultimate Wise I", Global_Database):,d}\n'
                                  f'Wisdom I : {getpriceofbook("Wisdom I", Global_Database):,d}\n'
                                  f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                  f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                  f'Combo I : {getpriceofbook("Combo I", Global_Database):,d}\n'
                                  f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                  f'Spirit Pet (Epic) : {getpriceofpet("Spirit","EPIC", Global_Database):,d}\n'
                                  f'Spirit Pet (Leg) : {getpriceofpet("Spirit","LEGENDARY", Global_Database):,d}\n'
                                  f'Spirit Bone : {getpriceof("Spirit Bone", Global_Database):,d}\n'
                                  f'Spirit Boots : {getpriceof("Spirit Boots", Global_Database):,d}\n'
                                  f'Spirit Wing : {getpriceof("Spirit Wing", Global_Database):,d}\n'
                                  f'Fuming Potato Book : {int(getbazaarprice("FUMING_POTATO_BOOK")):,d}\n'
                                  f'Recombobulator 3000 : {int(getbazaarprice("RECOMBOBULATOR_3000")):,d}'
                                  , colour=discord.Colour.red()
                                  )
            await ctx.send(embed=embed)
        elif int(Efloor) == 5:
            embed = discord.Embed(title=f"Floor {Efloor} prices",
                                  description=
                                  f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                  f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                  f'Lethality VI : {getpriceofbook("Lethality VI", Global_Database):,d}\n'
                                  f'Ultimate Wise I : {getpriceofbook("Ultimate Wise I", Global_Database):,d}\n'
                                  f'Wisdom I : {getpriceofbook("Wisdom I", Global_Database):,d}\n'
                                  f'Legion I :{getpriceofbook("Legion I",Global_Database):,d}\n'
                                  f'Overload I :{getpriceofbook("Overload I",Global_Database):,d}\n'
                                  f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                  f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                  f'Combo I : {getpriceofbook("Combo I", Global_Database):,d}\n'
                                  f'Last Stand I : {getpriceofbook("Last Stand I", Global_Database):,d}\n'
                                  f'No Pain No Gain I : {getpriceofbook("No Pain No Gain I", Global_Database):,d}\n'
                                  f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                  f'Shadow Assassin Helmet : {getpriceof("Shadow Assassin Helmet", Global_Database):,d}\n'
                                  f'Shadow Assassin Chestplate : {getpriceof("Shadow Assassin Chestplate", Global_Database):,d}\n'
                                  f'Shadow Assassin Leggings : {getpriceof("Shadow Assassin Leggings", Global_Database):,d}\n'
                                  f'Shadow Assassin Boots : {getpriceof("Shadow Assassin Boots", Global_Database):,d}\n'
                                  f'Warped Stone : {getpriceof("Warped Stone", Global_Database):,d}\n'
                                  f'Dark Orb : {getpriceof("Dark Orb", Global_Database):,d}\n'
                                  f'Last Breath : {getpriceof("Last Breath", Global_Database):,d}\n'
                                  f'Livid Dagger : {getpriceof("Livid Dagger", Global_Database):,d}\n'
                                  f'Fuming Potato Book : {int(getbazaarprice("FUMING_POTATO_BOOK")):,d}\n'
                                  f'Recombobulator 3000 : {int(getbazaarprice("RECOMBOBULATOR_3000")):,d}'
                                  , colour=discord.Colour.red()
                                  )
            await ctx.send(embed=embed)
        elif int(Efloor) == 6:
            Ss = format(getpriceof("Sadan's Brooch", Global_Database), ",d")
            gs = format(getpriceof("Giant's Sword", Global_Database), ",d")
            embed = discord.Embed(title=f"Floor {Efloor} prices",
                                  description=
                                  f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                  f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                  f'Lethality VI : {getpriceofbook("Lethality VI", Global_Database):,d}\n'
                                  f'Swarm I : {getpriceofbook("Swarm I", Global_Database):,d}\n'
                                  f'Ultimate Wise I : {getpriceofbook("Ultimate Wise I", Global_Database):,d}\n'
                                  f'Wisdom I : {getpriceofbook("Wisdom I", Global_Database):,d}\n'
                                  f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                  f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                  f'Combo I : {getpriceofbook("Combo I", Global_Database):,d}\n'
                                  f'No Pain No Gain I : {getpriceofbook("No Pain No Gain I", Global_Database):,d}\n'
                                  f'Legion I :{getpriceofbook("Legion I", Global_Database):,d}\n'
                                  f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                  f'Precursor Eye : {getpriceof("Precursor Eye", Global_Database):,d}\n'
                                  f'Necromancer Lord Helmet : {getpriceof("Necromancer Lord Helmet", Global_Database):,d}\n'
                                  f'Necromancer Lord Chestplate : {getpriceof("Necromancer Lord Chestplate", Global_Database):,d}\n'
                                  f'Necromancer Lord Leggings : {getpriceof("Necromancer Lord Leggings", Global_Database):,d}\n'
                                  f'Necromancer LordBoots : {getpriceof("Necromancer Lord Boots", Global_Database):,d}\n'
                                  f'Giant Tooth : {getpriceof("Giant Tooth", Global_Database):,d}\n'
                                  f'Sadans Brooch : {Ss}\n'
                                  f'Giants Sword: {gs}\n'
                                  f'Necromancer Sword: {getpriceof("Necromancer Sword", Global_Database):,d}\n'
                                  f'Ancient Rose: {getpriceof("Ancient Rose", Global_Database):,d}\n'
                                  f'Summoning Ring: {getpriceof("Summoning Ring", Global_Database):,d}\n'
                                  f'Fuming Potato Book : {int(getbazaarprice("FUMING_POTATO_BOOK")):,d}\n'
                                  f'Recombobulator 3000 : {int(getbazaarprice("RECOMBOBULATOR_3000")):,d}'
                                  , colour=discord.Colour.red()
                                  )
            await ctx.send(embed=embed)
        elif int(Efloor) == 7:
            Nh = format(getpriceof("necron's handle", Global_Database), ",d")
            embed = discord.Embed(title=f"Floor {Efloor} prices",
                                  description=
                                  f'Infinite Quiver VI : {getpriceofbook("Infinite Quiver VI", Global_Database):,d}\n'
                                  f'Feather Falling VI : {getpriceofbook("Feather Falling VI", Global_Database):,d}\n'
                                  f'Soul Eater I : {getpriceofbook("Soul Eater I", Global_Database):,d}\n'
                                  f'One For All I : {getpriceofbook("One For All I", Global_Database):,d}\n'
                                  f'Lethality VI : {getpriceofbook("Lethality VI", Global_Database):,d}\n'
                                  f'Swarm I : {getpriceofbook("Swarm I",Global_Database):,d}\n'
                                  f'Ultimate Wise I : {getpriceofbook("Ultimate Wise I", Global_Database):,d}\n'
                                  f'Wisdom I : {getpriceofbook("Wisdom I", Global_Database):,d}\n'
                                  f'Rejuvenate I {getpriceofbook("Rejuvenate I", Global_Database):,d}\n'
                                  f'Bank I : {getpriceofbook("Bank I", Global_Database):,d}\n'
                                  f'Combo I : {getpriceofbook("Combo I", Global_Database):,d}\n'
                                  f'No Pain No Gain I : {getpriceofbook("No Pain No Gain I", Global_Database):,d}\n'
                                  f'Legion I :{getpriceofbook("Legion I",Global_Database):,d}\n'
                                  f'Hot Potato Book : {int(getbazaarprice("HOT_POTATO_BOOK")):,d}\n'
                                  f'Precursor Gear : {getpriceof("Precursor Gear", Global_Database):,d}\n'
                                  f'Wither Blood : {getpriceof("Wither Blood", Global_Database):,d}\n'
                                  f'Wither Helmet : {getpriceof("Wither Helmet", Global_Database):,d}\n'
                                  f'Wither Chestplate : {getpriceof("Wither Chestplate", Global_Database):,d}\n'
                                  f'Wither Leggings : {getpriceof("Wither Leggings", Global_Database):,d}\n'
                                  f'Wither Boots : {getpriceof("Wither Boots", Global_Database):,d}\n'
                                  f'Wither Shield: {getpriceof("Wither Shield", Global_Database):,d}\n'
                                  f'Implosion: {getpriceof("implosion", Global_Database):,d}\n'
                                  f'Shadow Warp: {getpriceof("Shadow Warp", Global_Database):,d}\n'
                                  f'Auto Recomboulator: {getpriceof("Auto Recombobulator", Global_Database):,d}\n'
                                  f'Wither Catalyst: {getpriceof("Wither Catalyst", Global_Database):,d}\n'
                                  f'Necrons Handle: {Nh}\n'
                                  , colour=discord.Colour.red()
                                  )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Sorry! This floor has not been added yet. Check back later")


updateDB.start()

bot.run(bot_key)
