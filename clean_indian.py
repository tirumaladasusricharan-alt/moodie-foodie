"""Step 1: Remove garbage Indian food combinations and duplicates."""
import json, sys
sys.path.insert(0, r'c:\Users\DELL\Desktop\moodie')
from food_data import FOOD_DATABASE

# Nonsense patterns to remove
GARBAGE = [
    'Tofu Pani Puri', 'Tofu Mild Pani Puri', 'Tofu Bhel Puri', 'Tofu Biryani',
    'Tofu Butter Pakora', 'Tofu Garlic Malai Kofta', 'Tofu Kadhi Pakora',
    'Tofu Misal Pav', 'Tofu Moong Dal Chilla', 'Tofu Samosa', 'Tofu Spicy Momo',
    'Tofu Tandoori Bhindi Masala', 'Tofu Upma', 'Tofu Aloo Paratha',
    'Veg Mutton Biryani', 'Fish Dhokla', 'Mutton Dhokla', 'Chicken Dhokla',
    'Chicken Pani Puri', 'Chicken Sev Puri', 'Chicken Bhel Puri',
    'Fish Bhel Puri', 'Fish Misal Pav', 'Fish Home-style Misal Pav',
    'Fish Sabudana Khichdi', 'Fish Masala Dosa', 'Fish Mild Neer Dosa',
    'Fish Mild Pav Bhaji', 'Fish Special Rava Bhidi', 'Fish Spicy Rava Bhidi',
    'Fish Tandoori Bhel Puri', 'Fish Tandoori Navratan Korma',
    'Chicken Sabudana Khichdi', 'Chicken Spicy Sabudana Khichdi',
    'Chicken Spicy Upma', 'Chicken Mild Idli with Sambar',
    'Chicken Garlic Dal Makhani', 'Chicken Garlic Kadhi Pakora',
    'Chicken Classic Methi Thepla', 'Chicken Tandoori Dal Makhani',
    'Chicken Tandoori Aloo Paratha', 'Chicken Navratan Korma',
    'Chicken Bhindi Masala', 'Mutton Butter Bhindi Masala',
    'Mutton Misal Pav', 'Mutton Pav Bhaji', 'Mutton Dhokla',
    'Mutton Garlic Appam', 'Mutton Special Upma', 'Mutton Spicy Poha',
    'Mutton Spicy Chole Chawal', 'Mutton Spicy Vada Pav', 'Mutton Spicy Pakora',
    'Mushroom Classic Mutton Rogan Josh', 'Mushroom Home-style Mutton Rogan Josh',
    'Mushroom Mutton Biryani', 'Mushroom Spicy Dahi Vada',
    'Mushroom Spicy Navratan Korma', 'Mushroom Spicy Idli with Sambar',
    'Mushroom Special Dahi Vada', 'Mushroom Special Methi Thepla',
    'Mushroom Special Akki Rotti', 'Mushroom Butter Poha',
    'Mushroom Classic Pav Bhaji', 'Paneer Mutton Biryani',
    'Paneer Home-style Misal Pav', 'Paneer Home-style Upma',
    'Paneer Mild Navratan Korma', 'Prawn Aloo Gobi', 'Prawn Chole Chawal',
    'Prawn Dal Makhani', 'Prawn Fish Curry', 'Prawn Home-style Methi Thepla',
    'Prawn Mild Masala Dosa', 'Prawn Mild Sabudana Khichdi', 'Prawn Rajma Chawal',
    'Prawn Adai', 'Prawn Butter Rava Bhidi',
    'Egg Aloo Gobi', 'Egg Home-style Laal Maas', 'Egg Laal Maas',
    'Egg Mild Bhindi Masala', 'Egg Special Aloo Tikki', 'Egg Spicy Aloo Paratha',
    'Egg Spicy Moong Dal Chilla', 'Egg Butter Methi Thepla',
    'Fish Bhindi Masala', 'Fish Classic Bhindi Masala', 'Fish Classic Egg Curry',
    'Fish Kadhi Pakora', 'Fish Garlic Pakora', 'Fish Goan Prawn Curry',
    'Fish Tandoori Pakora', 'Garlic Goan Prawn Curry',
    'Veg Butter Chole Chawal', 'Veg Butter Sabudana Khichdi',
    'Veg Classic Pakora', 'Veg Dahi Vada', 'Veg Garlic Malai Kofta',
    'Veg Pani Puri', 'Veg Rajma Chawal', 'Veg Rava Bhidi', 'Veg Akki Rotti',
    'Veg Appam', 'Vegetable Hunan Sweet and Sour Pork',
    'Tandoori Poha', 'Tandoori Neer Dosa', 'Tandoori Puttu',
    'Tandoori Misal Pav', 'Tandoori Aloo Gobi', 'Tandoori Aloo Tikki',
    'Tandoori Baingan Bharta', 'Tandoori Bhindi Masala',
    'Tandoori Chole Bhature', 'Tandoori Dal Makhani',
    'Tandoori Navratan Korma', 'Tandoori Rajma Chawal',
    'Tandoori Palak Paneer', 'Tandoori Paneer Paratha',
    'Butter Butter Chicken', 'Garlic Rava Bhidi',
]

garbage_set = set(GARBAGE)

# Remove garbage and deduplicate Indian items
seen_indian = set()
cleaned = []
removed = 0

for food in FOOD_DATABASE:
    if food['cuisine'] == 'Indian':
        if food['name'] in garbage_set:
            removed += 1
            continue
        key = (food['name'], food['category'], food['diet'])
        if key in seen_indian:
            removed += 1
            continue
        seen_indian.add(key)
    cleaned.append(food)

print(f"Removed {removed} garbage/duplicate Indian items")
print(f"Remaining: {len(cleaned)} total items")
print(f"Indian items remaining: {sum(1 for f in cleaned if f['cuisine']=='Indian')}")

# Write back
with open(r'c:\Users\DELL\Desktop\moodie\food_data.py', 'w', encoding='utf-8') as f:
    f.write("FOOD_DATABASE = [\n")
    for i, food in enumerate(cleaned):
        f.write("    {\n")
        f.write(f'        "name": {json.dumps(food["name"])},\n')
        f.write(f'        "cuisine": {json.dumps(food["cuisine"])},\n')
        f.write(f'        "diet": {json.dumps(food["diet"])},\n')
        f.write(f'        "category": {json.dumps(food["category"])},\n')
        f.write(f'        "moods": {json.dumps(food["moods"])},\n')
        hvy = "True" if food["is_heavy"] else "False"
        f.write(f'        "is_heavy": {hvy},\n')
        f.write(f'        "suitable_times": {json.dumps(food["suitable_times"])}\n')
        f.write("    }")
        if i < len(cleaned) - 1:
            f.write(",")
        f.write("\n")
    f.write("]\n")

print("[OK] Cleaned food_data.py written.")
