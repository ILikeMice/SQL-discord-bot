import discord
import json
from discord.ext import commands
import os
from discord import app_commands
import mysql.connector
import mysql.connector.cursor  

def readdata():
    with open("data.json", "r") as infile:
        data = json.load(infile)
    return data

def writedata(data):
    with open("data.json", "w") as outfile:
        json.dump(data, outfile, indent=3)


BOT_TOKEN = "token"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.tree.command(name="adddatabase", description="Add a database to the bot")
async def adddatabase(interaction: discord.Interaction, name: str, hosturl: str, user: str, password: str):
    uid = str(interaction.user.id)
    data = readdata()
    if uid not in data["Users"]:
        data["Users"][uid] = {}
        print(data["Users"])
    data["Users"][uid][name] = {
                                "tables": [],
                                "host": hosturl,
                                "user": user,
                                "password": password
                                }
    try: 
        
        db = mysql.connector.connect(host=hosturl, user=user, password=password)
        cursor = db.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS " + name)
        writedata(data)
        await interaction.response.send_message(f"Added database {name} to the bot")
    except Exception as e:
        await interaction.response.send_message(f"Failed to add database {name} to the bot: {e}")
    
    

async def type_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    types = ["VARCHAR", "TEXT", "DATE", "INT"]
    return [
        app_commands.Choice(name=columntype, value=columntype)
        for columntype in types if current.lower() in columntype.lower()
    ]




@bot.tree.command(name="addtable", description="Add a table to a database (you need to add a column, add more columns using /addcolumn)")
@app_commands.autocomplete(columntype=type_autocomplete)
async def addtable(interaction: discord.Interaction, dbname: str, tablename: str, columnname: str, columntype: str, length: int):
    uid = str(interaction.user.id)
    data = readdata()
    if data["Users"][uid][dbname] == None:
        await interaction.response.send_message(f"Database {dbname} does not exist")
        return
    host = data["Users"][uid][dbname]["host"]
    user = data["Users"][uid][dbname]["user"]
    password = data["Users"][uid][dbname]["password"]
    print(host,user,password)
    try:
        db = mysql.connector.connect(host=host, user=user, password=password)
        cursor = db.cursor()
        cursor.execute("USE " + dbname)
        print("CREATE TABLE IF NOT EXISTS " + tablename + " (" + columnname +" " + columntype + ")")
        cursor.execute("CREATE TABLE IF NOT EXISTS " + tablename + " (" + columnname +" " + columntype + f"({length})" + ")")
        cursor.execute("SHOW TABLES")
        for table in cursor:
            if not table in data["Users"][uid][dbname]["tables"]:
                data["Users"][uid][dbname]["tables"].append(table)
        writedata(data)
        await interaction.response.send_message(f"Added table {tablename} to database {dbname}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to connect to database {dbname}: {e}", ephemeral=True)


@bot.tree.command(name="addcolumn", description="Add a column to a table in a database")
@app_commands.autocomplete(columntype=type_autocomplete)
async def addcolumn(interaction: discord.Interaction, dbname: str, tablename: str, columnname: str, columntype: str, length: int):
    uid = str(interaction.user.id)
    data = readdata()
    if dbname not in data["Users"][uid]:
        await interaction.response.send_message(f"Database {dbname} does not exist")
        return
    if not tablename in data["Users"][uid][dbname]["tables"]:
        await interaction.response.send_message(f"Table {tablename} does not exist in database {dbname}")
        return
    host = data["Users"][uid][dbname]["host"]
    user = data["Users"][uid][dbname]["user"]
    password = data["Users"][uid][dbname]["password"]
    try:
        db = mysql.connector.connect(host=host, user=user, password=password)
        cursor = db.cursor()
        cursor.execute("USE " + dbname)
        cursor.execute("ALTER TABLE " + tablename + " ADD " + columnname + " " + columntype + f"({length})")
        await interaction.response.send_message(f"Added column {columnname} to table {tablename} in database {dbname}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error executing command with database {dbname}: {e}", ephemeral=True)



@bot.tree.command(name="addrow", description="Add a row to a table in a database")
async def addrow(interaction: discord.Interaction, dbname: str, tablename: str, values: str):
    uid = str(interaction.user.id)
    data = readdata()
    if dbname not in data["Users"][uid]:
        await interaction.response.send_message(f"Database {dbname} does not exist")
        return
    if not tablename in data["Users"][uid][dbname]["tables"]:
        await interaction.response.send_message(f"Table {tablename} does not exist in database {dbname}")
        return
    host = data["Users"][uid][dbname]["host"]
    user = data["Users"][uid][dbname]["user"]
    password = data["Users"][uid][dbname]["password"]
    try:
        db = mysql.connector.connect(host=host, user=user, password=password)
        cursor = db.cursor()
        cursor.execute("USE " + dbname)
        cursor.execute("DESCRIBE " + tablename)
        thing = [i[0] for i in cursor.fetchall()]
        thing = str(thing).replace("'", "").replace("[", "").replace("]", "")
        values = '"' + values.replace(",", '","') + '"'
        print("INSERT INTO " + tablename + " (" + thing + ")" " VALUES (" + values + ")")
        cursor.execute("INSERT INTO " + tablename + " (" + thing + ")" " VALUES (" + values + ")")
        db.commit()
        await interaction.response.send_message(f"Added row to table {tablename} in database {dbname}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error executing command with database {dbname}: {e}", ephemeral=True)





@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

bot.run(BOT_TOKEN)
