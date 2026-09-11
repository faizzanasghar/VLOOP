import os
import sys
import streamlit as st
import pandas as pd
import requests

# Add src folder to system path
sys.path.append(os.path.abspath("src"))

try:
    from recommender import MovieRecommender
except ImportError:
    # Fallback to handle import during first load when files are being created
    MovieRecommender = None

# ----------------------------------------------------
# 🌟 PAGE CONFIGURATION & THEME
# ----------------------------------------------------
st.set_page_config(
    page_title="CineMatch | Premium Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, premium glassmorphism dark-mode look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');

    /* Global App Container */
    .stApp {
        background: linear-gradient(135deg, #090e1a 0%, #0f172a 40%, #1e1b4b 100%);
        color: #f1f5f9;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header Styling */
    .app-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #f43f5e 0%, #ec4899 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 15px;
        margin-bottom: 5px;
        letter-spacing: -0.05em;
    }
    
    .app-subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #94a3b8;
        margin-bottom: 35px;
        font-weight: 300;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b;
    }
    
    /* Sidebar Headers */
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f43f5e;
        margin-top: 25px;
        margin-bottom: 15px;
        border-left: 4px solid #f43f5e;
        padding-left: 10px;
    }

    /* Glassmorphism Input Container */
    .search-box-container {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 35px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    
    /* Section Title */
    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 20px;
        border-bottom: 2px solid rgba(244, 63, 94, 0.2);
        padding-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Recommendation Card Design */
    .movie-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    
    .movie-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: #f43f5e;
        box-shadow: 0 20px 30px rgba(244, 63, 94, 0.2);
    }
    
    .movie-card img {
        width: 100%;
        border-radius: 12px;
        aspect-ratio: 2/3;
        object-fit: cover;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    }
    
    .movie-title {
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 12px;
        margin-bottom: 6px;
        height: 40px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
    }
    
    .movie-metric {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        background-color: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.2);
        margin-bottom: 6px;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }
    
    .movie-meta {
        font-size: 11px;
        color: #94a3b8;
        font-style: italic;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* Details Panel */
    .details-panel {
        background: rgba(30, 41, 59, 0.35);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 25px;
        margin-top: 30px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 🔑 TMDB POSTER FETCHING HELPER
# ----------------------------------------------------
def get_movie_poster(movie_id, api_key=None):
    if not api_key or api_key.strip() == "":
        api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
        
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key.strip()}&language=en-US"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        pass
    
    # Beautiful movie theme fallback image if fetching fails
    return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=300&auto=format&fit=crop"

# ----------------------------------------------------
# 🚂 PIPELINE EXECUTION FOR ON-THE-FLY TRAINING
# ----------------------------------------------------
def run_training_pipeline():
    try:
        import preprocess
        import model
        preprocess.main()
        model.main()
        return True
    except Exception as e:
        st.error(f"Error during training: {e}")
        return False

# ----------------------------------------------------
# 📁 MODEL INITIALIZATION
# ----------------------------------------------------
@st.cache_resource
def load_recommender_system():
    if not MovieRecommender:
        return None
    try:
        return MovieRecommender("models")
    except FileNotFoundError:
        return None

# Attempt to load the model
recommender = load_recommender_system()

# ----------------------------------------------------
# 💻 UI HEADER
# ----------------------------------------------------
st.markdown('<div class="app-title">🎬 CineMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Discover your next favorite movie using Content-Based Filtering</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 🛠️ SIDEBAR CONTROLS
# ----------------------------------------------------
st.sidebar.markdown('<div class="sidebar-header">🔧 Recommender Engine</div>', unsafe_allow_html=True)

# Vectorization switch
method = st.sidebar.selectbox(
    "Choose Similarity Model",
    options=["Count Vectorizer", "TF-IDF"],
    help="Count Vectorizer recommends based on exact tag frequencies. TF-IDF down-weights words that are very common across all movies, highlighting unique keywords."
)

# Optional TMDB API Key Input
tmdb_api_key = st.sidebar.text_input(
    "TMDB API Key (Optional)",
    type="password",
    help="Provide your TMDB API v3 key to fetch high-res movie posters. A default key will be used if left blank."
)

st.sidebar.markdown('<div class="sidebar-header">📁 Data & Pipeline</div>', unsafe_allow_html=True)

# Re-train button in sidebar
if st.sidebar.button("♻️ Retrain Models", help="Re-run preprocessing and model compilation"):
    with st.sidebar.spinner("Running training pipeline..."):
        success = run_training_pipeline()
        if success:
            st.sidebar.success("Training complete!")
            st.cache_resource.clear()
            st.rerun()

# ----------------------------------------------------
# 🧠 MAIN APP LOGIC
# ----------------------------------------------------
if recommender is None:
    # Model not built yet
    st.warning("⚠️ Recommendation model pickle files were not found under `models/`.")
    st.info("💡 You can initialize and build the models directly now by clicking the button below.")
    if st.button("🚀 Build & Train Models Now (Preprocess + Feature Engineering)"):
        with st.spinner("Executing pipeline files... This takes 10-15 seconds."):
            success = run_training_pipeline()
            if success:
                st.success("🎉 Preprocessing and model training completed successfully!")
                st.cache_resource.clear()
                st.rerun()
else:
    # Model loaded successfully
    titles = recommender.get_all_titles()
    genres_list = recommender.get_all_genres()
    
    # Sidebar Genre Filter
    genre_filter = st.sidebar.selectbox(
        "Filter Recommendations by Genre",
        options=["All Genres"] + genres_list
    )
    selected_genre = None if genre_filter == "All Genres" else genre_filter
    
    # 🔍 Search container
    st.markdown('<div class="search-box-container">', unsafe_allow_html=True)
    col_search, col_btn = st.columns([4, 1])
    
    with col_search:
        selected_movie_title = st.selectbox(
            "Select or Type a Movie Title",
            options=titles,
            placeholder="Type here to search movie database...",
            index=titles.index("Avatar") if "Avatar" in titles else 0
        )
        
    with col_btn:
        st.write("") # Spacer to align button
        st.write("") 
        recommend_btn = st.button("🔍 Recommend Similar", use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # 🎯 RECOMMENDATION PRESENTATION
    # ----------------------------------------------------
    if recommend_btn:
        with st.spinner("Finding matches..."):
            try:
                # Call recommendation engine
                matched_title, recommendations = recommender.recommend(
                    movie_title=selected_movie_title,
                    method=method,
                    genre_filter=selected_genre,
                    top_n=5
                )
                
                st.markdown(f'<div class="section-title">🍿 Recommended for: <i>{matched_title}</i></div>', unsafe_allow_html=True)
                
                if not recommendations:
                    st.warning(f"No movies found matching genre '{genre_filter}' similar to '{matched_title}'. Try choosing another genre filter.")
                else:
                    # Create 5 columns
                    cols = st.columns(5)
                    for idx, movie in enumerate(recommendations):
                        with cols[idx]:
                            # Fetch movie poster
                            poster_url = get_movie_poster(movie['movie_id'], tmdb_api_key)
                            
                            # Render card with hover animations and metadata
                            genres_str = " | ".join(movie['genres_original'][:2]) if isinstance(movie['genres_original'], list) else ""
                            st.markdown(f"""
                            <div class="movie-card">
                                <img src="{poster_url}" />
                                <div class="movie-title">{movie['title']}</div>
                                <div class="movie-metric">{movie['similarity_score']*100:.1f}% Match</div>
                                <div class="movie-meta">{genres_str}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    # Detailed Information Panel below recommendations
                    st.markdown('<div class="details-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🔍 Movie Details & Overviews</div>', unsafe_allow_html=True)
                    
                    selected_detail_title = st.selectbox(
                        "Inspect recommended movie details:",
                        options=[movie['title'] for movie in recommendations]
                    )
                    
                    if selected_detail_title:
                        detail_movie = next(m for m in recommendations if m['title'] == selected_detail_title)
                        
                        det_col1, det_col2 = st.columns([1, 4])
                        with det_col1:
                            detail_poster = get_movie_poster(detail_movie['movie_id'], tmdb_api_key)
                            st.image(detail_poster, use_container_width=True)
                        with det_col2:
                            st.markdown(f"### {detail_movie['title']}")
                            st.markdown(f"**Genres:** {', '.join(detail_movie['genres_original'])}")
                            st.markdown(f"**Match Rating:** `{detail_movie['similarity_score']*100:.2f}%` similarity using {method}")
                            st.markdown(f"**Synopsis:**")
                            st.write(detail_movie['overview'])
                            
                            # Optional TMDB details fetching if available
                            api_key = tmdb_api_key.strip() if tmdb_api_key else os.getenv("TMDB_API_KEY")
                            tmdb_url = f"https://api.themoviedb.org/3/movie/{detail_movie['movie_id']}?api_key={api_key}&language=en-US" if api_key else None
                            try:
                                tmdb_resp = requests.get(tmdb_url, timeout=3).json()
                                if 'release_date' in tmdb_resp:
                                    st.markdown(f"**Release Date:** {tmdb_resp.get('release_date')}")
                                    st.markdown(f"**Rating (TMDB):** ⭐ {tmdb_resp.get('vote_average')}/10 ({tmdb_resp.get('vote_count')} votes)")
                                    st.markdown(f"**Runtime:** {tmdb_resp.get('runtime')} minutes")
                            except:
                                pass
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except KeyError as e:
                st.error(f"Movie search error: {e}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                
    else:
        # ----------------------------------------------------
        # 🔥 POPULAR & TRENDING MOVIES (INITIAL STATE)
        # ----------------------------------------------------
        st.markdown('<div class="section-title">🔥 Popular & Trending Movies</div>', unsafe_allow_html=True)
        
        # Get top 5 sorted by popularity
        trending_df = recommender.df.sort_values(by="popularity", ascending=False).head(5)
        
        cols_trend = st.columns(5)
        for idx, (_, movie) in enumerate(trending_df.iterrows()):
            with cols_trend[idx]:
                poster_url = get_movie_poster(movie['movie_id'], tmdb_api_key)
                genres_str = " | ".join(movie['genres_original'][:2]) if isinstance(movie['genres_original'], list) else ""
                
                # Check for release date if possible
                rating_str = f"Rating: {movie['vote_average']}/10" if 'vote_average' in movie else ""
                
                st.markdown(f"""
                <div class="movie-card">
                    <img src="{poster_url}" />
                    <div class="movie-title">{movie['title']}</div>
                    <div class="movie-metric">{rating_str}</div>
                    <div class="movie-meta">{genres_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.info("💡 Select a movie above and click **Recommend Similar** to see custom recommendations!")
