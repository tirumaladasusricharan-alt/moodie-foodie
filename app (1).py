"""
Moodie Foodie — Personality-driven food recommendation web app.
Flask + MySQL + scikit-learn
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# from flaskwebgui import FlaskUI  <-- Moved this to the bottom for cloud safety
from database import get_db_connection, init_db, export_users_to_csv
from moodie_engine import engine, PERSONALITIES, DIETS, CUISINES, MOODS, TIMES
WEATHERS = ['Pleasant', 'Hot', 'Rainy', 'Cold']

MOOD_DESCRIPTIONS = {
    'Happy': 'You are glowing! Keep the vibes high with celebratory treats. For breakfast: Masala Dosa or Puri-Bhaji. For lunch/dinner: Chicken Biryani, Butter Chicken with Naan, or Paneer Pulao. Dessert: Gulab Jamun or Rasgulla.',
    'Sad': 'Time for soul-soothing comfort to lift your spirits. Try warm Idli-Sambar or Poha. For heavy meals: Creamy Dal Makhani, Paneer Butter Masala, or Rajma Chawal. Dessert: Hot Gajar Ka Halwa.',
    'Stressed': 'Take a breather with easy-to-eat munchies. Grab a Vada Pav, Samosas, or Sev Puri. For a quick start: Mysore Bonda or a hot Cup of Filter Coffee with Biscuits.',
    'Angry': 'Channel that fire into bold, intense flavors! Spice it up with Chicken 65, Chilli Paneer, or Gobi Manchurian. For a morning kick: Spicy Mirchi Bajji or Masala Chai.',
    'Excited': 'Match your energy with adventurous street food and party flavors! Pani Puri, Pav Bhaji, and Spring Rolls are perfect. For a big meal: Hyderabadi Biryani or Chilli Chicken.',
    'Bored': 'Break the monotony with something crunchy and fun. Masala Vada, Dahi Puri, or hot Mysore Bonda will spice up your day. Try some Jalebi-Rabri for a sweet twist.',
    'Anxious': 'Stay grounded with familiar, gentle flavors. Plain Dosa, Upma, or a comforting bowl of Dal Rice/Khichdi will help you relax and feel at home.',
    'Romantic': 'Sweet and spicy, just like your mood. Indulge in Rasmalai, Paneer Tikka, or a shared plate of Veg/Chicken Momos. A light evening snack like Dahi Puri is also great.'
}
import os
import sys
import time

def get_path(filename):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(".")
    return os.path.join(base, filename)

template_folder = get_path('templates')
static_folder = get_path('static')

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_moodie_key_2024')
app.config['SESSION_PERMANENT'] = True

# Hardcoded Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123" 


# ─── PWA ────────────────────────────────────────────────────────
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def sw():
    return app.send_static_file('sw.js')


# ─── Helpers ────────────────────────────────────────────────────
def _user_dict(row, columns):
    """Convert a MySQL row tuple + column names to a dict."""
    return dict(zip(columns, row))


# ─── Routes ─────────────────────────────────────────────────────
@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect('/admin')
        return redirect('/dashboard')
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to correct dashboard
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect('/admin')
        return redirect('/dashboard')

    if request.method == 'POST':
        action = request.form.get('action', 'login')
        username = request.form['username']
        password = request.form['password']
        role_intent = request.form.get('role_intent', 'user')

        # ─── Debug Login ───
        print(f"[DEBUG] Login attempt: user='{username}', role_intent='{role_intent}', action='{action}'")

        # 1. Hardcoded Admin Check
        if username.strip().lower() == ADMIN_USER.lower() and password.strip() in [ADMIN_PASS, 'sricharan3103']:
            session.permanent = True
            session['user_id'] = 8 # Match DB admin ID
            session['username'] = ADMIN_USER
            session['role'] = 'admin'
            session.modified = True
            print("[DEBUG] Hardcoded Admin login SUCCESS")
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except Exception as e:
            print(f"[ERR] DB Connection failed: {e}")
            flash("Database connection error. Please try again later.", "error")
            return redirect('/login')

        if action == 'signup':
            # ── Sign-up with personality analysis ──
            age             = int(request.form.get('age', 25))
            personality     = request.form.get('personality', 'Ambivert')
            diet_type       = request.form.get('diet_type', 'Non-Vegetarian')
            spice_level     = int(request.form.get('spice_level', 3))
            sweet_tooth     = int(request.form.get('sweet_tooth', 3))
            cuisine_pref    = request.form.get('cuisine_pref', 'Indian')
            health_conscious = 1 if request.form.get('health_conscious') else 0
            allergies       = request.form.get('allergies', '')

            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                flash('Username already taken. Please log in or choose another.', 'error')
                cursor.close()
                conn.close()
                return redirect('/login')

            cursor.execute(
                """INSERT INTO users
                   (username, password, age, personality, diet_type,
                    spice_level, sweet_tooth, cuisine_pref, health_conscious, allergies, role)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (username.strip(), password.strip(), age, personality, diet_type,
                 spice_level, sweet_tooth, cuisine_pref, health_conscious, allergies, 'user')
            )
            conn.commit()
            
            # Export to CSV automatically
            export_users_to_csv()

            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            columns = [desc[0] for desc in cursor.description]
            user = _user_dict(cursor.fetchone(), columns)

            # Store profile in session
            for key in ['id', 'username', 'age', 'personality', 'diet_type',
                         'spice_level', 'sweet_tooth', 'cuisine_pref', 'health_conscious', 'allergies', 'role']:
                session_key = 'user_id' if key == 'id' else key
                session[session_key] = user[key]

            flash(f'Welcome, {username}! Your taste profile is ready.', 'success')
            cursor.close()
            conn.close()
            return redirect('/dashboard')

        else:
            # ── Log in ──
            cursor.execute('SELECT * FROM users WHERE username = %s', (username.strip(),))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                user = _user_dict(row, columns)
                print(f"[DEBUG] Found user in DB: {user['username']}, checking password...")
                if user['password'] == password.strip():
                    # Check role vs intent
                    if role_intent == 'admin' and user['role'] != 'admin':
                        print(f"[DEBUG] Role mismatch: intent='admin', user_role='{user['role']}'")
                        flash('Unauthorized. You do not have admin privileges.', 'error')
                        cursor.close()
                        conn.close()
                        return redirect('/login')
                    
                    for key in ['id', 'username', 'age', 'personality', 'diet_type',
                                 'spice_level', 'sweet_tooth', 'cuisine_pref', 'health_conscious', 'allergies', 'role']:
                        session_key = 'user_id' if key == 'id' else key
                        session[session_key] = user[key]
                    
                    flash(f'Welcome back, {username}!', 'success')
                    session['username'] = user['username']
                    session['role'] = user['role']
                    
                    # Load questionnaire answers from DB
                    cursor.execute("SELECT * FROM questionnaire WHERE user_id = %s", (user['id'],))
                    q_row = cursor.fetchone()
                    if q_row:
                        session['questionnaire_answers'] = {f'q{i}': q_row[i] for i in range(1, 16)}
                    
                    if user['role'] == 'admin':
                        return redirect('/admin')
                    return redirect('/dashboard')
                else:
                    flash('Incorrect password.', 'error')
            else:
                flash('User not found. Please sign up first.', 'error')

        cursor.close()
        conn.close()

    return render_template('login.html',
                           personalities=PERSONALITIES,
                           diets=DIETS,
                           cuisines=CUISINES)


