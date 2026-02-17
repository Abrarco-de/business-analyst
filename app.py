from thefuzz import process

def get_header_mapping(columns):
    """Matches headers using math similarity instead of Gemini API."""
    standard_schema = ["transaction_id", "timestamp", "product_name", "quantity", "unit_price", "cost_price"]
    
    # Custom Arabic/Messy mapping hints
    synonyms = {
        "product_name": ["item", "desc", "منتج", "اسم"],
        "unit_price": ["price", "rate", "سعر", "بيع", "sar"],
        "quantity": ["qty", "amount", "كمية", "عدد"],
        "cost_price": ["cost", "purchase", "تكلفة", "شراء"]
    }

    mapping = {}
    for col in columns:
        col_clean = col.lower().strip()
        
        # Check against synonyms first
        for standard, hints in synonyms.items():
            # If the column name is very similar to our hints
            match, score = process.extractOne(col_clean, hints)
            if score > 85: # 85% similarity
                mapping[col] = standard
                break
                
    return mapping








