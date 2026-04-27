"""Seed database with demo camping products and an admin user.

Run: python -m app.seed
"""

import asyncio
import uuid

from sqlalchemy import select

from app.core.database import async_session, engine, Base
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.product import Category, Product, ProductImage

# Import all models
import app.models  # noqa: F401


CATEGORIES = [
    {"name": "Tents", "slug": "tents", "description": "Camping tents for every adventure"},
    {"name": "Sleeping Bags", "slug": "sleeping-bags", "description": "Stay warm in the wild"},
    {"name": "Backpacks", "slug": "backpacks", "description": "Carry your gear in comfort"},
    {"name": "Cooking", "slug": "cooking", "description": "Camp stoves, cookware, and utensils"},
    {"name": "Lighting", "slug": "lighting", "description": "Headlamps, lanterns, and flashlights"},
    {"name": "Furniture", "slug": "furniture", "description": "Chairs, tables, and hammocks"},
]

PRODUCT_IMAGES = {
    "trailmaster-2-person-tent": "/images/products/trailmaster-2-person-tent.jpg",
    "basecamp-4-person-family-tent": "/images/products/basecamp-4-person-family-tent.jpg",
    "summit-pro-ultralight-tent": "/images/products/summit-pro-ultralight-tent.jpg",
    "arctic-night-minus10-sleeping-bag": "/images/products/arctic-night-sleeping-bag.jpg",
    "summer-breeze-sleeping-bag": "/images/products/summer-breeze-sleeping-bag.jpg",
    "expedition-65l-backpack": "/images/products/expedition-65l-backpack.jpg",
    "daytripper-25l-pack": "/images/products/daytripper-25l-pack.jpg",
    "jetboil-compact-stove": "/images/products/jetboil-compact-stove.jpg",
    "campchef-cast-iron-skillet": "/images/products/campchef-cast-iron-skillet.jpg",
    "titanium-spork-set-4pack": "/images/products/titanium-spork-set.jpg",
    "lumibeam-600-headlamp": "/images/products/lumibeam-600-headlamp.jpg",
    "solar-lantern-pro": "/images/products/solar-lantern-pro.jpg",
    "packlite-camp-chair": "/images/products/packlite-camp-chair.jpg",
    "treehugger-hammock": "/images/products/treehugger-hammock.jpg",
}