@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        answers = {}
        for i in range(1, 16):
            q_key = f'q{i}'
            other_key = f'q{i}_other'
            val = request.form.get(q_key)
            if val == 'Other':
                val = request.form.get(other_key, 'Other')
            answers[q_key] = val
        
        # Save to DB
        cursor.execute("SELECT user_id FROM questionnaire WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE questionnaire SET 
                q1=%s, q2=%s, q3=%s, q4=%s, q5=%s, q6=%s, q7=%s, q8=%s, q9=%s, q10=%s, q11=%s, q12=%s, q13=%s, q14=%s, q15=%s
                WHERE user_id = %s
            """, (*[answers.get(f'q{i}', '') for i in range(1, 16)], user_id))
        else:
            cursor.execute("""
                INSERT INTO questionnaire (user_id, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, *[answers.get(f'q{i}', '') for i in range(1, 16)]))
        
        conn.commit()
        session['questionnaire_answers'] = answers
        session.modified = True
        cursor.close()
        conn.close()
        flash('Questionnaire updated successfully!', 'success')
        return redirect('/dashboard')

    # Load from DB if not in session
    existing_answers = session.get('questionnaire_answers')
    if not existing_answers:
        cursor.execute("SELECT * FROM questionnaire WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if row:
            # row is (user_id, q1, q2, ...)
            # If using SQLiteRow, we can access by key or index
            # Our SQLiteWrapper returns tuples or rows depending on fetchall
            # Let's assume it behaves like a dict if possible, or use indices
            existing_answers = {f'q{i}': row[i] for i in range(1, 16)}
            session['questionnaire_answers'] = existing_answers
    
    cursor.close()
    conn.close()
    return render_template('questionnaire.html', answers=existing_answers or {})


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect('/login')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        mood           = request.form.get('mood', 'Happy')
        mood_intensity = int(request.form.get('intensity', 3))
        time_of_day    = request.form.get('time_of_day', 'Afternoon')
        weather        = request.form.get('weather', 'Pleasant')

        # 1. Fetch rated foods to avoid (1-4) or prefer (5)
        avoid_foods = []
        prefer_foods = []
        conn = get_db_connection()
        cursor = conn.cursor()
        print(f"[DEBUG] Current User ID in session: {session.get('user_id')}")
        try:
            # Fetch all feedback ordered by most recent first
            cursor.execute(
                """SELECT recommended_primary, rating FROM feedback 
                   WHERE user_id = %s 
                   ORDER BY id DESC""",
                (session.get('user_id'),)
            )
            
            seen_foods = set()
            for row in cursor.fetchall():
                food_name = row[0]
                rating = row[1]
                if food_name not in seen_foods:
                    seen_foods.add(food_name)
                    if rating < 5:
                        avoid_foods.append(food_name)
                    elif rating == 5:
                        prefer_foods.append(food_name)
            
            print(f"[DEBUG] Avoid List: {avoid_foods}")
            print(f"[DEBUG] Prefer List: {prefer_foods}")
        except Exception as e:
            print(f"[WARN] Failed to fetch rating lists: {e}")
        
        # 2. Log the mood and reflection
        mood_reason = request.form.get('mood_reason', '')
        mood_duration = request.form.get('mood_duration', '')
        food_goal = request.form.get('food_goal', '')

        cursor.execute(
            """INSERT INTO mood_logs (user_id, mood, mood_intensity, time_of_day, weather)
               VALUES (%s, %s, %s, %s, %s)""",
            (session['user_id'], mood, mood_intensity, time_of_day, weather)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # 3. Build user profile for prediction
        user_profile = {
            'age':              session.get('age', 25),
            'personality':      session.get('personality', 'Ambivert'),
            'diet_type':        session.get('diet_type', 'Non-Vegetarian'),
            'spice_level':      session.get('spice_level', 3),
            'sweet_tooth':      session.get('sweet_tooth', 3),
            'cuisine_pref':     session.get('cuisine_pref', 'Indian'),
            'health_conscious': session.get('health_conscious', 0),
            'allergies':        session.get('allergies', ''),
            'mood':             mood,
            'mood_intensity':   mood_intensity,
            'time_of_day':      time_of_day,
            'weather':          weather,
            'mood_reason':      mood_reason,
            'mood_duration':    mood_duration,
            'food_goal':        food_goal,
            'questionnaire':    session.get('questionnaire_answers', {})
        }

        # ML prediction with timing and avoidance
        start_time = time.time()
        results = engine.predict(user_profile, avoid_foods=avoid_foods, prefer_foods=prefer_foods)
        exec_time = time.time() - start_time
        print(f"[FAST] Prediction in {exec_time:.4f}s with {len(avoid_foods)} avoided and {len(prefer_foods)} preferred items")

        results['exec_time'] = round(exec_time, 4)
        results['mood_description'] = MOOD_DESCRIPTIONS.get(mood, "Enjoy this curated selection!")
        session['last_results'] = results
        session['last_mood'] = mood
        session['last_intensity'] = mood_intensity

        return redirect('/results')

    return render_template('dashboard.html',
                           username=session['username'],
                           personality=session.get('personality', 'Ambivert'),
                           diet_type=session.get('diet_type'),
                           moods=MOODS,
                           times=TIMES,
                           weathers=WEATHERS)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Get data from form
        age              = int(request.form.get('age', 25))
        personality      = request.form.get('personality', 'Ambivert')
        diet_type        = request.form.get('diet_type', 'Non-Vegetarian')
        spice_level      = int(request.form.get('spice_level', 3))
        sweet_tooth      = int(request.form.get('sweet_tooth', 3))
        cuisine_pref     = request.form.get('cuisine_pref', 'Indian')
        health_conscious = 1 if request.form.get('health_conscious') else 0
        allergies        = request.form.get('allergies', '')

        # Update DB
        cursor.execute(
            """UPDATE users SET 
               age=%s, personality=%s, diet_type=%s, spice_level=%s, 
               sweet_tooth=%s, cuisine_pref=%s, health_conscious=%s, allergies=%s
               WHERE id=%s""",
            (age, personality, diet_type, spice_level, sweet_tooth, cuisine_pref, health_conscious, allergies, session['user_id'])
        )
        conn.commit()

        # Update session
        session['age'] = age
        session['personality'] = personality
        session['diet_type'] = diet_type
        session['spice_level'] = spice_level
        session['sweet_tooth'] = sweet_tooth
        session['cuisine_pref'] = cuisine_pref
        session['health_conscious'] = health_conscious
        session['allergies'] = allergies

        flash('Your preferences have been updated!', 'success')
        
        # Export updated data to CSV
        export_users_to_csv()
        
        cursor.close()
        conn.close()
        return redirect('/dashboard')

    # GET: Load current data
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    columns = [desc[0] for desc in cursor.description]
    user_row = cursor.fetchone()
    user_data = _user_dict(user_row, columns)

    cursor.close()
    conn.close()

    return render_template('edit_profile.html', 
                           user=user_data,
                           personalities=PERSONALITIES,
                           diets=DIETS,
                           cuisines=CUISINES)


@app.route('/results', methods=['GET', 'POST'])
def results():
    if 'user_id' not in session:
        return redirect('/login')

    results = session.get('last_results')
    if not results:
        return redirect('/dashboard')

    if request.method == 'POST':
        rating = int(request.form.get('rating', 3))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO feedback
               (user_id, mood, mood_intensity, recommended_primary, rating)
               VALUES (%s, %s, %s, %s, %s)""",
            (session['user_id'], session.get('last_mood'), session.get('last_intensity'),
             results['primary'], rating)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Thanks for rating! Your feedback helps us improve.', 'success')
        return redirect('/dashboard')

    return render_template('results.html', results=results,
                           username=session['username'])


@app.route('/admin')
def admin():
    # Protection: Only allow if 'admin' is logged in
    if session.get('role') != 'admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Analytics Stats
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(rating) FROM feedback')
    avg_rating = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT mood, COUNT(*) as cnt FROM mood_logs
        GROUP BY mood ORDER BY cnt DESC LIMIT 1
    """)
    row = cursor.fetchone()
    top_mood = row[0] if row else 'N/A'

    # 2. Recent Feedback
    cursor.execute("""
        SELECT f.id, u.username, f.mood, f.recommended_primary, f.rating, f.created_at
        FROM feedback f JOIN users u ON f.user_id = u.id
        ORDER BY f.created_at DESC LIMIT 15
    """)
    columns_fb = [desc[0] for desc in cursor.description]
    feedbacks = [dict(zip(columns_fb, r)) for r in cursor.fetchall()]

    # 3. Personality distribution
    cursor.execute('SELECT personality, COUNT(*) as cnt FROM users GROUP BY personality')
    personality_dist = {r[0]: r[1] for r in cursor.fetchall()}

    # 4. Full User Database
    cursor.execute('SELECT id, username, age, personality, diet_type, cuisine_pref, created_at FROM users ORDER BY created_at DESC')
    columns_u = [desc[0] for desc in cursor.description]
    all_users = [dict(zip(columns_u, r)) for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    stats = {
        'total_users': total_users,
        'average_rating': round(avg_rating, 1),
        'most_common_mood': top_mood,
    }

    return render_template('admin.html', stats=stats, feedbacks=feedbacks,
                           personality_dist=personality_dist, all_users=all_users)


# ─── Startup ────────────────────────────────────────────────────
if __name__ == '__main__':
    print("[START] Initializing Moodie Foodie...")
    init_db()

    if not engine.is_trained:
        engine.generate_synthetic_data()

    # Detect if we are running on a server (Hugging Face, Render, etc.)
    # Hugging Face usually provides a SPACE_ID or similar env var
    is_server = os.environ.get('SPACE_ID') or os.environ.get('RENDER') or os.environ.get('PORT')

    if is_server:
        # Standard web server mode for Cloud
        port = int(os.environ.get('PORT', 7860))
        print(f"[OK] Running in CLOUD mode on port {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        # Integrated Desktop UI with flaskwebgui (local use)
        from flaskwebgui import FlaskUI
        print("[OK] Running in DESKTOP mode")
        ui = FlaskUI(app=app, server="flask", port=5000, width=1200, height=900)
        ui.run()
