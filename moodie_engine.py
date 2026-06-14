"""
Moodie Engine — ML-powered food recommendation system.

Uses a RandomForestClassifier trained on synthetic mood + personality data
to recommend foods. The pipeline handles encoding and scaling automatically.
"""
import os
import random
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import sys

def get_path(filename, persistent=False):
    """
    If persistent=True, returns path next to the EXE (for saving DB/Models).
    If persistent=False, returns path inside the bundle (for templates/static).
    """
    if getattr(sys, 'frozen', False):
        if persistent:
            # Next to the actual .exe
            base = os.path.dirname(sys.executable)
        else:
            # Inside the temp _MEIPASS folder
            base = sys._MEIPASS
    else:
        base = os.path.abspath(".")
    return os.path.join(base, filename)

MODEL_PATH = get_path('moodie_model.pkl', persistent=True)
LABEL_PATH = get_path('moodie_labels.pkl', persistent=True)

# Internal fallback if persistent ones don't exist yet
BUN_MODEL = get_path('moodie_model.pkl', persistent=False)
BUN_LABEL = get_path('moodie_labels.pkl', persistent=False)

# ─── Food Mapping ──────────────────────────────────────────────
# foods are now mapped as: mood -> category -> cuisine -> [foods]
from food_data import FOOD_DATABASE


PERSONALITIES = ['Introvert', 'Extrovert', 'Ambivert', 'Adventurous', 'Calm']
DIETS = ['Vegetarian', 'Non-Vegetarian', 'Vegan', 'Eggetarian']
CUISINES = ['Indian', 'Chinese', 'Italian', 'Mexican', 'Continental', 'Japanese']
MOODS = ['Happy', 'Sad', 'Stressed', 'Angry', 'Excited', 'Bored', 'Anxious', 'Romantic']
TIMES = ['Morning', 'Afternoon', 'Evening', 'Night']
WEATHERS = ['Hot', 'Cold', 'Rainy', 'Pleasant']

DRINKS = {
    'Sweet': ['Mango Lassi', 'Cold Coffee', 'Milkshake', 'Hot Chocolate', 'Fruit Juice', 'Soda', 'Boba Tea'],
    'Non-Sweet': ['Fresh Lime Soda', 'Buttermilk', 'Green Tea', 'Black Coffee', 'Iced Tea', 'Sparkling Water', 'Coconut Water']
}

SWEET_KEYWORDS = [
    'halwa', 'rasgulla', 'katli', 'pak', 'shrikhand', 'phirni', 'jalebi', 'jamun', 
    'laddu', 'barfi', 'peda', 'kheer', 'rasmalai', 'malpua', 'rabri', 'ghevar', 
    'sandesh', 'mishti', 'cake', 'brownie', 'pie', 'fondue', 'ice cream', 'sorbet', 
    'donut', 'pastry', 'cookie', 'muffin', 'pudding', 'tart', 'cheesecake', 
    'soufflé', 'mousse', 'trifle', 'custard', 'churros', 'conchas', 'mochi', 'taiyaki',
    'sweet', 'dessert', 'candy', 'chocolate'
]

SPICY_KEYWORDS = [
    'spicy', 'mirchi', 'chilli', 'chili', 'kolhapuri', 'andhra', 'chettinad', 
    'szechuan', 'schezwan', 'kung pao', 'hot', 'peri peri', 'jalapeno', 
    'wasabi', 'teekha', 'jalfrezi', 'vindaloo', 'madras', 'peppery', 'fire'
]

CATEGORICAL_FEATURES = ['personality', 'diet_type', 'cuisine_pref', 'mood', 'time_of_day', 'weather']
NUMERICAL_FEATURES = ['age', 'spice_level', 'sweet_tooth', 'health_conscious', 'mood_intensity']


def _pick_food_category(personality, diet_type, health_conscious, spice_level, mood):
    """Determine the best food category for a user based on their profile."""
    if diet_type == 'Vegan':
        return 'vegan'
    if diet_type == 'Vegetarian':
        return 'veg'
    if health_conscious:
        return 'healthy'
    if personality == 'Adventurous' or (personality == 'Extrovert' and spice_level >= 4):
        return 'adventurous'
    return 'comfort'


