# Moodie-Foodie: Intelligent Mood-Based Food Recommendation System

Moodie-Foodie is an emotion-aware food recommendation system designed to solve decision fatigue by aligning culinary choices with a user’s psychological state. By capturing demographics and mood intensity, the platform moves beyond traditional search filters to understand the why behind a craving. 

The core architecture bridges complex machine learning with a practical web application to transform traditional food discovery into an intuitive, emotionally resonant service.

---

## Features

- Psychological Profile and Input Tracking: Captures user demographics, specific mood intensity levels, and historical preferences.
- Smart Safety Net Logic: Recognizes high-stress emotional states to prioritize familiar Comfort Favorites over experimental cuisines.
- Random Forest Predictive Engine: Utilizes a data preprocessing and scaling pipeline with a Random Forest classifier to predict optimal food categories in under 2 seconds.
- Multi-Tier Recommendations: Generates a primary recommendation alongside two tailored alternatives for a flexible user experience.
- Adaptive Feedback Loop: Continuously refines machine learning predictions by tracking and recording user interactions and ratings to mitigate model drift.

---

## System Architecture and UML

The system separates privileges and duties between the end-user and the administrative dashboard. 

### Use Case Diagram
The platform manages actions ranging from user profile management and mood inputs to backend data preprocessing, reporting, and feedback collection.

- User Actions: Register, Login, Update/View Profile, Select Inputs (Mood/Intensity), View Report, View and Give Feedback, Logout.
- Admin Actions: Data Preprocessing, Analyze and Generate Report, Analyze Feedback, View and Save Feedback.

---

## Tech Stack and Requirements

### Software Requirements
- Operating System: Windows 10 / 11, Linux (Ubuntu), or Android (for mobile access)
- Backend and AI Logic: Python (Django )
- Frontend Interface: HTML5, CSS3, JavaScript
- Database Management: SQL (for user profiles, historical logs, and feedback tracking)
- Development Environments: Anaconda / Python IDLE, Visual Studio Code, Jupyter Notebook (for model testing)

### Hardware Requirements
- Processor: Intel i3 / i5 / i7 or equivalent (required for data processing and ML computation)
- Host Server: High-performance local environment or cloud server capable of handling simultaneous requests.
- Client Devices: Desktop, Laptop, Tablet, or Smartphone interface.

---

## Non-Functional and Quality Standards

- Performance: High-precision matching completed within a 2-second response window, optimized for concurrent multi-user traffic.
- Security and Privacy: Personal demographic and emotional data are encrypted both in transit and at rest. Training inputs are fully anonymized and stripped of Personally Identifiable Information (PII).
- Usability: Calming color palettes designed to minimize user stress, allowing a recommendation to be reached in 3 taps or fewer from the home screen.
- Reliability: Engineered for 99.9% uptime. Features a built-in fallback system that defaults to a user's historical favorites if the mood-sensing module fails.

---

