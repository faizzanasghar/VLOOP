import os
import pandas as pd
import ast

def convert_genres_keywords(text):
    if pd.isna(text):
        return []
    try:
        return [item['name'] for item in ast.literal_eval(text)]
    except (ValueError, SyntaxError):
        return []

def convert_cast(text):
    if pd.isna(text):
        return []
    try:
        return [item['name'] for item in ast.literal_eval(text)[:3]]
    except (ValueError, SyntaxError):
        return []

def fetch_director(text):
    if pd.isna(text):
        return []
    try:
        for item in ast.literal_eval(text):
            if item.get('job') == 'Director':
                return [item['name']]
        return []
    except (ValueError, SyntaxError):
        return []

def collapse_spaces(lst):
    return [x.replace(" ", "") for x in lst]

def main():
    print("Starting data preprocessing...")
    
    # Check paths
    movies_path = os.path.join("data", "tmdb_5000_movies.csv")
    credits_path = os.path.join("data", "tmdb_5000_credits.csv")
    
    if not os.path.exists(movies_path) or not os.path.exists(credits_path):
        # Fallback to current directory if not moved yet
        if os.path.exists("tmdb_5000_movies.csv") and os.path.exists("tmdb_5000_credits.csv"):
            movies_path = "tmdb_5000_movies.csv"
            credits_path = "tmdb_5000_credits.csv"
            print("Found datasets in root directory. Preprocessing will proceed.")
        else:
            raise FileNotFoundError("TMDB dataset files not found!")

    # Load datasets
    movies = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)
    
    print(f"Loaded {len(movies)} movies and {len(credits)} credits.")
    
    # Merge datasets on title
    movies = movies.merge(credits, on="title")
    print(f"Merged dataset shape: {movies.shape}")
    
    # Select relevant columns
    # We select 'id' (which will be movie_id) and other required columns.
    # Note that credits has 'movie_id' and movies has 'id'. 
    # Let's keep both or rename 'id' to 'movie_id'.
    movies = movies[['id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'popularity', 'vote_average']]
    movies.rename(columns={'id': 'movie_id'}, inplace=True)
    
    # Handle missing values in overview
    movies['overview'] = movies['overview'].fillna('')
    
    # Convert JSON columns into python lists
    movies['genres_clean'] = movies['genres'].apply(convert_genres_keywords)
    movies['keywords_clean'] = movies['keywords'].apply(convert_genres_keywords)
    movies['cast_clean'] = movies['cast'].apply(convert_cast)
    movies['director_clean'] = movies['crew'].apply(fetch_director)
    
    # Keep the original genres, cast, and directors for UI searching and details
    movies['genres_original'] = movies['genres_clean'].copy()
    movies['cast_original'] = movies['cast_clean'].copy()
    movies['director_original'] = movies['director_clean'].copy()
    
    # Collapse spaces (e.g. "Science Fiction" -> "ScienceFiction")
    movies['genres_clean'] = movies['genres_clean'].apply(collapse_spaces)
    movies['keywords_clean'] = movies['keywords_clean'].apply(collapse_spaces)
    movies['cast_clean'] = movies['cast_clean'].apply(collapse_spaces)
    movies['director_clean'] = movies['director_clean'].apply(collapse_spaces)
    
    # Split overview text into list of words
    movies['overview_words'] = movies['overview'].apply(lambda x: x.split())
    
    # Create tags column
    movies['tags_list'] = (
        movies['overview_words'] + 
        movies['genres_clean'] + 
        movies['keywords_clean'] + 
        movies['cast_clean'] + 
        movies['director_clean']
    )
    
    # Convert tags list back to string
    movies['tags'] = movies['tags_list'].apply(lambda x: " ".join(x))
    movies['tags'] = movies['tags'].apply(lambda x: x.lower())
    
    # Select clean output columns
    preprocessed_df = movies[['movie_id', 'title', 'overview', 'genres_original', 'cast_original', 'director_original', 'tags', 'popularity', 'vote_average']]
    
    # Create data directory if it does not exist
    os.makedirs("data", exist_ok=True)
    
    # Save the preprocessed data
    output_path = os.path.join("data", "preprocessed_movies.csv")
    preprocessed_df.to_csv(output_path, index=False)
    print(f"Preprocessed data saved to {output_path}. Shape: {preprocessed_df.shape}")

if __name__ == "__main__":
    main()