def _select_food(mood, personality, diet_type, health_conscious, spice_level, sweet_tooth, cuisine_pref, age, time_of_day):
    """Select a specific food item from the database using probability weighting."""
    category = _pick_food_category(personality, diet_type, health_conscious, spice_level, mood)
    
    eligible_foods = []
    weights = []
    
    for food in FOOD_DATABASE:
        # 1. Cuisine Filter
        if food['cuisine'] != cuisine_pref:
            continue
            
        # 2. Mood Filter (check if mood is in the list of moods for this food)
        if mood not in food['moods']:
            continue
            
        # 3. Category Filter
        if food['category'] != category:
            continue
            
        # 4. Diet Filter
        if diet_type == 'Vegan' and food['diet'] != 'Vegan':
            continue
        if diet_type == 'Vegetarian' and food['diet'] not in ['Vegetarian', 'Vegan']:
            continue
            
        # Add to candidates
        eligible_foods.append(food['name'])
        
        # 5. Weighting Logic (the "Intelligence")
        weight = 1.0
        
        # Heavy Food Penalty for Morning/Evening
        if time_of_day in ['Morning', 'Evening'] and food['is_heavy']:
            weight *= 0.1  # 10x less likely
            
        # Age-based Heavy Food Penalty (Threshold 35+)
        if age >= 35 and food['is_heavy']:
            weight *= 0.1  # 10x less likely
            
        # Time Affinity - STRICT enforcement for defined times
        if food['suitable_times']:
            if time_of_day in food['suitable_times']:
                weight *= 50.0  # 50x more likely if it's the right time
            else:
                weight *= 0.01  # 100x less likely if it's the wrong time
            
        # 6. Sweet Level Penalty
        is_sweet = any(k in food['name'].lower() for k in SWEET_KEYWORDS)
        if is_sweet:
            if sweet_tooth <= 1:
                weight *= 0.0  # Blocked
            elif sweet_tooth == 2:
                weight *= 0.05 # 20x less likely
            elif sweet_tooth >= 4:
                weight *= 2.0  # 2x more likely
                
        # 7. Spice Level Penalty
        is_spicy = any(k in food['name'].lower() for k in SPICY_KEYWORDS)
        if is_spicy:
            if spice_level <= 1:
                weight *= 0.0  # Blocked
            elif spice_level == 2:
                weight *= 0.1  # 10x less likely
            elif spice_level >= 4:
                weight *= 3.0  # 3x more likely
                
        weights.append(weight)
        
    if not eligible_foods:
        # Broaden search if nothing found
        return "Special Stir-fry" if cuisine_pref == 'Chinese' else "Classic Dish"
        
    return random.choices(eligible_foods, weights=weights, k=1)[0]


def _get_all_foods_for_cuisine(cuisine_pref):
    """Crawler to get all unique food names for a specific cuisine from the database."""
    valid_foods = set()
    for food in FOOD_DATABASE:
        if food['cuisine'] == cuisine_pref:
            valid_foods.add(food['name'])
    return list(valid_foods)



def _get_food_price(food_name):
    """Generate a consistent, realistic INR price for a food based on its name."""
    # Use sum of ascii values to generate a deterministic price between ₹150 and ₹950
    name_val = sum(ord(c) for c in food_name)
    base_price = 150 + (name_val % 80) * 10
    return int(base_price)

