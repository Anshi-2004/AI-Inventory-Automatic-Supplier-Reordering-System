import os
import csv
import random
from datetime import datetime, date, timedelta, timezone

# Output directory for CSV files
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "dataset")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"📦 Generating synthetic dataset in: {OUTPUT_DIR}")

# Seed random numbers for reproducibility
random.seed(42)

# --- Configuration & Mock Lists ---
START_DATE = datetime(2025, 8, 1, tzinfo=timezone.utc)
END_DATE = datetime(2026, 8, 1, tzinfo=timezone.utc)
TOTAL_DAYS = (END_DATE - START_DATE).days

SUPPLIER_NAMES = [
    ("Acme Medical Supplies", "Acme Corp"),
    ("Medline Hospital Equipment", "Medline Industries"),
    ("Cardinal Health Solutions", "Cardinal Health Inc"),
    ("McKesson Pharma", "McKesson Corporation"),
    ("Raj Medical Wholesale", "Raj Enterprises"),
    ("Global Biotech Reagents", "Global Biotech Ltd"),
    ("Premier Surgicals", "Premier Products"),
    ("Helix Diagnostics", "Helix Labs"),
    ("Safety First PPE", "Safety First Group"),
    ("Apex Pharmaceuticals", "Apex Pharma Ltd"),
    ("Lifeline Medicals", "Lifeline Healthcare"),
    ("Beacon Lab Supplies", "Beacon Scientific"),
    ("Comfort Care Gloves", "Comfort Care Inc"),
    ("Metro Surgical Supplies", "Metro Surgicals"),
    ("Zenith Health Supplies", "Zenith Pharma")
]

