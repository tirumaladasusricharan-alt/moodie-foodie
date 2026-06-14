import json, sys, random
sys.path.insert(0, r'c:\Users\DELL\Desktop\moodie')
from food_data import FOOD_DATABASE

# Remove ALL Indian items - we'll replace them with curated ones
non_indian = [f for f in FOOD_DATABASE if f['cuisine'] != 'Indian']
print(f"Kept {len(non_indian)} non-Indian items")

MOODS_ALL = ['Happy','Sad','Stressed','Angry','Excited','Bored','Anxious','Romantic']

def make(name, diet, cat, heavy, times, moods):
    return {"name":name,"cuisine":"Indian","diet":diet,"category":cat,
            "moods":moods,"is_heavy":heavy,"suitable_times":times}

random.seed(42)
indian_dict = {}

def add_item(name, diet, cat, heavy, times, moods):
    if name not in indian_dict:
        indian_dict[name] = make(name, diet, cat, heavy, times, moods)

# Mood Groups for intentional mapping
M_HAPPY = ['Happy', 'Excited', 'Romantic']
M_SAD = ['Sad', 'Bored', 'Anxious']
M_STRESSED = ['Stressed', 'Angry', 'Anxious']
M_INTENSE = ['Angry', 'Excited']
M_COZY = ['Romantic', 'Sad', 'Bored']
M_CELEBRATE = ['Happy', 'Excited']

# === MORNING TIFFINS (STRICTLY MORNING) ===
morning_data = [
    ("Mysore Bonda", "Vegetarian", "comfort", True, M_HAPPY + ['Bored']),
    ("Aloo Poori", "Vegetarian", "comfort", True, M_HAPPY + ['Sad']),
    ("Chole Puri", "Vegetarian", "comfort", True, M_HAPPY + ['Angry']),
    ("Masala Dosa", "Vegetarian", "comfort", True, M_HAPPY + ['Stressed']),
    ("Plain Dosa", "Vegetarian", "veg", False, ['Happy', 'Bored']),
    ("Rava Dosa", "Vegetarian", "veg", False, ['Excited', 'Anxious']),
    ("Idli with Sambar", "Vegetarian", "veg", False, ['Sad', 'Anxious', 'Happy']),
    ("Vada with Sambar", "Vegetarian", "veg", False, ['Happy', 'Excited']),
    ("Rava Idli", "Vegetarian", "veg", False, ['Happy', 'Bored']),
    ("Thatte Idli", "Vegetarian", "veg", False, M_CELEBRATE),
    ("Khaman Dhokla", "Vegetarian", "veg", False, ['Happy', 'Excited', 'Romantic']),
    ("Poha", "Vegetarian", "veg", False, ['Anxious', 'Bored', 'Happy']),
    ("Upma", "Vegetarian", "veg", False, ['Anxious', 'Sad']),
    ("Set Dosa", "Vegetarian", "veg", False, ['Happy', 'Bored']),
    ("Appam with Stew", "Vegetarian", "veg", True, ['Romantic', 'Sad']),
]
for name, diet, cat, heavy, moods in morning_data:
    add_item(name, diet, cat, heavy, ["Morning"], moods)

# === STREET FOOD & SNACKS (STRICTLY EVENING) ===
evening_data = [
    ("Pani Puri", "Vegetarian", M_HAPPY + ['Bored']),
    ("Sev Puri", "Vegetarian", M_HAPPY + ['Excited']),
    ("Dahi Puri", "Vegetarian", ['Happy', 'Sad', 'Romantic']),
    ("Samosa", "Vegetarian", ['Happy', 'Stressed', 'Bored']),
    ("Vada Pav", "Vegetarian", ['Happy', 'Angry', 'Excited']),
    ("Pav Bhaji", "Vegetarian", ['Happy', 'Sad', 'Excited']),
    ("Gobi Manchurian", "Vegetarian", ['Angry', 'Excited', 'Bored']),
    ("Chicken 65", "Non-Vegetarian", ['Angry', 'Excited', 'Stressed']),
    ("Mirchi Bajji", "Vegetarian", ['Angry', 'Excited', 'Anxious']),
    ("Chilli Bajji", "Vegetarian", ['Angry', 'Excited', 'Anxious']),
    ("Maddur Vada", "Vegetarian", ['Bored', 'Happy', 'Romantic']),
    ("Masala Puri", "Vegetarian", ['Happy', 'Sad', 'Excited']),
    ("Momos", "Vegetarian", ['Happy', 'Bored', 'Romantic']),
    ("Spring Rolls", "Vegetarian", ['Excited', 'Happy']),
    ("Egg Puff", "Non-Vegetarian", ['Stressed', 'Bored']),
    ("Chicken Puff", "Non-Vegetarian", ['Stressed', 'Bored']),
    ("Bhel Puri", "Vegetarian", ['Bored', 'Happy']),
]
for name, diet, moods in evening_data:
    add_item(name, diet, "adventurous", False, ["Evening"], moods)