def _get_food_emoji(food_name):
    """Return a consistent emoji sticker for the food."""
    name = food_name.lower()
    if any(k in name for k in ['pizza', 'margherita']): return '🍕'
    if any(k in name for k in ['burger', 'vada pav']): return '🍔'
    if any(k in name for k in ['sushi', 'poke']): return '🍣'
    if any(k in name for k in ['noodles', 'ramen', 'pad thai', 'chowmein']): return '🍜'
    if any(k in name for k in ['chicken', 'wings', 'nuggets']): return '🍗'
    if any(k in name for k in ['taco', 'burrito', 'wrap', 'shawarma']): return '🌮'
    if any(k in name for k in ['salad', 'bowl', 'veggie']): return '🥗'
    if any(k in name for k in ['soup', 'pho']): return '🍲'
    if any(k in name for k in ['cake', 'brownie', 'pie', 'fondue']): return '🍰'
    if any(k in name for k in ['ice cream', 'sorbet']): return '🍦'
    if any(k in name for k in ['curry', 'masala', 'dal', 'chole', 'rajma']): return '🍛'
    if any(k in name for k in ['rice', 'biryani']): return '🍚'
    if any(k in name for k in ['bread', 'naan', 'toast', 'sandwich']): return '🍞'
    if any(k in name for k in ['fries', 'nachos', 'chips', 'popcorn']): return '🍟'
    if any(k in name for k in ['pasta', 'mac & cheese', 'risotto']): return '🍝'
    return '🥘'