PRODUCT_TEMPLATES = [
    # (Category, Name, Code, Unit, AvgDailyUsage, StorageLocation)
    # --- Medicines ---
    ("Medicines", "Paracetamol 500mg", "MED-PCM-500", "units", 45, "Shelf A-1"),
    ("Medicines", "Ibuprofen 400mg", "MED-IBU-400", "units", 30, "Shelf A-2"),
    ("Medicines", "Amoxicillin 500mg", "MED-AMX-500", "units", 25, "Shelf A-3"),
    ("Medicines", "Metformin 500mg", "MED-MET-500", "units", 40, "Shelf A-4"),
    ("Medicines", "Atorvastatin 20mg", "MED-ATO-20", "units", 35, "Shelf A-5"),
    ("Medicines", "Omeprazole 20mg", "MED-OME-20", "units", 28, "Shelf A-6"),
    ("Medicines", "Amlodipine 5mg", "MED-AML-5", "units", 32, "Shelf A-7"),
    ("Medicines", "Azithromycin 250mg", "MED-AZI-250", "units", 15, "Shelf A-8"),
    ("Medicines", "Gabapentin 300mg", "MED-GAB-300", "units", 20, "Shelf A-9"),
    ("Medicines", "Losartan 50mg", "MED-LOS-50", "units", 30, "Shelf A-10"),
    ("Medicines", "Pantoprazole 40mg", "MED-PAN-40", "units", 22, "Shelf A-11"),
    ("Medicines", "Cetirizine 10mg", "MED-CET-10", "units", 18, "Shelf A-12"),
    ("Medicines", "Prednisone 10mg", "MED-PRE-10", "units", 12, "Shelf A-13"),
    ("Medicines", "Clopidogrel 75mg", "MED-CLO-75", "units", 25, "Shelf A-14"),
    ("Medicines", "Montelukast 10mg", "MED-MON-10", "units", 20, "Shelf A-15"),
    ("Medicines", "Albuterol Inhaler", "MED-ALB-INH", "units", 8, "Shelf A-16"),
    ("Medicines", "Levothyroxine 50mcg", "MED-LEV-50", "units", 50, "Shelf A-17"),
    ("Medicines", "Tramadol 50mg", "MED-TRA-50", "units", 14, "Shelf A-18"),
    ("Medicines", "Metoprolol 25mg", "MED-MTP-25", "units", 28, "Shelf A-19"),
    ("Medicines", "Warfarin 5mg", "MED-WAR-5", "units", 10, "Shelf A-20"),

    # --- Medical Supplies ---
    ("Medical Supplies", "Syringes (5ml)", "SUP-SYR-5ML", "pieces", 120, "Shelf B-1"),
    ("Medical Supplies", "Syringes (2ml)", "SUP-SYR-2ML", "pieces", 150, "Shelf B-2"),
    ("Medical Supplies", "Syringes (10ml)", "SUP-SYR-10ML", "pieces", 80, "Shelf B-3"),
    ("Medical Supplies", "IV Cannula 20G", "SUP-IVC-20G", "pieces", 50, "Shelf B-4"),
    ("Medical Supplies", "IV Cannula 22G", "SUP-IVC-22G", "pieces", 60, "Shelf B-5"),
    ("Medical Supplies", "IV Cannula 18G", "SUP-IVC-18G", "pieces", 30, "Shelf B-6"),
    ("Medical Supplies", "Alcohol Prep Pads", "SUP-ALC-PAD", "boxes", 12, "Shelf B-7"),
    ("Medical Supplies", "Cotton Wool Rolls", "SUP-CTN-ROL", "pieces", 15, "Shelf B-8"),
    ("Medical Supplies", "Adhesive Plasters", "SUP-ADH-PLST", "boxes", 8, "Shelf B-9"),
    ("Medical Supplies", "Bandage Roll 4-inch", "SUP-BND-4IN", "pieces", 40, "Shelf B-10"),
    ("Medical Supplies", "Bandage Roll 3-inch", "SUP-BND-3IN", "pieces", 45, "Shelf B-11"),
    ("Medical Supplies", "Gauze Swabs 10x10cm", "SUP-GZE-SWB", "boxes", 18, "Shelf B-12"),
    ("Medical Supplies", "IV Infusion Set", "SUP-IVF-SET", "pieces", 70, "Shelf B-13"),
    ("Medical Supplies", "Urine Drainage Bag", "SUP-URN-BAG", "pieces", 25, "Shelf B-14"),
    ("Medical Supplies", "Foley Catheter Fr16", "SUP-FOL-CAT", "pieces", 15, "Shelf B-15"),
    ("Medical Supplies", "Disposable Scalpel #11", "SUP-DSC-11", "pieces", 20, "Shelf B-16"),
    ("Medical Supplies", "Disposable Scalpel #15", "SUP-DSC-15", "pieces", 18, "Shelf B-17"),
    ("Medical Supplies", "Sterile Water 10ml", "SUP-WTR-10ML", "units", 100, "Shelf B-18"),
    ("Medical Supplies", "Normal Saline 500ml", "SUP-SAL-500", "bottles", 60, "Shelf B-19"),
    ("Medical Supplies", "Ringer Lactate 500ml", "SUP-RIN-500", "bottles", 40, "Shelf B-20"),

    # --- PPE ---
    ("PPE", "Latex Gloves (M)", "PPE-GLV-LAT-M", "boxes", 25, "Shelf C-1"),
    ("PPE", "Latex Gloves (L)", "PPE-GLV-LAT-L", "boxes", 20, "Shelf C-2"),
    ("PPE", "Latex Gloves (S)", "PPE-GLV-LAT-S", "boxes", 15, "Shelf C-3"),
    ("PPE", "Nitrile Gloves (M)", "PPE-GLV-NIT-M", "boxes", 30, "Shelf C-4"),
    ("PPE", "Nitrile Gloves (L)", "PPE-GLV-NIT-L", "boxes", 28, "Shelf C-5"),
    ("PPE", "Nitrile Gloves (S)", "PPE-GLV-NIT-S", "boxes", 18, "Shelf C-6"),
    ("PPE", "N95 Respirator Mask", "PPE-MSK-N95", "pieces", 90, "Shelf C-7"),
    ("PPE", "3-Ply Surgical Mask", "PPE-MSK-3PLY", "boxes", 15, "Shelf C-8"),
    ("PPE", "Surgical Gown Sterile", "PPE-GWN-STR", "pieces", 22, "Shelf C-9"),
    ("PPE", "Disposable Gown Blue", "PPE-GWN-DSP", "pieces", 35, "Shelf C-10"),
    ("PPE", "Protective Goggles", "PPE-GOG-PRT", "pieces", 5, "Shelf C-11"),
    ("PPE", "Face Shield Clear", "PPE-FSH-CLR", "pieces", 8, "Shelf C-12"),
    ("PPE", "Shoe Covers Disposable", "PPE-SHC-DSP", "boxes", 6, "Shelf C-13"),
    ("PPE", "Bouffant Caps Blue", "PPE-CAP-BLU", "boxes", 5, "Shelf C-14"),
    ("PPE", "Hand Sanitizer 500ml", "PPE-SAN-500", "bottles", 14, "Shelf C-15"),
    ("PPE", "Hand Sanitizer 100ml", "PPE-SAN-100", "bottles", 20, "Shelf C-16"),
    ("PPE", "Disinfectant Wipes", "PPE-WIP-DIS", "tubs", 10, "Shelf C-17"),
    ("PPE", "Biohazard Bags Large", "PPE-BIO-LRG", "pieces", 40, "Shelf C-18"),
    ("PPE", "Biohazard Bags Medium", "PPE-BIO-MED", "pieces", 50, "Shelf C-19"),
    ("PPE", "Aprons Waterproof", "PPE-APR-WPR", "boxes", 4, "Shelf C-20"),

    # --- Surgical ---
    ("Surgical", "Vicryl Suture 3-0", "SRG-VIC-30", "boxes", 6, "Shelf D-1"),
    ("Surgical", "Vicryl Suture 2-0", "SRG-VIC-20", "boxes", 5, "Shelf D-2"),
    ("Surgical", "Vicryl Suture 4-0", "SRG-VIC-40", "boxes", 4, "Shelf D-3"),
    ("Surgical", "Silk Suture 3-0", "SRG-SLK-30", "boxes", 5, "Shelf D-4"),
    ("Surgical", "Silk Suture 2-0", "SRG-SLK-20", "boxes", 4, "Shelf D-5"),
    ("Surgical", "Monocryl Suture 4-0", "SRG-MON-40", "boxes", 3, "Shelf D-6"),
    ("Surgical", "Surgical Stapler", "SRG-STP-DSP", "pieces", 8, "Shelf D-7"),
    ("Surgical", "Staple Remover", "SRG-STP-REM", "pieces", 10, "Shelf D-8"),
    ("Surgical", "Epidural Needle 18G", "SRG-NDL-EPI", "pieces", 12, "Shelf D-9"),
    ("Surgical", "Suction Tubing 3m", "SRG-SUC-TUB", "pieces", 15, "Shelf D-10"),
    ("Surgical", "Lap Sponge 30x30cm", "SRG-LAP-SPN", "packs", 25, "Shelf D-11"),
    ("Surgical", "Surgical Blades #10", "SRG-BLD-10", "boxes", 3, "Shelf D-12"),
    ("Surgical", "Surgical Blades #22", "SRG-BLD-22", "boxes", 2, "Shelf D-13"),
    ("Surgical", "Bone Wax 2.5g", "SRG-BNE-WAX", "boxes", 2, "Shelf D-14"),
    ("Surgical", "Foley Catheter Fr18", "SRG-FOL-18", "pieces", 10, "Shelf D-15"),
    ("Surgical", "Surgical Tape 2-inch", "SRG-TAP-2IN", "rolls", 14, "Shelf D-16"),
    ("Surgical", "Skin Marker Pen", "SRG-SKN-PEN", "pieces", 15, "Shelf D-17"),
    ("Surgical", "Suction Yankauer Tip", "SRG-SUC-YNK", "pieces", 12, "Shelf D-18"),
    ("Surgical", "C-Section Drape", "SRG-DRP-CS", "pieces", 6, "Shelf D-19"),
    ("Surgical", "Universal Drape Pack", "SRG-DRP-UNV", "packs", 10, "Shelf D-20"),

    # --- Lab Reagents ---
    ("Lab Reagents", "EDTA Blood Tubes (K2)", "LAB-EDT-K2", "pieces", 200, "Shelf E-1"),
    ("Lab Reagents", "Serum Sep Tubes (SST)", "LAB-SRM-SST", "pieces", 180, "Shelf E-2"),
    ("Lab Reagents", "Sodium Citrate Tubes", "LAB-SCT-TUBE", "pieces", 100, "Shelf E-3"),
    ("Lab Reagents", "Glucose Test Strips", "LAB-GLU-STP", "boxes", 12, "Shelf E-4"),
    ("Lab Reagents", "HIV Rapid Test Kits", "LAB-HIV-KIT", "kits", 5, "Shelf E-5"),
    ("Lab Reagents", "HCV Rapid Test Kits", "LAB-HCV-KIT", "kits", 4, "Shelf E-6"),
    ("Lab Reagents", "Syphilis Test Kits", "LAB-SYP-KIT", "kits", 4, "Shelf E-7"),
    ("Lab Reagents", "Urine Dipsticks 10T", "LAB-URN-DIP", "boxes", 8, "Shelf E-8"),
    ("Lab Reagents", "Pregnancy Test HCG", "LAB-HCG-STR", "pieces", 30, "Shelf E-9"),
    ("Lab Reagents", "D-Dimer Test Kits", "LAB-DDM-KIT", "kits", 3, "Shelf E-10"),
    ("Lab Reagents", "Troponin I Rapid Kit", "LAB-TRP-KIT", "kits", 6, "Shelf E-11"),
    ("Lab Reagents", "CRP Latex Slide Kit", "LAB-CRP-KIT", "kits", 2, "Shelf E-12"),
    ("Lab Reagents", "Rheumatoid Factor Kit", "LAB-RF-KIT", "kits", 2, "Shelf E-13"),
    ("Lab Reagents", "Blood Culture Bottles", "LAB-BLD-CUL", "pieces", 22, "Shelf E-14"),
    ("Lab Reagents", "Malaria Antigen Kit", "LAB-MAL-KIT", "kits", 15, "Shelf E-15"),
    ("Lab Reagents", "Pipette Tips 200uL", "LAB-PIP-200", "boxes", 3, "Shelf E-16"),
    ("Lab Reagents", "Pipette Tips 1000uL", "LAB-PIP-1KW", "boxes", 2, "Shelf E-17"),
    ("Lab Reagents", "Microscope Slides", "LAB-MIC-SLD", "boxes", 5, "Shelf E-18"),
    ("Lab Reagents", "Pregnancy Test Cassette", "LAB-HCG-CAS", "pieces", 25, "Shelf E-19"),
    ("Lab Reagents", "Blood Grouping Anti-A", "LAB-BGP-ANA", "vials", 2, "Shelf E-20")
]


