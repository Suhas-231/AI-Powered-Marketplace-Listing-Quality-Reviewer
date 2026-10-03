import json
import logging
from pathlib import Path
from app.database import db
from app.models.policy import Policy
from app.models.user import User
from app.models.listing import Listing

logger = logging.getLogger(__name__)

def seed_initial_data():
    """Seeds demonstration policies, default user, and realistic showcase listings."""
    try:
        # 1. Seed Default User
        if not User.query.first():
            default_user = User(
                name="Suhas (Compliance Officer)",
                email="compliance@marketplace.local",
                role="Senior Reviewer"
            )
            db.session.add(default_user)
            db.session.commit()
            logger.info("Default user seeded.")

        # 2. Seed Demonstration Policies
        if Policy.query.count() == 0:
            policy_file = Path(__file__).resolve().parent.parent.parent.parent / "policy_documents" / "sample_policies.json"
            policies_data = []
            if policy_file.exists():
                with open(policy_file, "r", encoding="utf-8") as f:
                    policies_data = json.load(f)
            else:
                # Fallback embedded demonstration policies
                policies_data = [
                    {
                        "policy_code": "POL-TITLE-001",
                        "section_number": "Section 1.1",
                        "title": "Title Formatting & Length Limitation",
                        "category": "Product title guidelines",
                        "description": "Titles must accurately identify the product, begin with brand name, and not exceed 150 characters. Emoji, excessive punctuation, and all-caps text are prohibited.",
                        "severity_guidance": "Medium",
                        "is_active": True,
                        "is_demo_policy": True
                    },
                    {
                        "policy_code": "POL-PROM-001",
                        "section_number": "Section 3.1",
                        "title": "Unsubstantiated Promotional Superlatives",
                        "category": "Promotional claims",
                        "description": "Subjective superlatives like '#1 Best in the World', 'Miracle Solution', or 'Guaranteed 100% Success' cannot be claimed without verified independent certification.",
                        "severity_guidance": "High",
                        "is_active": True,
                        "is_demo_policy": True
                    },
                    {
                        "policy_code": "POL-HLTH-001",
                        "section_number": "Section 4.1",
                        "title": "Medical, Therapeutic & Disease-Cure Claims",
                        "category": "Medical and health claims",
                        "description": "Products that are not certified prescription medications must never claim to cure, treat, diagnose, or prevent human diseases.",
                        "severity_guidance": "High",
                        "is_active": True,
                        "is_demo_policy": True
                    },
                    {
                        "policy_code": "POL-DESC-002",
                        "section_number": "Section 2.2",
                        "title": "Prohibition of Off-Platform Redirection",
                        "category": "Description guidelines",
                        "description": "Product descriptions must never include hyperlinks, external website URLs, WhatsApp numbers, direct phone numbers, or prompts directing transactions outside the marketplace.",
                        "severity_guidance": "High",
                        "is_active": True,
                        "is_demo_policy": True
                    }
                ]

            for item in policies_data:
                p = Policy(
                    policy_code=item.get("policy_code"),
                    section_number=item.get("section_number"),
                    title=item.get("title"),
                    category=item.get("category"),
                    description=item.get("description"),
                    severity_guidance=item.get("severity_guidance", "Medium"),
                    is_active=item.get("is_active", True),
                    is_demo_policy=item.get("is_demo_policy", True)
                )
                db.session.add(p)
            db.session.commit()
            logger.info(f"Seeded {len(policies_data)} demonstration policies.")

        # 3. Seed Realistic Sample Listings
        if Listing.query.count() == 0:
            user = User.query.first()
            sample_listings = [
                {
                    "title": "MIRACLE HERBAL TEA 100% CURES DIABETES & CANCER FAST WEIGHT LOSS GUARANTEED",
                    "description": "Our miraculous natural herbal detox tea is scientifically proven to completely cure chronic diabetes, arthritis, and cancer in 14 days! You will lose 15kg in one week with zero dieting. Order directly on WhatsApp at +1-555-0199 for 20% discount off-platform! Visit our secret shop at https://miracle-cures.fake/buy.",
                    "category": "Health & Personal Care",
                    "price": 49.99,
                    "currency": "USD",
                    "listing_type": "Product",
                    "seller": "Vitality Miracle Labs",
                    "attributes": {
                        "Volume": "250g",
                        "Ingredients": "Herbal Blend, Green Tea",
                        "Form": "Loose Leaf"
                    },
                    "tags": ["miracle", "weight loss", "cure diabetes", "cancer", "detox"],
                    "status": "pending_review"
                },
                {
                    "title": "UltraBass Pro Wireless Noise Cancelling Over-Ear Headphones Bluetooth 5.3",
                    "description": "Experience pristine acoustics with the UltraBass Pro wireless headphones. Features active noise cancellation up to 35dB, 40mm neodymium dynamic audio drivers, ergonomic protein leather memory foam ear cushions, and up to 40 hours continuous playtime on a single charge. Includes USB-C fast charging cable, 3.5mm auxiliary cable, and protective travel case.",
                    "category": "Electronics & Gadgets",
                    "price": 129.50,
                    "currency": "USD",
                    "listing_type": "Product",
                    "seller": "SonicTech Audio Direct",
                    "attributes": {
                        "Battery Life": "40 Hours",
                        "Connectivity": "Bluetooth 5.3",
                        "Noise Cancellation": "Active (ANC 35dB)",
                        "Color": "Matte Black",
                        "Weight": "240g"
                    },
                    "tags": ["headphones", "bluetooth", "noise cancelling", "wireless audio"],
                    "status": "draft"
                },
                {
                    "title": "CHEAP 100% GENUINE APPLE IPHONE 15 PRO MAX FIRST COPY OEM UNBEATABLE BEST PRICE IN WORLD!!!!",
                    "description": "Buy original replica brand new phone. Infinite battery life guaranteed never dies. Contact seller via email directpay@scam-mail.org for special wire transfer discount. We do not accept returns. Fast international drop shipping.",
                    "category": "Electronics & Gadgets",
                    "price": 299.00,
                    "currency": "USD",
                    "listing_type": "Product",
                    "seller": "Global Electronics Liquidation",
                    "attributes": {
                        "Storage": "1000GB",
                        "Battery": "Infinite",
                        "Warranty": "Lifetime"
                    },
                    "tags": ["apple", "iphone", "replica", "cheapest", "oem"],
                    "status": "pending_review"
                }
            ]

            for s in sample_listings:
                listing = Listing(
                    user_id=user.id if user else None,
                    title=s["title"],
                    description=s["description"],
                    category=s["category"],
                    price=s["price"],
                    currency=s["currency"],
                    listing_type=s["listing_type"],
                    seller=s["seller"],
                    attributes=s["attributes"],
                    tags=s["tags"],
                    status=s["status"]
                )
                db.session.add(listing)
            db.session.commit()
            logger.info("Sample listings seeded.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding initial data: {e}")
