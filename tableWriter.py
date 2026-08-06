import csv
import os
import sqlite3

def populate_tables(DB_NAME):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    cursor.execute("PRAGMA foreign_keys = ON")


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

            print(orders_values)
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

    conn.commit()

    print('Tables created and filled')
    cursor.close()
    conn.close()
    