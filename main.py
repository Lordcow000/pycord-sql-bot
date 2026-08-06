import discord
from dotenv import load_dotenv

import sqlite3
import csv
import os



load_dotenv()
DB_NAME = os.getenv('DATABASE_NAME')
if not DB_NAME:
    raise RuntimeError("DATABASE_NAME environment variable is not set")




# if os.path.exists(DB_NAME):
#     os.remove(DB_NAME)

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")
print(DB_NAME)


# region sql

def populate_tables():



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

    restaurant_table = """
    CREATE TABLE IF NOT EXISTS Restaurants(
        restaurant_id INTEGER PRIMARY KEY,
        restaurant_name TEXT NOT NULL,
        restaurant_address TEXT NOT NULL,
        restaurant_phone TEXT NOT NULL
    )
    """

    dish_table = """
    CREATE TABLE IF NOT EXISTS Dishes(
        dish_id INTEGER PRIMARY KEY,
        restaurant_id INTEGER NOT NULL,
        dish_name TEXT NOT NULL,
        dish_price FLOAT NOT NULL,

        FOREIGN KEY (restaurant_id) REFERENCES Restaurants (restaurant_id)
    )
    """

    orders_table = """
    CREATE TABLE IF NOT EXISTS Orders(
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        restaurant_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,

        FOREIGN KEY (customer_id) REFERENCES Customers (customer_id),
        FOREIGN KEY (restaurant_id) REFERENCES Restaurants (restaurant_id)
    )
    """

    orders_items = """
    CREATE TABLE IF NOT EXISTS OrdersItems(
        order_id INTEGER NOT NULL,
        dish_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price FLOAT NOT NULL,

        PRIMARY KEY (order_id, dish_id),

        FOREIGN KEY (order_id) REFERENCES Orders (order_id),
        FOREIGN KEY (dish_id) REFERENCES Dishes (dish_id)

    )
    """

    cursor.execute(customer_table)
    cursor.execute(restaurant_table)
    cursor.execute(dish_table)
    cursor.execute(orders_table)
    cursor.execute(orders_items)

    with open("csv's/mainData.csv", mode='r', newline='', encoding='utf-8') as file:
        dict_reader = csv.DictReader(file)
        rows = list(dict_reader)

        for row in rows:
            # region customers
            customer_values = (row['CustomerName'], row['CustomerEmail'], row['CustomerAddress'], row['Suburb'], row['PostCode'], row['CustomerPhone'])

            cursor.execute("SELECT customer_id FROM Customers WHERE customer_email = ?", (row['CustomerEmail'],))
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO Customers (customer_name, customer_email, customer_address, suburb, postcode, customer_phone) 
                    VALUES (?,?,?,?,?,?)
                    """,
                    customer_values,
                )
            # endregion

            # region restraunts
            restaurant_values = (row['RestaurantName'], row['RestaurantAddress'], row['RestaurantPhone'])

            cursor.execute("SELECT restaurant_id FROM Restaurants WHERE restaurant_name = ?", (row['RestaurantName'],))
            if cursor.fetchone() is None:
                cursor.execute(
                """
                INSERT INTO Restaurants (restaurant_name, restaurant_address, restaurant_phone) 
                VALUES (?,?,?)
                """,
                restaurant_values,
                )

            conn.commit()
            # endregion

            # region dishes
            cursor.execute("SELECT restaurant_id FROM Restaurants WHERE restaurant_name = ?", (row['RestaurantName'],))
            restaurant_id, = (cursor.fetchone())

            dish_values = (restaurant_id, row['DishName'], row['DishPrice'])

            cursor.execute("SELECT dish_id FROM Dishes WHERE dish_name = ? AND restaurant_id = ?", (row['DishName'],restaurant_id))
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO Dishes (restaurant_id, dish_name, dish_price)
                    VALUES (?, ?, ?)
                    """,
                    dish_values)
            conn.commit()
            # endregion 

        for row in rows:
            # region orders
            cursor.execute("SELECT customer_id FROM Customers WHERE customer_name = ?", (row['CustomerName'],))
            customer_id, = cursor.fetchone()

            cursor.execute("SELECT restaurant_id FROM Restaurants WHERE restaurant_name = ?", (row['RestaurantName'],))
            restaurant_id, = cursor.fetchone()        

            orders_values = (customer_id, restaurant_id, row['OrderDate'])

            cursor.execute(
                """
                INSERT INTO Orders (customer_id, restaurant_id, order_date)
                VALUES (?, ?, ?)
                """,
                orders_values)
            conn.commit()
            # endregion

            # region orders/items
            cursor.execute("SELECT order_id FROM Orders WHERE customer_id = ? AND restaurant_id = ? AND order_date = ?", (customer_id, restaurant_id, row['OrderDate'],))
            order_id, = cursor.fetchone()

            cursor.execute("SELECT dish_id FROM Dishes WHERE dish_name = ? AND restaurant_id = ?", (row['DishName'], restaurant_id,))
            dish_id, = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO OrdersItems (order_id, dish_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, dish_id, row['Quantity'], row['TotalAmount'],))
            # endregion
    conn.commit()


