import argparse
import sys
import os
import logging
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.db.conn import get_db

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ADMIN")

def create_shop(name, timezone="Asia/Tashkent"):
    try:
        with get_db() as cur:
            cur.execute(
                "INSERT INTO shops (name, timezone) VALUES (%s, %s) RETURNING id",
                (name, timezone)
            )
            shop_id = cur.fetchone()['id']
            print(f"\n✅ Shop Created Successfully!")
            print(f"🆔 Shop ID: {shop_id}")
            print(f"📛 Name: {name}")
            print(f"🌍 Timezone: {timezone}")
            print(f"\n👉 Next Step: Set SHOP_ID={shop_id} in your deployment.")
            return shop_id
    except Exception as e:
        logger.error(f"Error creating shop: {e}")

def add_barber(shop_id, name):
    try:
        with get_db() as cur:
            cur.execute(
                "INSERT INTO barbers (shop_id, display_name) VALUES (%s, %s) RETURNING id",
                (shop_id, name)
            )
            barber_id = cur.fetchone()['id']
            
            # Add default services
            cur.execute(
                "INSERT INTO services (shop_id, name, duration_min) VALUES (%s, 'Haircut', 30), (%s, 'Beard', 20)",
                (shop_id, shop_id)
            )
            
            # Add default work hours (Mon-Sun 10-20)
            for day in range(7):
                cur.execute(
                    "INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) VALUES (%s, %s, '10:00', '20:00', 30)",
                    (barber_id, day)
                )
                
            print(f"\n✅ Barber '{name}' Added to Shop {shop_id}!")
            print(f"🆔 Barber ID: {barber_id}")
            print("✨ Auto-added default services and work hours (10-20).")
    except Exception as e:
        logger.error(f"Error adding barber: {e}")

def list_shops():
    try:
        with get_db() as cur:
            cur.execute("SELECT * FROM shops ORDER BY id")
            shops = cur.fetchall()
            print("\n📋 --- ACTIVE SHOPS ---")
            for s in shops:
                print(f"[{s['id']}] {s['name']} (created: {s['created_at'].strftime('%Y-%m-%d')})")
    except Exception as e:
        logger.error(f"Error listing shops: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Barber Bot Admin Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create_shop
    p_shop = subparsers.add_parser("create_shop", help="Create a new shop")
    p_shop.add_argument("name", help="Name of the shop")
    
    # add_barber
    p_barber = subparsers.add_parser("add_barber", help="Add a barber to a shop")
    p_barber.add_argument("shop_id", type=int, help="Shop ID")
    p_barber.add_argument("name", help="Barber Name")
    
    # list_shops
    p_list = subparsers.add_parser("list_shops", help="List all shops")

    args = parser.parse_args()

    if args.command == "create_shop":
        create_shop(args.name)
    elif args.command == "add_barber":
        add_barber(args.shop_id, args.name)
    elif args.command == "list_shops":
        list_shops()
