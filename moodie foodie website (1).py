from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from moodie_engine import engine
import time
import os

app = Flask(__name__)
app.secret_key = 'super_secret_calming_key'

# Dummy admin data for visualization
ADMIN_STATS = {
    'total_users': 150,
    'average_rating': 4.2,
    'most_common_mood': 'Stressed',
    'avg_response_time': 0.12
}

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] # Note: In production, hash passwords
        age = request.form.get('age', 25) # Default age if signup
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user:
            if user['password'] == password:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['age'] = user['age']
                return redirect('/dashboard')
            else:
                flash('Invalid credentials')
        else:
            # Simple auto-signup if user doesn't exist
            conn.execute('INSERT INTO users (username, password, age) VALUES (?, ?, ?)', (username, password, int(age)))
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['age'] = user['age']
            return redirect('/dashboard')
            
        conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
        
    if request.method == 'POST':
        mood = request.form.get('mood')
        intensity = int(request.form.get('intensity'))
        age = session.get('age', 25)
        
        # Engine execution with timing
        start_time = time.time()
        results = engine.predict(age, mood, intensity)
        end_time = time.time()
        
        # Ensure under 2 seconds requirement
        execution_time = end_time - start_time
        print(f"Model executed in {execution_time:.4f} seconds")
        
        session['last_results'] = results
        return redirect('/results')
        
    return render_template('dashboard.html', username=session['username'])

@app.route('/results', methods=['GET', 'POST'])
def results():
    if 'user_id' not in session:
        return redirect('/login')
        
    results = session.get('last_results')
    if not results:
        return redirect('/dashboard')
        
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        
        conn = get_db_connection()
        conn.execute('INSERT INTO feedback (user_id, recommended_primary, rating) VALUES (?, ?, ?)',
                     (session['user_id'], results['primary'], rating))
        conn.commit()
        conn.close()
        flash('Thank you for your feedback!')
        return redirect('/dashboard')
        
    return render_template('results.html', results=results)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    feedbacks = conn.execute('SELECT * FROM feedback ORDER BY id DESC LIMIT 10').fetchall()
    conn.close()
    
    return render_template('admin.html', stats=ADMIN_STATS, feedbacks=feedbacks)

if __name__ == '__main__':
    # Make sure engine is trained on startup
    if not engine.is_trained:
        engine.generate_synthetic_data()
        
    app.run(debug=True, port=5000)