#populate_tables()



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

    embeds = embed_builder(headers, data)
    
    return embeds



def get_columns(ctx: discord.AutocompleteContext):

    table = ctx.options['table']
    cursor.execute(f"SELECT * FROM {table}")

    return [col[0] for col in cursor.description]

def get_queries(ctx: discord.AutocompleteContext):
   pass 

# endregion




# region built-in-queries
built_in_queries = {
    '1': 
        "SELECT * FROM Orders WHERE customer_id = 1",

    '2': """
        SELECT r.restaurant_name, d.dish_name 
        FROM Dishes d
        INNER JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        WHERE r.restaurant_id = 1
    """,

    '3': """
        SELECT c.customer_name, SUM(oi.unit_price) AS total_price
        FROM Customers c
        INNER JOIN Orders o ON c.customer_id = o.customer_id
        INNER JOIN OrdersItems oi ON o.order_id = oi.order_id
        GROUP BY c.customer_name
    """,

    '4': """
        SELECT c.customer_name, COUNT(o.order_id) AS total_orders
        FROM Customers c
        INNER JOIN Orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_name
    """,

    '5': """
        SELECT c.customer_name, COUNT(o.order_id) AS total_orders
        FROM Customers c
        INNER JOIN Orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_name
        HAVING total_orders > 30
    """,

    '6': """
        SELECT r.restaurant_name, d.dish_name
        FROM Dishes d
        INNER JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        ORDER BY r.restaurant_name
    """,

    '7': """
        SELECT d.dish_name, COUNT(oi.dish_id) AS total_orders
        FROM OrdersItems oi
        INNER JOIN Dishes d ON oi.dish_id = d.dish_id
        GROUP BY d.dish_name
        ORDER BY total_orders DESC
        LIMIT 1
    """,

    '8': """
        SELECT r.restaurant_name, AVG(d.dish_price) AS avg
        FROM Dishes d
        INNER JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        GROUP BY r.restaurant_name
    """,

    '9': """
        SELECT oi.order_id, d.dish_name, oi.quantity
        FROM OrdersItems oi
        INNER JOIN Dishes d ON oi.dish_id = d.dish_id
    """,

    '10': """
        SELECT r.restaurant_name, SUM(oi.unit_price) AS revenue
        FROM Restaurants r
        INNER JOIN Orders o ON r.restaurant_id = o.restaurant_id
        INNER JOIN OrdersItems oi ON o.order_id = oi.order_id
        GROUP BY r.restaurant_name
    """,

    '11': """
        SELECT CONCAT(customer_name, ': ', customer_email) AS CustomerContact
        FROM Customers
    """,

    '12': """
        SELECT d.dish_name, (d.dish_price * oi.quantity) AS CalculatedTotal
        FROM OrdersItems oi
        INNER JOIN Dishes d ON oi.dish_id = d.dish_id
        INNER JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        ORDER BY r.restaurant_id
    """,

    'custom': """
        SELECT d.dish_name, d.dish_id, (d.dish_price * SUM(oi.quantity)) AS CalculatedTotal
        FROM Dishes d
        INNER JOIN OrdersItems oi ON d.dish_id = oi.dish_id
        INNER JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
        GROUP BY d.dish_id
        ORDER BY r.restaurant_id
    """
}

# endregion


# region bot 
load_dotenv() 
bot = discord.Bot()

def embed_builder(headers, data):
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
            
        embeds.append(embed)
    
    return embeds

async def send_embeds(ctx, embeds):
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i + 10]
        await ctx.respond(embeds=chunk)

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
queries = [str(i) for i in range(1,13)]

print(queries)

@select_group.command()
async def all_(ctx:discord.ApplicationContext, table: str = discord.Option(choices=tables)): # type: ignore
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

@sub_select_group.command(description="Formated as: SELECT * FROM [table] WHERE [column] = [value]")
async def where(
    ctx, 
    table: discord.Option(str, choices=tables), # type: ignore
    column: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_columns)), # type: ignore
    value: str = discord.Option(), # type: ignore
    ): # type: ignore

    headers, data = select_where(table, f"{column} = '{value}'")
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

@bot.command(description="Execute a built-in query")
async def query(
    ctx, 
    query_number: discord.Option(str, choices=queries,), # type: ignore
    ): 
    
    embeds = custom_query(built_in_queries[query_number])
    await send_embeds(ctx, embeds)





@bot.command(description="Hi")
async def custom(ctx, query: str = discord.Option()): # type: ignore
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