class MoodieEngine:
    """ML-powered food recommendation engine."""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.is_trained = False
        self._try_load()

    def _try_load(self):
        """Try to load a previously trained model."""
        # 1. Try persistent path first (user-updated model)
        if os.path.exists(MODEL_PATH) and os.path.exists(LABEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.label_encoder = joblib.load(LABEL_PATH)
                self.is_trained = True
                print("[OK] Loaded pre-trained model from disk.")
                return
            except Exception: pass
        
        # 2. Try bundled fallback
        if os.path.exists(BUN_MODEL) and os.path.exists(BUN_LABEL):
            try:
                self.model = joblib.load(BUN_MODEL)
                self.label_encoder = joblib.load(BUN_LABEL)
                self.is_trained = True
                print("[OK] Loaded bundled fallback model.")
                # Save it to persistent path so we don't have to fallback again
                joblib.dump(self.model, MODEL_PATH, compress=3)
                joblib.dump(self.label_encoder, LABEL_PATH)
            except Exception:
                print("[INFO] No model found. Need training.")
                self.is_trained = False
        else:
            print("[INFO] No model found. Need training.")
            self.is_trained = False

    def generate_synthetic_data(self, n_samples=10000):
        """Generate synthetic training data and train the model."""
        print("[INFO] Generating synthetic training data...")
        rows = []
        for _ in range(n_samples):
            age = random.randint(15, 65)
            personality = random.choice(PERSONALITIES)
            diet_type = random.choice(DIETS)
            spice_level = random.randint(0, 5)
            sweet_tooth = random.randint(0, 5)
            cuisine_pref = random.choice(CUISINES)
            health_conscious = random.choice([0, 1])
            mood = random.choice(MOODS)
            mood_intensity = random.randint(1, 5)
            time_of_day = random.choice(TIMES)
            weather = random.choice(WEATHERS)

            food = _select_food(mood, personality, diet_type, health_conscious, spice_level, sweet_tooth, cuisine_pref, age, time_of_day)

            rows.append({
                'age': age,
                'personality': personality,
                'diet_type': diet_type,
                'spice_level': spice_level,
                'sweet_tooth': sweet_tooth,
                'cuisine_pref': cuisine_pref,
                'health_conscious': health_conscious,
                'mood': mood,
                'mood_intensity': mood_intensity,
                'time_of_day': time_of_day,
                'weather': weather,
                'recommended_food': food,
            })

        df = pd.DataFrame(rows)
        self._train(df)

    def _train(self, df):
        """Train the RandomForest pipeline on the dataframe."""
        print("[INFO] Training ML model...")
        X = df.drop('recommended_food', axis=1)
        y = df['recommended_food']

        # Encode target labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        # Build preprocessing + model pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
                ('num', StandardScaler(), NUMERICAL_FEATURES),
            ]
        )

        self.model = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=50,
                max_depth=12,
                min_samples_split=10,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            ))
        ])

        # Train-test split for validation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"[OK] Model trained - Accuracy: {acc:.2%}")

        # Save
        joblib.dump(self.model, MODEL_PATH, compress=3)
        joblib.dump(self.label_encoder, LABEL_PATH)
        self.is_trained = True
        print("[OK] Model saved to disk.")

    def predict(self, user_profile: dict, avoid_foods: list = None, prefer_foods: list = None) -> dict:
        """
        Predict food recommendations for a user.

        Parameters
        ----------
        user_profile : dict with keys:
            age, personality, diet_type, spice_level, sweet_tooth,
            cuisine_pref, health_conscious, mood, mood_intensity,
            time_of_day, weather
        avoid_foods : list of food names to penalize (1-4 star rated)
        prefer_foods : list of food names to prioritize (5-star rated)

        Returns
        -------
        dict with 'primary', 'alternatives' (list), 'drink', 'category'
        """
        if avoid_foods is None:
            avoid_foods = []
        if prefer_foods is None:
            prefer_foods = []

        input_df = pd.DataFrame([{
            'age': user_profile.get('age', 25),
            'personality': user_profile.get('personality', 'Ambivert'),
            'diet_type': user_profile.get('diet_type', 'Non-Vegetarian'),
            'spice_level': user_profile.get('spice_level', 3),
            'sweet_tooth': user_profile.get('sweet_tooth', 3),
            'cuisine_pref': user_profile.get('cuisine_pref', 'Indian'),
            'health_conscious': user_profile.get('health_conscious', 0),
            'mood': user_profile.get('mood', 'Happy'),
            'mood_intensity': user_profile.get('mood_intensity', 3),
            'time_of_day': user_profile.get('time_of_day', 'Afternoon'),
            'weather': user_profile.get('weather', 'Pleasant'),
        }])

        # Get probability distribution for top-N predictions
        probas = self.model.predict_proba(input_df)[0]
        classifier_classes = self.model.named_steps['classifier'].classes_
        
        # Apply temperature scaling to increase confidence sharpness
        temperature = 0.4 
        logits = np.log(probas + 1e-10)
        
        # Create a mapping from food name to index in the probas/logits array
        # This is critical because the classifier might only know a subset of all possible foods
        food_to_idx = {}
        idx_to_food = {}
        for i, class_idx in enumerate(classifier_classes):
            food_name = self.label_encoder.inverse_transform([class_idx])[0]
            food_to_idx[food_name] = i
            idx_to_food[i] = food_name

        # 1. Penalize avoided foods (1-4 stars)
        for food_name in avoid_foods:
            if food_name in food_to_idx:
                logits[food_to_idx[food_name]] -= 20.0 # Extreme penalty
        
        # 2. Boost preferred foods (5 stars)
        for food_name in prefer_foods:
            if food_name in food_to_idx:
                logits[food_to_idx[food_name]] += 20.0 # Extreme bonus
        
        scaled_logits = logits / temperature
        # Subtract max for numerical stability
        scaled_logits -= np.max(scaled_logits)
        exp_logits = np.exp(scaled_logits)
        probas = exp_logits / np.sum(exp_logits)

        # Extract key profile parameters
        sweet_tooth = user_profile.get('sweet_tooth', 3)
        spice_level = user_profile.get('spice_level', 3)
        allergies_str = user_profile.get('allergies', '')
        allergy_list = [a.strip().lower() for a in allergies_str.split(',')] if allergies_str else []

        # 3. Aggressive Prob adjustment for Sweet Tooth (Post-scaling)
        sweet_tooth = user_profile.get('sweet_tooth', 3)
        if sweet_tooth <= 2:
            for i in range(len(probas)):
                food_name = idx_to_food[i]
                if any(k in food_name.lower() for k in SWEET_KEYWORDS):
                    if sweet_tooth <= 1:
                        probas[i] = 0.0 # Hard Block
                    else:
                        probas[i] *= 0.1 # 10x reduction
            
            # Renormalize probas
            if np.sum(probas) > 0:
                probas /= np.sum(probas)

        # Renormalize probas
        if np.sum(probas) > 0:
            probas /= np.sum(probas)

        # 4. Aggressive Prob adjustment for Spice Level
        if spice_level <= 2 or spice_level >= 4:
            for i in range(len(probas)):
                food_name = idx_to_food[i]
                is_spicy = any(k in food_name.lower() for k in SPICY_KEYWORDS)
                if is_spicy:
                    if spice_level <= 1:
                        probas[i] = 0.0 # Hard Block
                    elif spice_level == 2:
                        probas[i] *= 0.1 # 10x reduction
                    elif spice_level >= 4:
                        probas[i] *= 5.0 # 5x Boost
                elif spice_level >= 4:
                    # If high spice level, slightly penalize non-spicy foods to favor spicy ones
                    probas[i] *= 0.5
            
            # Renormalize probas
            if np.sum(probas) > 0:
                probas /= np.sum(probas)

        # 5. Questionnaire and Reflection Adjustments (The "Deep Personalization")
        q = user_profile.get('questionnaire', {})
        food_goal = user_profile.get('food_goal', 'Match my mood')

        for i in range(len(probas)):
            food_name = idx_to_food[i].lower()
            weight_adj = 1.0

            # Match or Change Mood
            if food_goal == 'Change my mood':
                # If they want to change mood, nudge them away from the most "mood-locked" foods 
                # or just add a bit of randomness/diversity
                weight_adj *= 1.2
            
            # Flavor Profile Nudge (Q4)
            q4 = q.get('q4', '')
            if 'Sweet' in q4 and any(k in food_name for k in SWEET_KEYWORDS):
                weight_adj *= 1.5
            elif 'Savory' in q4 and not any(k in food_name for k in SWEET_KEYWORDS):
                weight_adj *= 1.2

            # Weekend Vibe Nudge (Q13)
            q13 = q.get('q13', '')
            if 'Brunch' in q13 and any(k in food_name for k in ['egg', 'toast', 'pancake', 'waffle', 'paratha']):
                weight_adj *= 1.4
            
            # Drink Pairings (Q15)
            q15 = q.get('q15', '')
            # (Note: This mostly affects the 'drink' returned at the end, but can nudge food too)

            probas[i] *= weight_adj

        # Final renormalization
        if np.sum(probas) > 0:
            probas /= np.sum(probas)

        # Get sorted indices based on modified probabilities
        top_indices_in_probas = np.argsort(probas)[::-1]
        top_foods_all = [idx_to_food[i] for i in top_indices_in_probas]

        # Filter out foods based on allergies and CUISINE
        cuisine_pref = user_profile.get('cuisine_pref', 'Indian')
        valid_cuisine_foods = _get_all_foods_for_cuisine(cuisine_pref)
        
        allergies_str = user_profile.get('allergies', '')
        allergy_list = [a.strip().lower() for a in allergies_str.split(',')] if allergies_str else []

        filtered_top_indices = []
        filtered_top_foods = []
        
        # Normalize avoid/prefer lists for robust comparison
        avoid_foods_normalized = [f.strip().lower() for f in avoid_foods if f]
        prefer_foods_normalized = [f.strip().lower() for f in prefer_foods if f]
        
        # Get the food database as a name-to-info map for quick lookup
        food_lookup = {f['name']: f for f in FOOD_DATABASE}
        
        for idx, food_name in zip(top_indices_in_probas, top_foods_all):
            # 0. HARD FILTER: Avoid foods with 1-4 star ratings
            # UNLESS they were also rated 5 stars (Last rating wins)
            if food_name.strip().lower() in avoid_foods_normalized:
                if food_name.strip().lower() not in prefer_foods_normalized:
                    continue
                
            # 1. Check if food exists in our database (it should)
            food_info = food_lookup.get(food_name)
            if not food_info:
                continue
                
            # 2. STRICT TIME FILTER: Ensure the food is suitable for this time of day
            time_of_day = user_profile.get('time_of_day', 'Afternoon')
            if food_info['suitable_times'] and time_of_day not in food_info['suitable_times']:
                continue

            # 3. Cuisine Filter
            cuisine_pref = user_profile.get('cuisine_pref', 'Indian')
            if food_info['cuisine'] != cuisine_pref:
                continue
            
            # 4. Allergy Filter
            has_allergy = any(allergy in food_name.lower() for allergy in allergy_list if allergy)
            if has_allergy:
                continue

            # 5. AGGRESSIVE AVOIDANCE CHECK (Double check)
            # Ensure 1-4 star foods are NEVER shown unless they were later rated 5 stars
            fn_clean = food_name.strip().lower()
            if fn_clean in avoid_foods_normalized:
                if fn_clean not in prefer_foods_normalized:
                    # print(f"[DEBUG] Blocking avoided food: {food_name}")
                    continue

            # If all checks pass, add to our list
            
            # 6. STRICT LEVEL FILTER (Double check for Zero tolerance)
            is_sweet = any(k in food_name.lower() for k in SWEET_KEYWORDS)
            is_spicy = any(k in food_name.lower() for k in SPICY_KEYWORDS)
            
            if sweet_tooth <= 1 and is_sweet:
                continue
            if spice_level <= 1 and is_spicy:
                continue

            filtered_top_indices.append(idx)
            filtered_top_foods.append(food_name)
            if len(filtered_top_foods) >= 10:
                break
        
        # Fallback if somehow all foods are filtered out
        if not filtered_top_foods:
            # Last resort: Just find any food in the database that fits the cuisine and doesn't violate sweet/spicy/allergy
            for f in FOOD_DATABASE:
                if f['cuisine'] == cuisine_pref:
                    is_sweet = any(k in f['name'].lower() for k in SWEET_KEYWORDS)
                    is_spicy = any(k in f['name'].lower() for k in SPICY_KEYWORDS)
                    has_allergy = any(allergy in f['name'].lower() for allergy in allergy_list if allergy)
                    
                    if sweet_tooth <= 1 and is_sweet: continue
                    if spice_level <= 1 and is_spicy: continue
                    if has_allergy: continue
                    
                    filtered_top_foods.append(f['name'])
                    if len(filtered_top_foods) >= 5: break
            
            # If STILL empty (very unlikely), just use the original top but it's really a failure state
            if not filtered_top_foods:
                filtered_top_foods = top_foods_all[:5]

        top_indices = filtered_top_indices[:10]
        top_foods = filtered_top_foods[:10]

        # Determine category & drink
        mood = user_profile.get('mood', 'Happy')
        personality = user_profile.get('personality', 'Ambivert')
        diet_type = user_profile.get('diet_type', 'Non-Vegetarian')
        health_conscious = user_profile.get('health_conscious', 0)
        spice_level = user_profile.get('spice_level', 3)
        sweet_tooth = user_profile.get('sweet_tooth', 3)

        category = _pick_food_category(personality, diet_type, health_conscious, spice_level, mood)
        
        # Select drink based on questionnaire (Q15) and sweet tooth
        q15 = q.get('q15', '')
        if 'Soda/Cola' in q15:
            drink = random.choice(['Chilled Coke', 'Pepsi', 'Thums Up', 'Sprite'])
        elif 'Plain Water' in q15:
            drink = 'Refreshing Mineral Water'
        elif 'Tea/Coffee' in q15:
            drink = random.choice(['Masala Chai', 'Filter Coffee', 'Ginger Tea'])
        elif q15 and q15 != 'Other':
            drink = q15 # Use the "Other" text if provided
        elif sweet_tooth <= 2:
            drink = random.choice(DRINKS.get('Non-Sweet'))
        else:
            drink = random.choice(DRINKS.get('Sweet'))

        # Confidence percentage for the primary recommendation
        confidence = max(10.0, float(probas[top_indices[0]]) * 100)

        # Construct alternatives list with names and prices (Show top 5 now)
        alternatives = []
        for alt_name in top_foods[1:6]:
            alternatives.append({
                'name': alt_name,
                'price': f"₹{_get_food_price(alt_name)}",
                'emoji': _get_food_emoji(alt_name)
            })

        return {
            'primary': top_foods[0],
            'primary_price': f"₹{_get_food_price(top_foods[0])}",
            'primary_emoji': _get_food_emoji(top_foods[0]),
            'alternatives': alternatives,
            'drink': drink,
            'category': category.title(),
            'confidence': round(confidence, 1),
            'mood': mood,
        }


# Singleton engine instance
engine = MoodieEngine()