# --- Generate Tables ---

# 1. users.csv
users = [
    {
        "id": 1,
        "name": "Admin User",
        "email": "admin@inventory.com",
        "password_hash": "$2b$12$R.S1nQJ5827.y.o/U8a19e5n9L0X.C7Q2vJgZ0z392V3y0o5LqW6q",  # Admin@1234
        "role": "ADMIN",
        "is_active": "true",
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    },
    {
        "id": 2,
        "name": "Inventory Manager",
        "email": "manager@inventory.com",
        "password_hash": "$2b$12$K89K9G1O2T3s4n5a6B7c8DeF.GHIJKLMNoPQRSTUVWXYZ.12345678",  # Manager@1234
        "role": "INVENTORY_MANAGER",
        "is_active": "true",
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    }
]

# 2. suppliers.csv
suppliers = []
for idx, (name, company) in enumerate(SUPPLIER_NAMES):
    s_id = idx + 1
    priority = "PREFERRED" if s_id <= 3 else ("HIGH" if s_id <= 7 else ("MEDIUM" if s_id <= 12 else "LOW"))
    average_delivery_days = random.randint(3, 10)
    suppliers.append({
        "id": s_id,
        "supplier_name": name,
        "company_name": company,
        "email": f"orders@{company.lower().replace(' ', '').replace('.', '').replace(',', '')}.com",
        "phone": f"+91-98{random.randint(10, 99)}45{random.randint(1000, 9999)}",
        "address": f"{random.randint(10, 500)} Industrial Zone, Sector-{random.randint(1, 15)}, Mumbai, India",
        "preferred_contact_method": "email" if random.random() > 0.3 else "phone",
        "average_delivery_days": average_delivery_days,
        "emergency_available": "true" if random.random() > 0.4 else "false",
        "priority": priority,
        "status": "ACTIVE",
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    })

