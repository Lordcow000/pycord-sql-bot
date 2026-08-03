import discord
import os
from dotenv import load_dotenv

import sqlite3
import csv


DB_NAME = "db.db"

# region sql
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

test_table = """
    CREATE TABLE IF NOT EXISTS test(
        id INTEGER PTIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        year INTEGER NOT NULL,
        grade TEXT NOT NULL
    )
"""

customer_table = """
CREATE TABLE IF NOT EXISTS Customers(
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_address TEXT NOT NULL,
    suburb TEXT NOT NULL,
    postcode TEXT NOT NULL,
    customer_phone TEXT NOT NULL
)
"""






cursor.execute(test_table)
cursor.execute(customer_table)

with open('test.csv', mode='r', newline='', encoding='utf-8') as file:
    dict_reader = csv.DictReader(file)

    for row in dict_reader:
        values = (row['Id'], row['Name'], row['Year'], row['Grade'])
        cursor.execute("""
            INSERT INTO test (id, name, year, grade) 
            VALUES (?, ?, ?, ?) """,
            values)

with open('customers.csv', mode='r', newline='', encoding='utf-8') as file:
    dict_reader = csv.DictReader(file)

    for row in dict_reader:
        values = (row['CustomerId'], row['CustomerName'], row['CustomerEmail'], row['CustomerAddress'], row['Suburb'], row['PostCode'], row['CustomerPhone'])
        cursor.execute("""
            INSERT INTO Customers (customer_id, customer_name, customer_email, customer_address, suburb, postcode, customer_phone) 
            VALUES (?,?,?,?,?,?,?)""",
            values)


def get_info_for_embed(table_name):
    cursor.execute(f"SELECT * FROM {table_name}")

    data = cursor.fetchall()
    headers = [col[0] for col in cursor.description]

    return headers, data

def select_where(table_name, query):
    cursor.execute(f"SELECT * FROM {table_name} WHERE {query}")

    data = cursor.fetchall()
    headers = [col[0] for col in cursor.description]

    return headers, data

def custom_query(query):
    cursor.execute(f"{query}")
    data = cursor.fetchall()

    headers = [col[0] for col in cursor.description]
    
    return headers, data


conn.commit()
# endregion


# region bot 
load_dotenv() 
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.command(description= "Hi")
async def hello(ctx):
    headers, data = get_info_for_embed("Customers")
    # returns a list of dicts
    results = [dict(zip(headers, row)) for row in data]

    embeds = []

    for col in results:
        embed = discord.Embed(
                #title=f"Data",
                #description="Really longg descriptionnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",
                color=discord.Colour.blurple(),
            )
        for header in headers:
            embed.add_field(name=f"***{header}***", value=str(col[header]), inline=True)

        # embed.add_field(name="name", value=name, inline=True)
        # embed.add_field(name="year", value=year, inline=True)
        # embed.add_field(name="grade", value=grade, inline=True)


        embeds.append(embed)

    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i + 10]
        await ctx.send(embeds=chunk)

    #await ctx.respond("Hey!", embeds=embeds)


select_group = bot.create_group("select", "select stuff")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

@select_group.command()
async def all_(ctx:discord.ApplicationContext, table: str = discord.Option(choices=tables)):
    headers, data = get_info_for_embed(table)
    # returns a list of dicts
    results = [dict(zip(headers, row)) for row in data]
    
    embeds = []
    
    for col in results:
        embed = discord.Embed(colour=discord.Colour.blurple())

        for header in headers:
            embed.add_field(name=f"***{header}***", value=str(col[header]), inline=True)
        embeds.append(embed)
    
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i + 10]
        await ctx.send(embeds=chunk)

sub_select_group = select_group.create_subgroup("all")


@sub_select_group.command()
async def where(ctx, table: str = discord.Option(choices=tables), column: str = discord.Option(), value: str = discord.Option()):
    headers, data = select_where(table, f"{column} = {value}")
    # returns a list of dicts
    results = [dict(zip(headers, row)) for row in data]
    
    embeds = []
    
    for col in results:
        embed = discord.Embed(colour=discord.Colour.blurple())

        for header in headers:
            embed.add_field(name=f"***{header}***", value=str(col[header]), inline=True)
        embeds.append(embed)
    
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i + 10]
        await ctx.respond(embeds=chunk)




@bot.command(description="Hi")
async def custom(ctx, query: str = discord.Option()):
    headers, data = custom_query(query)
    # returns a list of dicts
    results = [dict(zip(headers, row)) for row in data]
    
    embeds = []
    
    for col in results:
        embed = discord.Embed(colour=discord.Colour.blurple())
    
        for header in headers:
            embed.add_field(name=f"***{header}***", value=str(col[header]), inline=True)
        embeds.append(embed)
    
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i + 10]
        await ctx.respond(embeds=chunk)

bot.run(os.getenv('TOKEN'))
# endregion