# === HEAVY MAIN COURSE (STRICTLY AFTERNOON & NIGHT) ===
mains_data = [
    ("Chicken Biryani", "Non-Vegetarian", M_HAPPY + ['Sad', 'Excited']),
    ("Hyderabadi Biryani", "Non-Vegetarian", M_HAPPY + ['Angry', 'Excited']),
    ("Mutton Biryani", "Non-Vegetarian", M_HAPPY + ['Excited']),
    ("Veg Biryani", "Vegetarian", M_HAPPY + ['Bored']),
    ("Butter Chicken", "Non-Vegetarian", ['Sad', 'Romantic', 'Happy']),
    ("Paneer Butter Masala", "Vegetarian", ['Sad', 'Romantic', 'Happy']),
    ("Chilli Paneer", "Vegetarian", ['Angry', 'Excited', 'Stressed']),
    ("Chilli Chicken", "Non-Vegetarian", ['Angry', 'Excited', 'Stressed']),
    ("Dal Makhani", "Vegetarian", ['Sad', 'Stressed', 'Happy']),
    ("Chole Chawal", "Vegetarian", ['Happy', 'Bored', 'Anxious']),
    ("Rajma Chawal", "Vegetarian", ['Anxious', 'Sad', 'Happy']),
    ("Kadai Paneer", "Vegetarian", ['Angry', 'Excited']),
    ("Chicken Tikka Masala", "Non-Vegetarian", ['Happy', 'Excited', 'Romantic']),
    ("Dal Tadka", "Vegetarian", ['Sad', 'Anxious']),
    ("Jeera Rice", "Vegetarian", ['Bored', 'Anxious']),
]
for name, diet, moods in mains_data:
    add_item(name, diet, "comfort", True, ["Afternoon", "Night"], moods)

# === SWEETS & BEVERAGES (ANYTIME) ===
anytime_data = [
    ("Gulab Jamun", "Vegetarian", "comfort", False, M_HAPPY + ['Sad']),
    ("Rasmalai", "Vegetarian", "comfort", False, M_HAPPY + ['Romantic']),
    ("Jalebi", "Vegetarian", "comfort", False, M_HAPPY + ['Excited']),
    ("Jalebi with Rabri", "Vegetarian", "comfort", True, M_HAPPY + ['Excited']),
    ("Masala Chai", "Vegetarian", "veg", False, ['Stressed', 'Angry', 'Sad']),
    ("Filter Coffee", "Vegetarian", "veg", False, ['Stressed', 'Bored', 'Anxious']),
]
for name, diet, cat, heavy, moods in anytime_data:
    add_item(name, diet, cat, heavy, ["Morning", "Afternoon", "Evening", "Night"], moods)

# Add remaining items with random but sensible moods
for food in FOOD_DATABASE:
    if food['cuisine'] == 'Indian' and food['name'] not in indian_dict:
        m = random.sample(MOODS_ALL, 3)
        add_item(food['name'], food['diet'], food['category'], food['is_heavy'], food['suitable_times'], m)

indian = list(indian_dict.values())
all_foods = non_indian + indian
print(f"New Indian items added: {len(indian)}")

with open(r'c:\Users\DELL\Desktop\moodie\food_data.py', 'w', encoding='utf-8') as f:
    f.write("FOOD_DATABASE = [\n")
    for i, food in enumerate(all_foods):
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
        if i < len(all_foods) - 1:
            f.write(",")
        f.write("\n")
    f.write("]\n")
print("[OK] food_data.py rewritten successfully!")