# 3. products.csv
products = []
supplier_products = []
sp_counter = 1

for idx, t in enumerate(PRODUCT_TEMPLATES):
    p_id = idx + 1
    category, name, code, unit, avg_usage, location = t
    
    # Randomly assign a primary supplier (and backup suppliers)
    primary_supplier_id = random.randint(1, len(suppliers))
    
    # Stock calculations
    # Let's start with a generous initial quantity
    min_stock = avg_usage * random.randint(5, 10)
    emergency_reserve = avg_usage * random.randint(2, 4)
    initial_qty = min_stock * 2.5
    
    products.append({
        "id": p_id,
        "product_name": name,
        "product_code": code,
        "category": category,
        "description": f"{name} - standard quality medical stock item",
        "current_quantity": initial_qty,
        "unit": unit,
        "minimum_stock": min_stock,
        "average_daily_usage": float(avg_usage),
        "alert_days": 7,
        "critical_days": 3,
        "emergency_reserve": emergency_reserve,
        "expiry_date": "",  # will compute based on batches
        "storage_location": location,
        "primary_supplier_id": primary_supplier_id,
        "status": "ACTIVE",
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    })
    
    # Generate Supplier-Product links
    # Link primary supplier
    supplier_products.append({
        "id": sp_counter,
        "supplier_id": primary_supplier_id,
        "product_id": p_id,
        "unit_price": round(random.uniform(2.0, 150.0), 2),
        "minimum_order_quantity": float(avg_usage * 15),
        "delivery_days": suppliers[primary_supplier_id - 1]["average_delivery_days"],
        "priority": 1,
        "emergency_available": suppliers[primary_supplier_id - 1]["emergency_available"],
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    })
    sp_counter += 1
    
    # Link a backup supplier
    backup_supplier_id = random.choice([s["id"] for s in suppliers if s["id"] != primary_supplier_id])
    supplier_products.append({
        "id": sp_counter,
        "supplier_id": backup_supplier_id,
        "product_id": p_id,
        "unit_price": round(supplier_products[-1]["unit_price"] * random.uniform(1.05, 1.2), 2),
        "minimum_order_quantity": float(avg_usage * 10),
        "delivery_days": max(3, suppliers[backup_supplier_id - 1]["average_delivery_days"] + random.randint(-1, 2)),
        "priority": 2,
        "emergency_available": suppliers[backup_supplier_id - 1]["emergency_available"],
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    })
    sp_counter += 1


