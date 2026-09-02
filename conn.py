import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()


def get_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is missing from .env")
    return create_engine(
        db_url,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
    )

def _create_tables(conn):
    conn.execute(text("DROP TABLE IF EXISTS employees"))
    conn.execute(text("DROP TABLE IF EXISTS sales"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS shipment_orders (
            order_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR,
            order_timestamp TIMESTAMP,
            carrier_service VARCHAR,
            delivery_status VARCHAR,
            package_weight_kg NUMERIC(6,2),
            shipping_revenue_usd NUMERIC(10,2),
            delivery_delay_minutes INTEGER
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fulfillment_centers (
            hub_id VARCHAR PRIMARY KEY,
            hub_name VARCHAR,
            global_region VARCHAR,
            total_active_robots INTEGER,
            warehouse_capacity_pct NUMERIC(5,2),
            daily_processed_packages INTEGER
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS customer_experience_metrics (
            snapshot_date DATE,
            platform_type VARCHAR,
            support_ticket_category VARCHAR,
            average_csat_score NUMERIC(3,2),
            active_users_count INTEGER
        )
    """))


def _seed_data(conn):
    random.seed(42)
    now = datetime.now()

    carriers = ["Express", "Standard", "Eco-Saver"]
    statuses = ["Delivered", "In Transit", "Processing", "Delayed"]
    orders = []
    for i in range(150):
        carrier = random.choice(carriers)
        status = random.choices(statuses, weights=[55, 20, 10, 15])[0]
        weight = round(random.uniform(0.5, 40), 2)
        base = {"Express": 25, "Standard": 12, "Eco-Saver": 8}[carrier]
        revenue = round(base + weight * 1.2 + random.uniform(0, 20), 2)
        delay = (random.randint(60, 600) if status == "Delayed"
                 else random.randint(0, 30) if status == "Delivered" else 0)
        orders.append({
            "order_id": f"ORD-{10000 + i}",
            "customer_id": f"CUST-{random.randint(1000, 1200)}",
            "order_timestamp": now - timedelta(days=random.randint(0, 90),
                                               hours=random.randint(0, 23)),
            "carrier_service": carrier,
            "delivery_status": status,
            "package_weight_kg": weight,
            "shipping_revenue_usd": revenue,
            "delivery_delay_minutes": delay,
        })
    conn.execute(text("""
        INSERT INTO shipment_orders
        (order_id, customer_id, order_timestamp, carrier_service,
         delivery_status, package_weight_kg, shipping_revenue_usd,
         delivery_delay_minutes)
        VALUES (:order_id, :customer_id, :order_timestamp, :carrier_service,
                :delivery_status, :package_weight_kg, :shipping_revenue_usd,
                :delivery_delay_minutes)
    """), orders)

    hubs = [
        ("NYC-01", "NYC-01", "North America", 1200, 87.5, 62000),
        ("LAX-02", "LAX-02", "North America", 950, 74.2, 48000),
        ("LON-04", "LON-04", "EMEA", 1100, 91.0, 57000),
        ("BER-03", "BER-03", "EMEA", 700, 63.8, 31000),
        ("TOK-02", "TOK-02", "APAC", 1400, 95.3, 71000),
        ("SIN-05", "SIN-05", "APAC", 850, 69.4, 40000),
        ("GRU-06", "GRU-06", "LATAM", 400, 58.1, 21000),
        ("MEX-07", "MEX-07", "LATAM", 520, 66.7, 26000),
    ]
    conn.execute(text("""
        INSERT INTO fulfillment_centers
        (hub_id, hub_name, global_region, total_active_robots,
         warehouse_capacity_pct, daily_processed_packages)
        VALUES (:h0, :h1, :h2, :h3, :h4, :h5)
    """), [{"h0": h[0], "h1": h[1], "h2": h[2], "h3": h[3],
            "h4": h[4], "h5": h[5]} for h in hubs])

    platforms = ["iOS App", "Android App", "Desktop Web", "Mobile Web"]
    tickets = ["Missing Item", "Refund Request", "Billing", "Technical Error"]
    base_users = {"iOS App": 12000, "Android App": 15000,
                  "Desktop Web": 8000, "Mobile Web": 5000}
    metrics = []
    for day in range(30):
        date = (now - timedelta(days=29 - day)).date()
        for p in platforms:
            growth = day * random.randint(40, 120)
            metrics.append({
                "snapshot_date": date,
                "platform_type": p,
                "support_ticket_category": random.choices(
                    tickets, weights=[30, 25, 20, 25])[0],
                "average_csat_score": round(random.uniform(3.4, 4.8), 2),
                "active_users_count": base_users[p] + growth
                                      + random.randint(-300, 300),
            })
    conn.execute(text("""
        INSERT INTO customer_experience_metrics
        (snapshot_date, platform_type, support_ticket_category,
         average_csat_score, active_users_count)
        VALUES (:snapshot_date, :platform_type, :support_ticket_category,
                :average_csat_score, :active_users_count)
    """), metrics)

def setup_db_and_get_schema() -> str:
    engine = get_engine()

    with engine.connect() as conn:
        _create_tables(conn)
        count = conn.execute(text(
            "SELECT COUNT(*) FROM shipment_orders")).fetchone()[0]
        if count == 0:
            _seed_data(conn)
        conn.commit()

    inspector = inspect(engine)
    schema_str = "Database Schema:\n"
    for table in inspector.get_table_names():
        if table.startswith("checkpoint"):
            continue
        schema_str += f"\nTable: {table}\nColumns:\n"
        for col in inspector.get_columns(table):
            schema_str += f"  - {col['name']} ({str(col['type'])})\n"
    return schema_str.strip()


if __name__ == "__main__":
    print(setup_db_and_get_schema())