PRODUCTS = [
    # Tents
    {
        "name": "TrailMaster 2-Person Tent",
        "slug": "trailmaster-2-person-tent",
        "description": "Lightweight 2-person tent with full rain fly. 3-season rated, weighs only 2.1 kg. Perfect for backpacking trips.",
        "price": 129.99,
        "stock": 30,
        "category_slug": "tents",
    },
    {
        "name": "BaseCamp 4-Person Family Tent",
        "slug": "basecamp-4-person-family-tent",
        "description": "Spacious family tent with 2 rooms and a vestibule. Easy setup with color-coded poles.",
        "price": 249.99,
        "stock": 15,
        "category_slug": "tents",
    },
    {
        "name": "Summit Pro Ultralight Tent",
        "slug": "summit-pro-ultralight-tent",
        "description": "Ultra-lightweight solo tent at just 900g. Ideal for thru-hikers and minimalist campers.",
        "price": 349.99,
        "stock": 10,
        "category_slug": "tents",
    },
    # Sleeping Bags
    {
        "name": "Arctic Night -10°C Sleeping Bag",
        "slug": "arctic-night-minus10-sleeping-bag",
        "description": "Mummy-style sleeping bag rated to -10°C. Down fill with water-resistant shell.",
        "price": 189.99,
        "stock": 20,
        "category_slug": "sleeping-bags",
    },
    {
        "name": "Summer Breeze Sleeping Bag",
        "slug": "summer-breeze-sleeping-bag",
        "description": "Lightweight rectangular sleeping bag for warm weather camping. Comfortable down to 10°C.",
        "price": 59.99,
        "stock": 50,
        "category_slug": "sleeping-bags",
    },
    # Backpacks
    {
        "name": "Expedition 65L Backpack",
        "slug": "expedition-65l-backpack",
        "description": "Full-featured 65-liter backpack with adjustable torso length, rain cover, and multiple compartments.",
        "price": 199.99,
        "stock": 25,
        "category_slug": "backpacks",
    },
    {
        "name": "DayTripper 25L Pack",
        "slug": "daytripper-25l-pack",
        "description": "Versatile daypack with hydration sleeve, hip belt pockets, and breathable back panel.",
        "price": 79.99,
        "stock": 40,
        "category_slug": "backpacks",
    },
    # Cooking
    {
        "name": "JetBoil Compact Stove",
        "slug": "jetboil-compact-stove",
        "description": "All-in-one cooking system that boils water in 2 minutes. Includes 1L pot and stabilizer.",
        "price": 109.99,
        "stock": 35,
        "category_slug": "cooking",
    },
    {
        "name": "CampChef Cast Iron Skillet",
        "slug": "campchef-cast-iron-skillet",
        "description": "10-inch pre-seasoned cast iron skillet. Perfect for campfire cooking.",
        "price": 34.99,
        "stock": 45,
        "category_slug": "cooking",
    },
    {
        "name": "Titanium Spork Set (4-pack)",
        "slug": "titanium-spork-set-4pack",
        "description": "Lightweight titanium sporks, each weighing only 17g. Comes in a mesh carry bag.",
        "price": 24.99,
        "stock": 60,
        "category_slug": "cooking",
    },
    # Lighting
    {
        "name": "LumiBeam 600 Headlamp",
        "slug": "lumibeam-600-headlamp",
        "description": "600-lumen rechargeable headlamp with red-light mode. USB-C charging, 40-hour battery life.",
        "price": 44.99,
        "stock": 55,
        "category_slug": "lighting",
    },
    {
        "name": "Solar Lantern Pro",
        "slug": "solar-lantern-pro",
        "description": "Collapsible solar-powered lantern with 3 brightness levels. Also charges via USB.",
        "price": 29.99,
        "stock": 40,
        "category_slug": "lighting",
    },
    # Furniture
    {
        "name": "PackLite Camp Chair",
        "slug": "packlite-camp-chair",
        "description": "Ultralight folding chair weighing 870g. Supports up to 120 kg. Packs into its own carry bag.",
        "price": 69.99,
        "stock": 30,
        "category_slug": "furniture",
    },
    {
        "name": "TreeHugger Hammock",
        "slug": "treehugger-hammock",
        "description": "Double-size parachute nylon hammock with tree-friendly straps. Holds up to 200 kg.",
        "price": 39.99,
        "stock": 35,
        "category_slug": "furniture",
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(select(User).where(User.email == "admin@campgear.com"))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Create admin user
        admin = User(
            email="admin@campgear.com",
            hashed_password=hash_password("Admin123!"),
            full_name="CampGear Admin",
            role=Role.ADMIN,
        )
        session.add(admin)

        # Create demo customer
        customer = User(
            email="camper@example.com",
            hashed_password=hash_password("Camper123!"),
            full_name="Happy Camper",
            role=Role.CUSTOMER,
        )
        session.add(customer)

        # Create categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat = Category(**cat_data)
            session.add(cat)
            cat_map[cat_data["slug"]] = cat

        await session.flush()

        # Create products and images
        for prod_data in PRODUCTS:
            cat_slug = prod_data.pop("category_slug")
            slug = prod_data["slug"]
            product = Product(category_id=cat_map[cat_slug].id, **prod_data)
            session.add(product)
            await session.flush()
            if slug in PRODUCT_IMAGES:
                image = ProductImage(
                    product_id=product.id,
                    url=PRODUCT_IMAGES[slug],
                    alt_text=prod_data["name"],
                )
                session.add(image)

        await session.commit()
        print("Seed data created successfully!")
        print("  Admin:    admin@campgear.com / Admin123!")
        print("  Customer: camper@example.com / Camper123!")
        print(f"  Categories: {len(CATEGORIES)}")
        print(f"  Products: {len(PRODUCTS)}")


if __name__ == "__main__":
    asyncio.run(seed())
