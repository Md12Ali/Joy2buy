"""
Load a starter catalogue so the store is not empty after deployment.

    python manage.py seed_store

The command is safe to run more than once: existing categories and products
(matched by slug) are left untouched.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from products.models import Category, Product

CATALOGUE = [
    {
        "name": "Audio",
        "description": "Headphones, earbuds and speakers for home and "
                       "travel.",
        "products": [
            (
                "Aria Wireless Over-Ear Headphones", "79.99", 24,
                "Closed-back wireless headphones with active noise "
                "cancelling and soft memory-foam ear cushions. A full "
                "charge lasts up to 30 hours, and ten minutes on the "
                "charger gives roughly three more hours of listening.",
                "Battery life: Up to 30 hours\nConnectivity: Bluetooth 5.3 "
                "and 3.5 mm cable\nNoise cancelling: Active, 3 levels\n"
                "Weight: 255 g\nIn the box: Headphones, USB-C cable, audio "
                "cable, carry pouch",
            ),
            (
                "Pulse True Wireless Earbuds", "39.99", 60,
                "Lightweight in-ear buds with a pocket-sized charging "
                "case. Sweat and splash resistant, with touch controls for "
                "calls, music and your phone's voice assistant.",
                "Battery life: 7 hours, 28 hours with case\nWater "
                "resistance: IPX4\nConnectivity: Bluetooth 5.3\nEar tips: "
                "Small, medium and large included\nCharging: USB-C",
            ),
            (
                "Tempo Portable Bluetooth Speaker", "49.50", 0,
                "A compact speaker with surprisingly deep bass, built to "
                "survive rain, sand and the odd drop. Pair two together "
                "for stereo sound.",
                "Output: 20 W\nBattery life: Up to 14 hours\nWater "
                "resistance: IP67\nWeight: 540 g\nDimensions: 18 x 7 x 7 cm",
            ),
        ],
    },
    {
        "name": "Home & Kitchen",
        "description": "Everyday essentials that make cooking and living "
                       "easier.",
        "products": [
            (
                "Brewline Pour-Over Coffee Set", "34.00", 18,
                "A borosilicate glass carafe with a reusable stainless "
                "steel filter, so there are no paper filters to buy. Makes "
                "up to four cups and is dishwasher safe.",
                "Capacity: 600 ml\nMaterials: Borosilicate glass, "
                "stainless steel\nFilter: Reusable, double mesh\nCare: "
                "Dishwasher safe",
            ),
            (
                "Stoneware Dinner Set, 12 Piece", "64.99", 9,
                "Four dinner plates, four side plates and four bowls in a "
                "speckled reactive glaze. Each piece is finished by hand, "
                "so no two are exactly alike.",
                "Pieces: 12 (serves 4)\nMaterial: Glazed stoneware\nDinner "
                "plate: 27 cm\nCare: Dishwasher and microwave safe",
            ),
            (
                "Digital Kitchen Scale", "14.99", 75,
                "A slim tempered-glass scale that weighs in 1 g steps up "
                "to 5 kg. The tare button lets you add ingredients to the "
                "same bowl one after another.",
                "Capacity: 5 kg\nAccuracy: 1 g\nUnits: g, oz, lb, ml\n"
                "Power: 2 x AAA batteries (included)",
            ),
        ],
    },
    {
        "name": "Fitness",
        "description": "Equipment for training at home or outdoors.",
        "products": [
            (
                "FlexGrip Yoga Mat 6 mm", "24.99", 40,
                "A non-slip mat with enough cushioning to protect knees "
                "and wrists on hard floors. Alignment lines help with "
                "hand and foot placement, and a carry strap is included.",
                "Thickness: 6 mm\nSize: 183 x 61 cm\nMaterial: TPE, latex "
                "free\nWeight: 900 g",
            ),
            (
                "Adjustable Dumbbell Pair 20 kg", "89.00", 6,
                "One pair of dumbbells that adjusts from 2 kg to 10 kg "
                "each by adding or removing plates, replacing a full rack "
                "of fixed weights. Spin-lock collars keep plates secure.",
                "Total weight: 20 kg\nRange per dumbbell: 2 to 10 kg\n"
                "Grip: Knurled chrome steel\nPlates: Cast iron, "
                "rubber coated",
            ),
            (
                "Insulated Steel Water Bottle 750 ml", "18.50", 120,
                "Double-walled stainless steel keeps drinks cold for 24 "
                "hours or hot for 12. The leak-proof lid has a carry loop "
                "and fits most car cup holders.",
                "Capacity: 750 ml\nMaterial: 18/8 stainless steel\nBPA "
                "free: Yes\nCare: Hand wash recommended",
            ),
        ],
    },
    {
        "name": "Tech Accessories",
        "description": "Chargers, stands and add-ons for your devices.",
        "products": [
            (
                "65 W USB-C Fast Charger", "29.99", 55,
                "One compact wall charger for a laptop, tablet and phone. "
                "Two USB-C ports and one USB-A port share 65 watts "
                "between whatever is plugged in.",
                "Output: 65 W total\nPorts: 2 x USB-C, 1 x USB-A\nPlug: "
                "UK 3-pin, folding\nSafety: Over-heat and over-current "
                "protection",
            ),
            (
                "Aluminium Laptop Stand", "27.00", 33,
                "Raises a laptop screen to eye level to ease neck strain, "
                "with six height settings. Folds flat to slip into a "
                "laptop bag.",
                "Fits: Laptops from 10 to 16 inches\nMaterial: Anodised "
                "aluminium\nHeight settings: 6\nMaximum load: 8 kg",
            ),
            (
                "Braided USB-C Cable 2 m, Twin Pack", "11.99", 4,
                "Two nylon-braided cables tested to 10,000 bends. Each "
                "supports 60 W charging and fast data transfer.",
                "Length: 2 m\nCharging: Up to 60 W\nData: 480 Mbps\n"
                "Quantity: 2 cables",
            ),
        ],
    },
    {
        "name": "Stationery",
        "description": "Notebooks, pens and desk tools for work and study.",
        "products": [
            (
                "A5 Dotted Notebook, Hardcover", "12.50", 90,
                "192 numbered pages of 120 gsm paper that resists ink "
                "bleed-through. Includes two ribbon markers, an index "
                "page and a back pocket.",
                "Size: A5\nPages: 192, dotted\nPaper: 120 gsm, acid free\n"
                "Binding: Thread-sewn, lies flat",
            ),
            (
                "Gel Pen Set, 12 Colours", "8.99", 150,
                "Smooth 0.5 mm gel pens with quick-drying ink that will "
                "not smudge for left-handed writers. Supplied in a "
                "reusable tin.",
                "Tip: 0.5 mm\nColours: 12\nInk: Water-based gel\nBarrel: "
                "Recycled plastic",
            ),
            (
                "Bamboo Desk Organiser", "21.00", 28,
                "Five compartments and a drawer keep pens, notes and "
                "cables tidy. Made from sustainably grown bamboo with a "
                "natural oil finish.",
                "Material: Bamboo\nDimensions: 26 x 14 x 12 cm\n"
                "Compartments: 5 plus drawer\nAssembly: None required",
            ),
        ],
    },
    {
        "name": "Travel",
        "description": "Bags and organisers for commutes and trips away.",
        "products": [
            (
                "Commuter Backpack 22 L", "54.99", 21,
                "A water-resistant backpack with a padded sleeve for a "
                "16-inch laptop, a hidden pocket against the back for "
                "valuables and a strap that slides over a suitcase handle.",
                "Capacity: 22 litres\nLaptop sleeve: Up to 16 inches\n"
                "Material: Recycled polyester\nWeight: 780 g",
            ),
            (
                "Packing Cube Set, 6 Piece", "19.99", 46,
                "Six zipped cubes in three sizes keep clothes folded and "
                "separate inside a suitcase. Mesh tops let you see what "
                "is inside without unpacking.",
                "Pieces: 6\nSizes: 2 large, 2 medium, 2 small\nMaterial: "
                "Ripstop nylon\nCare: Machine washable",
            ),
            (
                "Universal Travel Adapter", "22.50", 37,
                "One adapter covering sockets in more than 150 countries, "
                "with two USB-C ports and two USB-A ports for charging "
                "phones at the same time. It does not convert voltage.",
                "Plug types: UK, EU, US, AU\nUSB ports: 2 x USB-C, 2 x "
                "USB-A\nFuse: 8 A, spare included\nNote: Not a voltage "
                "converter",
            ),
        ],
    },
]


class Command(BaseCommand):
    help = "Create starter categories and products for the JOY2BUY store."

    @transaction.atomic
    def handle(self, *args, **options):
        new_categories = 0
        new_products = 0
        for entry in CATALOGUE:
            category, created = Category.objects.get_or_create(
                slug=slugify(entry["name"]),
                defaults={
                    "name": entry["name"],
                    "description": entry["description"],
                },
            )
            new_categories += int(created)
            for name, price, stock, description, specs in entry["products"]:
                _, created = Product.objects.get_or_create(
                    slug=slugify(name),
                    defaults={
                        "category": category,
                        "name": name,
                        "price": Decimal(price),
                        "stock": stock,
                        "description": description,
                        "specifications": specs,
                    },
                )
                new_products += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {new_categories} categories and "
                f"{new_products} products added."
            )
        )