# --- Simulate Transactions, Batches, & Purchase Orders over 365 Days ---
transactions = []
product_batches = []
purchase_orders = []
purchase_order_items = []

txn_counter = 1
batch_counter = 1
po_counter = 1
poi_counter = 1

# Dictionary to track state during simulation
# product_id -> { "current_qty": float, "pending_order": bool, "order_delivered_date": datetime, "pending_po_id": int }
prod_states = {}
for p in products:
    p_id = p["id"]
    qty = p["current_quantity"]
    prod_states[p_id] = {
        "current_qty": qty,
        "pending_order": False,
        "order_delivered_date": None,
        "pending_po_id": None,
        "batches": []  # List of dicts: {"batch_id": int, "qty": float, "expiry_date": date}
    }
    
    # Initial batch creation
    b_id = batch_counter
    batch_counter += 1
    expiry_dt = (START_DATE + timedelta(days=random.randint(180, 540))).date()
    prod_states[p_id]["batches"].append({
        "batch_id": b_id,
        "batch_number": f"BAT-{p['product_code']}-INIT",
        "qty": qty,
        "expiry_date": expiry_dt
    })
    product_batches.append({
        "id": b_id,
        "product_id": p_id,
        "batch_number": f"BAT-{p['product_code']}-INIT",
        "quantity": qty,
        "manufacturing_date": (START_DATE - timedelta(days=30)).date().isoformat(),
        "expiry_date": expiry_dt.isoformat(),
        "received_date": START_DATE.date().isoformat(),
        "created_at": START_DATE.isoformat(),
        "updated_at": START_DATE.isoformat()
    })
    
    # Initial IN transaction
    transactions.append({
        "id": txn_counter,
        "product_id": p_id,
        "transaction_type": "IN",
        "quantity": qty,
        "stock_after": qty,
        "reason": "Initial stock seeding",
        "reference_id": "SYS-INIT",
        "batch_id": b_id,
        "transaction_date": START_DATE.isoformat(),
        "created_by": 1,
        "created_at": START_DATE.isoformat()
    })
    txn_counter += 1

