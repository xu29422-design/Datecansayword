import hashlib
import json

def generate_business_key(record, dimensions):
    """
    Generate a unique hash based on dimension fields.
    """
    key_string = "|".join([str(record.get(dim, "")) for dim in dimensions])
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()

def merge_data(existing_data, new_data, dimensions):
    """
    Merge new data into existing data idempotently based on dimensions.
    """
    # Create a dictionary of existing records mapped by their business key
    merged_dict = {generate_business_key(record, dimensions): record for record in existing_data}
    
    # Update or insert new records
    for record in new_data:
        key = generate_business_key(record, dimensions)
        merged_dict[key] = record
        
    # Return as list
    return list(merged_dict.values())

def process_and_save_to_github(storage, intercepted_data, repo_data_path="data/funnel_data.json"):
    """
    Process intercepted data, merge with existing GitHub data, and save back.
    """
    # 1. Extract records from intercepted data
    new_records = []
    for item in intercepted_data:
        data = item.get("data", {})
        if isinstance(data, dict) and "list" in data and "columns" in data:
            records = data["list"]
            columns_info = data["columns"]
            
            # Map column names
            col_mapping = {col["columnAsName"]: col["columnTitle"] for col in columns_info}
            
            for record in records:
                mapped_record = {col_mapping.get(k, k): v for k, v in record.items()}
                new_records.append(mapped_record)
                
    if not new_records:
        print("No valid funnel data found in intercepted requests.")
        return False

    # 2. Fetch existing data from GitHub
    existing_data = storage.read_json(repo_data_path) or []
    
    # 3. Define dimensions for deduplication (e.g., Date, Platform, Product)
    dimensions = ["统计时间", "端", "产品", "comp"] # Adjust based on actual data
    
    # 4. Merge data
    merged_data = merge_data(existing_data, new_records, dimensions)
    
    # 5. Save back to GitHub
    storage.write_json(repo_data_path, merged_data, f"Update data with {len(new_records)} new records")
    return True
