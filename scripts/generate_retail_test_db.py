import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


random.seed(20260902)
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "retail_operations_test.sqlite"

FIRST_NAMES = ["Aarav", "Aditi", "Arjun", "Diya", "Ishaan", "Kavya", "Meera", "Neha", "Rohan", "Saanvi", "Vikram", "Zoya"]
LAST_NAMES = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Nair", "Mehta", "Joshi", "Das"]
CITIES = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata", "Jaipur"]


def rows(count, factory):
    return [factory(index) for index in range(1, count + 1)]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    connection = sqlite3.connect(OUTPUT)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            city TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','inactive','preferred')),
            rating REAL NOT NULL
        );
        CREATE TABLE warehouses (
            warehouse_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','maintenance','closed'))
        );
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            city TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','inactive','vip')),
            credit_limit REAL NOT NULL
        );
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            city TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            salary REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','leave','terminated')),
            manager_id INTEGER,
            warehouse_id INTEGER,
            FOREIGN KEY(manager_id) REFERENCES employees(employee_id),
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(warehouse_id)
        );
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            cost_price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL,
            rating REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','discontinued','out_of_stock')),
            created_date TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(category_id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
        );
        CREATE TABLE inventory (
            inventory_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            reserved_quantity INTEGER NOT NULL,
            last_updated TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('available','low','unavailable')),
            UNIQUE(product_id, warehouse_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id),
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(warehouse_id)
        );
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            required_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','processing','shipped','delivered','cancelled')),
            shipping_city TEXT NOT NULL,
            billing_city TEXT NOT NULL,
            subtotal REAL NOT NULL,
            discount_amount REAL NOT NULL,
            tax_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
        );
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount_amount REAL NOT NULL,
            line_amount REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        );
        CREATE TABLE payments (
            payment_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            method TEXT NOT NULL CHECK(method IN ('card','upi','bank_transfer','cash')),
            amount REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','completed','failed','refunded')),
            transaction_reference TEXT NOT NULL UNIQUE,
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        );
        CREATE TABLE shipments (
            shipment_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            shipped_date TEXT,
            delivery_date TEXT,
            city TEXT NOT NULL,
            carrier TEXT NOT NULL,
            shipping_cost REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('preparing','in_transit','delivered','returned')),
            tracking_number TEXT NOT NULL UNIQUE,
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(warehouse_id),
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
        );
        CREATE TABLE reviews (
            review_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            title TEXT NOT NULL,
            comment TEXT,
            review_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('published','pending','rejected')),
            FOREIGN KEY(product_id) REFERENCES products(product_id),
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        );
        CREATE TABLE support_tickets (
            ticket_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_id INTEGER,
            employee_id INTEGER,
            subject TEXT NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('low','medium','high','urgent')),
            status TEXT NOT NULL CHECK(status IN ('open','in_progress','resolved','closed')),
            created_date TEXT NOT NULL,
            resolved_date TEXT,
            satisfaction_rating INTEGER CHECK(satisfaction_rating BETWEEN 1 AND 5),
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
        );
        """
    )

    categories = [(i, name, f"Products in {name.lower()}") for i, name in enumerate(
        ["Electronics", "Home", "Books", "Sports", "Beauty", "Toys", "Clothing", "Grocery", "Office", "Automotive"], 1)]
    connection.executemany("INSERT INTO categories VALUES (?,?,?)", categories)
    connection.executemany("INSERT INTO suppliers VALUES (?,?,?,?,?,?)", rows(25, lambda i: (
        i, f"Supplier {i:02d}", f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        random.choice(CITIES), random.choice(["active", "active", "preferred", "inactive"]), round(random.uniform(2.5, 5), 1))))
    connection.executemany("INSERT INTO warehouses VALUES (?,?,?,?,?)", rows(8, lambda i: (
        i, f"{CITIES[i - 1]} Distribution Centre", CITIES[i - 1], random.randrange(10000, 50001, 1000),
        random.choice(["active", "active", "maintenance"]))))
    connection.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)", rows(100, lambda i: (
        i, random.choice(FIRST_NAMES), random.choice(LAST_NAMES), f"customer{i}@example.com", random.choice(CITIES),
        str(date(2022, 1, 1) + timedelta(days=random.randrange(1300))), random.choice(["active", "active", "vip", "inactive"]),
        round(random.uniform(5000, 100000), 2))))

    employees = []
    for i in range(1, 65):
        employees.append((i, random.choice(FIRST_NAMES), random.choice(LAST_NAMES),
            random.choice(["Sales Executive", "Warehouse Associate", "Support Agent", "Operations Manager"]),
            random.choice(CITIES), str(date(2018, 1, 1) + timedelta(days=random.randrange(2800))),
            round(random.uniform(300000, 1800000), 2), random.choice(["active", "active", "leave", "terminated"]),
            random.randrange(1, i) if i > 8 else None, random.randint(1, 8)))
    connection.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?)", employees)

    products = rows(80, lambda i: (i, f"Product {i:03d}", random.randint(1, 10), random.randint(1, 25),
        round(random.uniform(100, 25000), 2), round(random.uniform(50, 10000), 2), random.randint(0, 500),
        random.randint(10, 60), round(random.uniform(2.0, 5.0), 1),
        random.choice(["active", "active", "discontinued", "out_of_stock"]),
        str(date(2021, 1, 1) + timedelta(days=random.randrange(1700)))))
    connection.executemany("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)", products)
    connection.executemany("INSERT INTO inventory VALUES (?,?,?,?,?,?,?)", rows(240, lambda i: (
        i, ((i - 1) % 80) + 1, ((i - 1) // 80) + 1, random.randint(0, 250), random.randint(0, 30),
        str(date(2025, 1, 1) + timedelta(days=random.randrange(365))), random.choice(["available", "available", "low", "unavailable"]))))

    orders = []
    for i in range(1, 181):
        subtotal = round(random.uniform(500, 60000), 2)
        discount = round(subtotal * random.choice([0, .05, .10, .15]), 2)
        tax = round((subtotal - discount) * .18, 2)
        order_day = date(2024, 1, 1) + timedelta(days=random.randrange(700))
        orders.append((i, random.randint(1, 100), random.randint(1, 64), str(order_day), str(order_day + timedelta(days=random.randint(2, 10))),
            random.choice(["pending", "processing", "shipped", "delivered", "delivered", "cancelled"]), random.choice(CITIES),
            random.choice(CITIES), subtotal, discount, tax, round(subtotal - discount + tax, 2)))
    connection.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", orders)
    connection.executemany("INSERT INTO order_items VALUES (?,?,?,?,?,?,?)", rows(500, lambda i: (
        i, ((i - 1) % 180) + 1, random.randint(1, 80), random.randint(1, 6),
        round(random.uniform(100, 25000), 2), round(random.uniform(0, 500), 2), round(random.uniform(100, 100000), 2))))
    connection.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?,?)", rows(180, lambda i: (
        i, i, str(date(2024, 1, 1) + timedelta(days=random.randrange(700))), random.choice(["card", "upi", "bank_transfer", "cash"]),
        orders[i - 1][-1], random.choice(["completed", "completed", "pending", "failed", "refunded"]), f"TXN-{i:06d}")))
    connection.executemany("INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows(180, lambda i: (
        i, i, random.randint(1, 8), random.randint(1, 64), str(date(2024, 1, 3) + timedelta(days=random.randrange(700))),
        str(date(2024, 1, 5) + timedelta(days=random.randrange(700))), random.choice(CITIES), random.choice(["BlueDart", "Delhivery", "DHL", "India Post"]),
        round(random.uniform(50, 1500), 2), random.choice(["preparing", "in_transit", "delivered", "delivered", "returned"]), f"SHIP-{i:06d}")))
    connection.executemany("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?)", rows(200, lambda i: (
        i, random.randint(1, 80), random.randint(1, 100), random.randint(1, 180), random.randint(1, 5),
        random.choice(["Excellent", "Good value", "Average", "Needs improvement", "Highly recommended"]),
        "A verified customer review.", str(date(2024, 1, 1) + timedelta(days=random.randrange(700))),
        random.choice(["published", "published", "pending", "rejected"]))))
    connection.executemany("INSERT INTO support_tickets VALUES (?,?,?,?,?,?,?,?,?,?)", rows(120, lambda i: (
        i, random.randint(1, 100), random.choice([None, random.randint(1, 180)]), random.choice([None, random.randint(1, 64)]),
        random.choice(["Late delivery", "Payment issue", "Damaged product", "Refund request", "Account help"]),
        random.choice(["low", "medium", "high", "urgent"]), random.choice(["open", "in_progress", "resolved", "closed"]),
        str(date(2024, 1, 1) + timedelta(days=random.randrange(700))), random.choice([None, str(date(2025, 1, 1) + timedelta(days=random.randrange(300)))]),
        random.choice([None, 1, 2, 3, 4, 5]))))

    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise RuntimeError(f"Foreign-key violations: {violations}")
    connection.commit()
    connection.close()
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