# Simulation Loop
print("⏳ Running daily simulation...")
for day in range(TOTAL_DAYS):
    current_date = START_DATE + timedelta(days=day)
    current_date_str = current_date.isoformat()
    
    # 1. Handle deliveries of pending orders
    for p_id, state in prod_states.items():
        if state["pending_order"] and state["order_delivered_date"] <= current_date:
            po_id = state["pending_po_id"]
            
            # Find the order items and PO
            po = next(o for o in purchase_orders if o["id"] == po_id)
            po_item = next(item for item in purchase_order_items if item["purchase_order_id"] == po_id and item["product_id"] == p_id)
            
            reorder_qty = po_item["requested_quantity"]
            
            # Update running quantity
            old_qty = state["current_qty"]
            new_qty = old_qty + reorder_qty
            state["current_qty"] = new_qty
            
            # Update PO status to DELIVERED
            po["status"] = "DELIVERED"
            po["updated_at"] = current_date_str
            po["approved_at"] = (state["order_delivered_date"] - timedelta(days=3)).isoformat()
            po_item["received_quantity"] = reorder_qty
            po_item["updated_at"] = current_date_str
            
            # Create new batch (FEFO)
            b_id = batch_counter
            batch_counter += 1
            expiry_dt = (current_date + timedelta(days=random.randint(180, 540))).date()
            batch_num = f"BAT-{products[p_id-1]['product_code']}-{po_id}"
            
            state["batches"].append({
                "batch_id": b_id,
                "batch_number": batch_num,
                "qty": reorder_qty,
                "expiry_date": expiry_dt
            })
            
            product_batches.append({
                "id": b_id,
                "product_id": p_id,
                "batch_number": batch_num,
                "quantity": reorder_qty,
                "manufacturing_date": (current_date - timedelta(days=15)).date().isoformat(),
                "expiry_date": expiry_dt.isoformat(),
                "received_date": current_date.date().isoformat(),
                "created_at": current_date_str,
                "updated_at": current_date_str
            })
            
            # Record IN Transaction
            transactions.append({
                "id": txn_counter,
                "product_id": p_id,
                "transaction_type": "IN",
                "quantity": reorder_qty,
                "stock_after": new_qty,
                "reason": f"Restock delivery (PO #{po_id})",
                "reference_id": f"PO-{po_id}",
                "batch_id": b_id,
                "transaction_date": current_date_str,
                "created_by": 2,
                "created_at": current_date_str
            })
            txn_counter += 1
            
            # Reset order state
            state["pending_order"] = False
            state["pending_po_id"] = None
            state["order_delivered_date"] = None
            
    # 2. Daily Consumption (OUT transactions)
    # To keep it realistic, not all products are consumed every single day.
    # We select a random sample of 70% of products to have consumption on any given day.
    active_products = random.sample(products, int(len(products) * 0.70))
    for p in active_products:
        p_id = p["id"]
        state = prod_states[p_id]
        
        # Calculate daily demand
        avg_use = p["average_daily_usage"]
        daily_demand = max(0, int(random.normalvariate(avg_use, avg_use * 0.2)))
        
        if daily_demand <= 0:
            continue
            
        # Consume stock (with FEFO batch allocation)
        available = state["current_qty"]
        actual_consumed = min(available, daily_demand)
        
        if actual_consumed <= 0:
            continue
            
        # Deduct from batches following FEFO
        remaining_to_deduct = actual_consumed
        state["batches"].sort(key=lambda x: x["expiry_date"])
        
        for batch in list(state["batches"]):
            if batch["qty"] >= remaining_to_deduct:
                batch["qty"] -= remaining_to_deduct
                remaining_to_deduct = 0
                break
            else:
                remaining_to_deduct -= batch["qty"]
                state["batches"].remove(batch)
                
        # Update running quantity
        old_qty = state["current_qty"]
        new_qty = old_qty - actual_consumed
        state["current_qty"] = new_qty
        
        # Record OUT Transaction
        transactions.append({
            "id": txn_counter,
            "product_id": p_id,
            "transaction_type": "OUT",
            "quantity": float(actual_consumed),
            "stock_after": new_qty,
            "reason": "Patient/Department consumption",
            "reference_id": f"TX-{current_date.strftime('%Y%m%d')}-{p_id}",
            "batch_id": state["batches"][0]["batch_id"] if state["batches"] else "",
            "transaction_date": current_date_str,
            "created_by": 2,
            "created_at": current_date_str
        })
        txn_counter += 1
        
        # 3. Check for low-stock triggers & purchase orders creation
        days_rem = new_qty / avg_use if avg_use > 0 else 999
        if days_rem <= p["alert_days"] and not state["pending_order"]:
            # Needs restock order!
            # Select primary supplier details
            sp_link = next(link for link in supplier_products if link["product_id"] == p_id and link["priority"] == 1)
            supp = suppliers[sp_link["supplier_id"] - 1]
            
            # Reorder calculation formula
            safety_buffer = 2  # settings.safety_buffer_days
            safety_stock_days = 7  # settings.safety_stock_days
            lead_time = sp_link["delivery_days"]
            
            # MOQ logic
            moq = sp_link["minimum_order_quantity"]
            desired_qty = avg_use * (lead_time + safety_stock_days + safety_buffer) - new_qty
            reorder_qty = max(moq, float(int(desired_qty)))
            
            # Create purchase order
            po_id = po_counter
            po_counter += 1
            
            delivery_days = sp_link["delivery_days"]
            required_by = current_date + timedelta(days=delivery_days)
            
            purchase_orders.append({
                "id": po_id,
                "supplier_id": supp["id"],
                "order_date": current_date_str,
                "required_by_date": required_by.isoformat(),
                "status": "APPROVED",
                "priority": "HIGH" if days_rem <= p["critical_days"] else "NORMAL",
                "total_items": 1,
                "notes": f"Auto-generated for replenishing {p['product_name']}. Days remaining: {days_rem:.1f}",
                "created_by": 2,
                "approved_by": 1,
                "approved_at": (current_date + timedelta(hours=2)).isoformat(),
                "created_at": current_date_str,
                "updated_at": current_date_str
            })
            
            purchase_order_items.append({
                "id": poi_counter,
                "purchase_order_id": po_id,
                "product_id": p_id,
                "requested_quantity": reorder_qty,
                "received_quantity": 0.0,
                "unit_price": sp_link["unit_price"],
                "created_at": current_date_str,
                "updated_at": current_date_str
            })
            poi_counter += 1
            
            # Update state to pending delivery
            state["pending_order"] = True
            state["pending_po_id"] = po_id
            state["order_delivered_date"] = required_by

    # 4. Small random events (damages, adjustments, expired batches)
    # Every 10 days, we might have a damage event for 1-2 products
    if day % 10 == 0:
        damage_prod = random.choice(products)
        state = prod_states[damage_prod["id"]]
        if state["current_qty"] > 5:
            damage_qty = random.randint(1, 3)
            old_qty = state["current_qty"]
            new_qty = old_qty - damage_qty
            state["current_qty"] = new_qty
            
            # Record DAMAGE Transaction
            transactions.append({
                "id": txn_counter,
                "product_id": damage_prod["id"],
                "transaction_type": "DAMAGE",
                "quantity": float(damage_qty),
                "stock_after": new_qty,
                "reason": "Broken container / packaging seal broken",
                "reference_id": f"DMG-{current_date.strftime('%Y%m%d')}",
                "batch_id": state["batches"][0]["batch_id"] if state["batches"] else "",
                "transaction_date": current_date_str,
                "created_by": 2,
                "created_at": current_date_str
            })
            txn_counter += 1

