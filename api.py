import os
import sys
import json
import sqlite3
import bcrypt
import requests
import pandas as pd
from typing import Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add src folder to system path
sys.path.append(os.path.abspath("src"))

from recommender import MovieRecommender

app = FastAPI(title="Vloop API", description="Vloop Movie Recommendation Backend API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join("data", "users.db")

class AuthPayload(BaseModel):
    username: str
    password: str

class WatchlistPayload(BaseModel):
    username: str
    watchlist: list = []


def ensure_db_directory():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def get_db():
    ensure_db_directory()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                watchlist TEXT DEFAULT '[]'
            )
            """
        )
        conn.commit()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def get_user_by_username(username: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def create_user(username: str, password_hash: str):
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_watchlist_for_user(username: str):
    user = get_user_by_username(username)
    if not user:
        return []
    try:
        return json.loads(user.get('watchlist', '[]') or '[]')
    except json.JSONDecodeError:
        return []


def save_watchlist_for_user(username: str, watchlist):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET watchlist = ? WHERE username = ?",
            (json.dumps(watchlist), username)
        )
        conn.commit()


# ----------------------------------------------------
# 🚂 MODEL INITIALIZATION & CACHE
# ----------------------------------------------------

def build_models_if_missing():
    """Run preprocessing and training if pkl files are not found."""
    models_dir = "models"
    required = ["movies_dict.pkl", "similarity_cv.pkl", "similarity_tfidf.pkl"]
    all_exist = all(os.path.exists(os.path.join(models_dir, f)) for f in required)
    if all_exist:
        return

    print("Model files not found — building from raw data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass

    # Step 1: Preprocess
    preprocessed_path = os.path.join("data", "preprocessed_movies.csv")
    if not os.path.exists(preprocessed_path):
        print("Running preprocess.py...")
        import preprocess
        preprocess.main()

    # Step 2: Train models
    print("Running model.py training...")
    import model as model_trainer
    model_trainer.main()
    print("Model build complete.")


build_models_if_missing()
init_db()
recommender = None
try:
    recommender = MovieRecommender("models")
except Exception as e:
    print(f"Error loading recommender system: {e}")

# In-memory cache for poster URLs to avoid repeated TMDB API hits
poster_cache = {}

def get_movie_poster(movie_id: int) -> str:
    if movie_id in poster_cache:
        return poster_cache[movie_id]
    
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                poster_cache[movie_id] = url
                return url
    except Exception:
        pass
    
    # Return placeholder
    return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"

def parse_list_field(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        import ast
        try:
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def format_movie_response(movie_row, include_poster: bool = True) -> dict:
    movie_dict = movie_row.to_dict() if isinstance(movie_row, pd.Series) else dict(movie_row)
    # Ensure cast and director are parsed correctly
    def parse_list(val):
        if isinstance(val, str):
            import ast
            try:
                return ast.literal_eval(val)
            except:
                return []
        return val if isinstance(val, list) else []

    genres = parse_list(movie_dict.get('genres_original', []))
    cast = parse_list(movie_dict.get('cast_original', []))
    director = parse_list(movie_dict.get('director_original', []))
    
    movie_id = int(movie_dict['movie_id'])
    
    # Basic data structure
    res = {
        "movie_id": movie_id,
        "title": movie_dict['title'],
        "overview": movie_dict.get('overview', ''),
        "genres": genres,
        "cast": cast,
        "director": director,
        "directors": director,
        "popularity": float(movie_dict.get('popularity', 0.0)),
        "vote_average": float(movie_dict.get('vote_average', 0.0)),
    }
    
    if include_poster:
        res["poster_url"] = get_movie_poster(movie_id)
        
    return res

# ----------------------------------------------------
#  AUTHENTICATION ENDPOINTS
# ----------------------------------------------------

@app.post("/api/auth/register")
def register(auth: AuthPayload):
    if not auth.username.strip() or not auth.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if get_user_by_username(auth.username):
        raise HTTPException(status_code=409, detail="Username already exists")

    pw_hash = hash_password(auth.password)
    if not create_user(auth.username, pw_hash):
        raise HTTPException(status_code=500, detail="Could not create user")

    return {"success": True, "username": auth.username}


@app.post("/api/auth/login")
def login(auth: AuthPayload):
    user = get_user_by_username(auth.username)
    if not user or not verify_password(auth.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"success": True, "username": auth.username, "watchlist": get_watchlist_for_user(auth.username)}


@app.get("/api/auth/watchlist")
def fetch_watchlist(username: str = Query(..., min_length=1)):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"watchlist": get_watchlist_for_user(username)}


@app.post("/api/auth/watchlist")
def save_watchlist(watchlist_payload: WatchlistPayload):
    if not get_user_by_username(watchlist_payload.username):
        raise HTTPException(status_code=404, detail="User not found")
    save_watchlist_for_user(watchlist_payload.username, watchlist_payload.watchlist)
    return {"success": True, "watchlist": watchlist_payload.watchlist}


# ----------------------------------------------------
# 📌 API ENDPOINTS
# ----------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": recommender is not None}

@app.get("/api/genres")
def get_genres():
    if recommender is None or recommender.df is None:
        return []
    return recommender.get_all_genres()

@app.get("/api/movies/popular")
def get_popular_movies(limit: int = 24):
    if recommender is None or recommender.df is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    popular = recommender.df.sort_values(by="popularity", ascending=False).head(limit)
    return [format_movie_response(row) for _, row in popular.iterrows()]

@app.get("/api/movies/top-rated")
def get_top_rated_movies(limit: int = 24):
    if recommender is None or recommender.df is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Filter out movies with low popularity or very low vote counts to avoid obscure ratings
    top_rated = recommender.df[recommender.df['popularity'] > 10].sort_values(by="vote_average", ascending=False).head(limit)
    return [format_movie_response(row) for _, row in top_rated.iterrows()]

@app.get("/api/movies/trending")
def get_trending_movies(limit: int = 24):
    if recommender is None or recommender.df is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Trending is computed by a combination of high popularity and high votes (e.g. popularity offset)
    trending = recommender.df.sort_values(by=["popularity", "vote_average"], ascending=[False, False]).iloc[10:10+limit]
    return [format_movie_response(row) for _, row in trending.iterrows()]

@app.get("/api/search")
def search_movies(q: str = Query(..., min_length=1), limit: int = 20):
    if recommender is None or recommender.df is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    query = q.strip().lower()
    if not query:
        return []

    # Case-insensitive substring match across title, genres, and cast
    def match_row(row):
        q_lower = q.lower()
        if q_lower in str(row.get('title', '')).lower():
            return True
        if q_lower in str(row.get('genres_original', '')).lower():
            return True
        if q_lower in str(row.get('cast_original', '')).lower():
            return True
        return False

    matches = recommender.df[recommender.df.apply(match_row, axis=1)].head(limit)
    return [format_movie_response(row) for _, row in matches.iterrows()]

@app.get("/api/recommend")
def recommend_movies(
    title: str, 
    method: str = "Count Vectorizer", 
    genre: Optional[str] = None, 
    top_n: int = 10
):
    if recommender is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        genre_filter = None if not genre or genre == "All Genres" else genre
        matched_title, recommendations = recommender.recommend(
            movie_title=title,
            method=method,
            genre_filter=genre_filter,
            top_n=top_n
        )
        
        # Format the recommendations
        formatted_recs = []
        for rec in recommendations:
            formatted_recs.append({
                "movie_id": int(rec['movie_id']),
                "title": rec['title'],
                "overview": rec.get('overview', ''),
                "genres": rec.get('genres_original', []),
                "popularity": float(rec.get('popularity', 0.0)),
                "vote_average": float(rec.get('vote_average', 0.0)),
                "similarity_score": float(rec.get('similarity_score', 0.0)),
                "poster_url": get_movie_poster(int(rec['movie_id']))
            })
            
        return {
            "matched_title": matched_title,
            "recommendations": formatted_recs
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/movie/{movie_id}")
def get_movie_details(movie_id: int):
    if recommender is None or recommender.df is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    match = recommender.df[recommender.df['movie_id'] == movie_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    return format_movie_response(match.iloc[0])



if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
