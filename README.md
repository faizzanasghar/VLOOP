# Vloop - Premium Movie Discovery & Recommendation Platform

Vloop is a production-grade, full-stack Movie Recommendation System built with **React**, **FastAPI**, **SQLite**, and **scikit-learn**. It leverages rich metadata from TMDB—such as genres, key search terms, top actors, and directors—to generate highly accurate, content-based film recommendations. 

The application has been completely redesigned with a modern, dark-themed, cinematic interface inspired by leading streaming platforms.

---

## 🌟 Key Features

1. **Dual Recommendation Engines**: Switch between Bag of Words (CountVectorizer) and TF-IDF models dynamically to fine-tune your recommendations.
2. **Actor & Genre Search**: The advanced search bar queries dynamically across titles, actors, and genres.
3. **User Authentication & Watchlists**: Secure local authentication (via `bcrypt` and SQLite) allows users to create accounts, log in, and persist their personalized watchlists.
4. **Cinematic 3D Interface**: Features a custom 3D "entering to the loop" splash animation, micro-interactions, smooth hover states, and glassmorphism styling.
5. **Interactive Detail Modal**: Inspect overviews, match scores, ratings, cast, and directors dynamically via the TMDB API integration.

---

## 📊 Dataset Details

The system relies on the **TMDB 5000 Movies Dataset**:
1. **`tmdb_5000_movies.csv`**: Contains details such as budget, genres, id, keywords, original title, overview, popularity, release date, runtime, title, vote_average, and vote_count.
2. **`tmdb_5000_credits.csv`**: Contains casting details (`cast` and `crew`) for each film.

---

## 🧠 Approach & Feature Engineering

The recommendation pipeline follows a standard NLP-based content-filtering approach:

### 1. Data Cleaning & Extraction
- **Merge**: Movies and Credits datasets are joined on the movie `title`.
- **Parsing JSON**: Metadata like genres, keywords, cast, and crew are parsed from string-serialized JSON lists into clean Python lists.
- **Entity Resolution**:
  - Top 5 cast members are extracted.
  - The movie's director is extracted from the crew array.
- **Token Normalization**: To prevent the vectorizer from splitting multi-word names (e.g., separating "Sam" and "Worthington"), spaces within name/genre entities are removed (e.g., "Sam Worthington" -> `SamWorthington`).

### 2. Feature Consolidation (Tags Creation)
- Text from the `overview` (tokenized), `genres`, `keywords`, `cast`, and `crew` lists are combined into a single `tags` column.

### 3. Stemming
- NLTK's `PorterStemmer` is applied to group word variations (e.g., "activities", "acted", "actor" -> "act").

### 4. Vectorization & Similarity
- **CountVectorizer (Bag of Words)**: Converts tags into a sparse matrix representing frequency of words.
- **TfidfVectorizer (Term Frequency-Inverse Document Frequency)**: Down-weights common words that appear across many movies while highlighting rare, differentiating terms.
- **Cosine Similarity**: Computes pairwise cosine similarity between all movie vectors.

---

## 🛠️ Tech Stack

- **Frontend**: React, Vite, Framer Motion, Vanilla CSS (Cinematic Dark Theme), Lucide Icons
- **Backend API**: Python 3.10+, FastAPI, Uvicorn
- **Database & Auth**: SQLite, bcrypt
- **Machine Learning**: scikit-learn, pandas, NumPy, NLTK
- **External Integrations**: TMDB API (Dynamic poster fetching)

---

## 🚀 How to Run Locally

### 1. Clone the project & Prepare Data
Ensure the dataset files are placed in the `data/` directory:
- `data/tmdb_5000_movies.csv`
- `data/tmdb_5000_credits.csv`

### 2. Set up Python Backend Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install backend requirements
pip install -r requirements.txt
```

### 3. Run Preprocessing and Train Models
Build the recommendation models locally:
```bash
# Process data and extract features (cast, directors, genres)
python src/preprocess.py

# Train CountVectorizer and TF-IDF models
python src/model.py
```

### 4. Start the FastAPI Backend Server
```bash
# Optional: enables live TMDB poster lookups (the app uses a placeholder without it)
# PowerShell: $env:TMDB_API_KEY = "your-tmdb-api-key"
uvicorn api:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 5. Start the React Frontend
Open a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
Navigate to `http://localhost:5173/` in your browser to experience Vloop!