# Write final quantities back to product structures
for p in products:
    p_id = p["id"]
    state = prod_states[p_id]
    p["current_quantity"] = state["current_qty"]
    
    # Find next expiring batch for product
    state["batches"].sort(key=lambda x: x["expiry_date"])
    active_batches = [b for b in state["batches"] if b["qty"] > 0]
    if active_batches:
        p["expiry_date"] = active_batches[0]["expiry_date"].isoformat()
    else:
        p["expiry_date"] = ""
        
    # Update Status
    avg_use = p["average_daily_usage"]
    days_rem = state["current_qty"] / avg_use if avg_use > 0 else 999
    if state["current_qty"] == 0:
        p["status"] = "OUT_OF_STOCK"
    elif days_rem <= p["critical_days"]:
        p["status"] = "CRITICAL"
    elif days_rem <= p["alert_days"]:
        p["status"] = "LOW_STOCK"
    else:
        p["status"] = "ACTIVE"
        
    # If nearest batch expires in under 30 days
    if active_batches:
        days_to_expiry = (active_batches[0]["expiry_date"] - END_DATE.date()).days
        if 0 < days_to_expiry <= 30:
            p["status"] = "EXPIRING_SOON"
        elif days_to_expiry <= 0:
            p["status"] = "EXPIRED"


