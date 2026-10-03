import re
import string
from flask import current_app
from app.models.listing import Listing

class ValidationService:
    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalizes a title for duplicate comparison:
        - Lowercases
        - Removes punctuation and symbols
        - Collapses whitespace
        """
        if not title:
            return ""
        text = title.lower()
        # Remove punctuation
        text = text.translate(str.maketrans("", "", string.punctuation))
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def check_duplicate(cls, title: str, category: str, exclude_id: int = None) -> dict:
        """
        Checks if a potential duplicate listing exists in the database.
        Returns a dict with `is_duplicate`, `duplicate_id`, and `matched_title`.
        """
        norm_input = cls.normalize_title(title)
        if not norm_input:
            return {"is_duplicate": False}

        # Query listings in the same category
        query = Listing.query.filter(Listing.category == category)
        if exclude_id:
            query = query.filter(Listing.id != exclude_id)
        
        candidates = query.all()
        for cand in candidates:
            norm_cand = cls.normalize_title(cand.title)
            # Exact normalized match or very high similarity
            if norm_input == norm_cand:
                return {
                    "is_duplicate": True,
                    "duplicate_id": cand.id,
                    "matched_title": cand.title,
                    "similarity": 1.0,
                    "message": f"Listing closely duplicates existing listing #{cand.id}: '{cand.title}'"
                }
            # Simple token overlap jaccard check
            tokens_in = set(norm_input.split())
            tokens_cand = set(norm_cand.split())
            if tokens_in and tokens_cand:
                intersection = tokens_in.intersection(tokens_cand)
                union = tokens_in.union(tokens_cand)
                jaccard = len(intersection) / len(union)
                if jaccard >= 0.85 and len(tokens_in) >= 3:
                    return {
                        "is_duplicate": True,
                        "duplicate_id": cand.id,
                        "matched_title": cand.title,
                        "similarity": round(jaccard, 2),
                        "message": f"Listing has high content similarity ({int(jaccard*100)}%) with listing #{cand.id}: '{cand.title}'"
                    }

        return {"is_duplicate": False}

    @classmethod
    def validate_listing_payload(cls, data: dict, exclude_id: int = None, check_duplicates: bool = True) -> dict:
        """
        Performs comprehensive deterministic validation on listing data.
        Returns:
        {
            "valid": bool,
            "errors": dict of {field: error_message},
            "warnings": list of warning messages,
            "sanitized_data": cleaned data dict
        }
        """
        errors = {}
        warnings = []
        sanitized = {}

        max_title_len = current_app.config.get("MAX_TITLE_LENGTH", 150)
        min_title_len = current_app.config.get("MIN_TITLE_LENGTH", 5)
        max_desc_len = current_app.config.get("MAX_DESC_LENGTH", 5000)
        min_desc_len = current_app.config.get("MIN_DESC_LENGTH", 20)
        allowed_categories = current_app.config.get("ALLOWED_CATEGORIES", [])
        allowed_currencies = current_app.config.get("ALLOWED_CURRENCIES", ["INR", "USD", "EUR", "GBP", "CAD", "AUD"])
        allowed_types = current_app.config.get("ALLOWED_LISTING_TYPES", ["Product", "Service"])

        # 1. Title validation
        raw_title = data.get("title")
        if not raw_title or not str(raw_title).strip():
            errors["title"] = "Product Title is required and cannot be empty."
        else:
            title_str = str(raw_title).strip()
            if len(title_str) < min_title_len:
                errors["title"] = f"Title must be at least {min_title_len} characters long."
            elif len(title_str) > max_title_len:
                errors["title"] = f"Title cannot exceed {max_title_len} characters (currently {len(title_str)})."
            else:
                sanitized["title"] = title_str

        # 2. Description validation
        raw_desc = data.get("description")
        if not raw_desc or not str(raw_desc).strip():
            errors["description"] = "Description is required and cannot be empty."
        else:
            desc_str = str(raw_desc).strip()
            if len(desc_str) < min_desc_len:
                errors["description"] = f"Description must be at least {min_desc_len} characters long."
            elif len(desc_str) > max_desc_len:
                errors["description"] = f"Description cannot exceed {max_desc_len} characters (currently {len(desc_str)})."
            else:
                sanitized["description"] = desc_str

        # 3. Category validation
        raw_cat = data.get("category")
        if not raw_cat or not str(raw_cat).strip():
            errors["category"] = "Category must be selected."
        else:
            cat_str = str(raw_cat).strip()
            if allowed_categories and cat_str not in allowed_categories:
                errors["category"] = f"Category '{cat_str}' is not supported. Must be one of: {', '.join(allowed_categories)}"
            else:
                sanitized["category"] = cat_str

        # 4. Price validation
        raw_price = data.get("price")
        if raw_price is None or raw_price == "":
            errors["price"] = "Price is required."
        else:
            try:
                price_val = float(raw_price)
                if price_val <= 0:
                    errors["price"] = "Price must be a positive number greater than 0."
                elif price_val > 10000000:
                    errors["price"] = "Price exceeds maximum allowable limit of 10,000,000."
                else:
                    sanitized["price"] = round(price_val, 2)
            except (ValueError, TypeError):
                errors["price"] = "Price must be a valid numeric value (e.g. 19.99)."

        # 5. Currency validation
        raw_curr = data.get("currency", "INR")
        curr_str = str(raw_curr).strip().upper() if raw_curr else "INR"
        if curr_str not in allowed_currencies:
            warnings.append(f"Currency '{curr_str}' will default to INR.")
            sanitized["currency"] = "INR"
        else:
            sanitized["currency"] = curr_str

        # 6. Listing Type validation
        raw_type = data.get("listing_type", "Product")
        type_str = str(raw_type).strip().capitalize() if raw_type else "Product"
        if type_str not in allowed_types:
            sanitized["listing_type"] = "Product"
        else:
            sanitized["listing_type"] = type_str

        # 7. Seller validation
        raw_seller = data.get("seller")
        if not raw_seller or not str(raw_seller).strip():
            errors["seller"] = "Seller name or vendor identifier is required."
        else:
            seller_str = str(raw_seller).strip()
            if len(seller_str) > 120:
                errors["seller"] = "Seller name cannot exceed 120 characters."
            else:
                sanitized["seller"] = seller_str

        # 8. Attributes validation
        raw_attrs = data.get("attributes", {})
        if raw_attrs is None:
            sanitized["attributes"] = {}
        elif not isinstance(raw_attrs, dict):
            errors["attributes"] = "Attributes must be a valid key-value object/dictionary."
        else:
            cleaned_attrs = {}
            for k, v in raw_attrs.items():
                k_clean = str(k).strip()
                if k_clean:
                    cleaned_attrs[k_clean] = str(v).strip() if v is not None else ""
            sanitized["attributes"] = cleaned_attrs

        # 9. Tags validation
        raw_tags = data.get("tags", [])
        if raw_tags is None:
            sanitized["tags"] = []
        elif isinstance(raw_tags, str):
            # comma-separated string fallback
            split_tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
            # deduplicate
            sanitized["tags"] = list(dict.fromkeys(split_tags))[:20]
        elif isinstance(raw_tags, list):
            cleaned_tags = []
            for t in raw_tags:
                if t and str(t).strip():
                    cleaned_tags.append(str(t).strip().lower())
            # deduplicate preserving order
            sanitized["tags"] = list(dict.fromkeys(cleaned_tags))[:20]
        else:
            errors["tags"] = "Tags must be a list of strings."

        # 10. Duplicate detection check (warning/flag)
        if check_duplicates and "title" in sanitized and "category" in sanitized:
            dup_result = cls.check_duplicate(sanitized["title"], sanitized["category"], exclude_id=exclude_id)
            if dup_result.get("is_duplicate"):
                warnings.append(dup_result["message"])

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized_data": sanitized
        }