# --- Export to CSV ---

def export_csv(filename, data, fieldnames):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"  ✅ Exported {len(data)} rows to {filename}")

# 1. Users
export_csv("users.csv", users, ["id", "name", "email", "password_hash", "role", "is_active", "created_at", "updated_at"])

# 2. Suppliers
export_csv("suppliers.csv", suppliers, [
    "id", "supplier_name", "company_name", "email", "phone", "address",
    "preferred_contact_method", "average_delivery_days", "emergency_available",
    "priority", "status", "created_at", "updated_at"
])

# 3. Products
export_csv("products.csv", products, [
    "id", "product_name", "product_code", "category", "description",
    "current_quantity", "unit", "minimum_stock", "average_daily_usage",
    "alert_days", "critical_days", "emergency_reserve", "expiry_date",
    "storage_location", "primary_supplier_id", "status", "created_at", "updated_at"
])

# 4. Supplier Products Link
export_csv("supplier_products.csv", supplier_products, [
    "id", "supplier_id", "product_id", "unit_price", "minimum_order_quantity",
    "delivery_days", "priority", "emergency_available", "created_at", "updated_at"
])

# 5. Product Batches
export_csv("product_batches.csv", product_batches, [
    "id", "product_id", "batch_number", "quantity", "manufacturing_date",
    "expiry_date", "received_date", "created_at", "updated_at"
])

# 6. Inventory Transactions (Target: 5000+)
export_csv("inventory_transactions.csv", transactions, [
    "id", "product_id", "transaction_type", "quantity", "stock_after",
    "reason", "reference_id", "batch_id", "transaction_date", "created_by", "created_at"
])

# 7. Purchase Orders
export_csv("purchase_orders.csv", purchase_orders, [
    "id", "supplier_id", "order_date", "required_by_date", "status", "priority",
    "total_items", "notes", "created_by", "approved_by", "approved_at", "created_at", "updated_at"
])

# 8. Purchase Order Items
export_csv("purchase_order_items.csv", purchase_order_items, [
    "id", "purchase_order_id", "product_id", "requested_quantity", "received_quantity",
    "unit_price", "created_at", "updated_at"
])

print("\n✨ CSV Dataset generation complete!")
