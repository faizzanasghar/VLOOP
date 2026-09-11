import os
import pickle
import pandas as pd
import numpy as np

class MovieRecommender:
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.df = None
        self.similarity_cv = None
        self.similarity_tfidf = None
        self.load_models()

    def load_models(self):
        movies_dict_path = os.path.join(self.models_dir, "movies_dict.pkl")
        similarity_cv_path = os.path.join(self.models_dir, "similarity_cv.pkl")
        similarity_tfidf_path = os.path.join(self.models_dir, "similarity_tfidf.pkl")

        if not (os.path.exists(movies_dict_path) and 
                os.path.exists(similarity_cv_path) and 
                os.path.exists(similarity_tfidf_path)):
            raise FileNotFoundError("Model pickle files not found! Please run preprocess.py and model.py first.")

        with open(movies_dict_path, 'rb') as f:
            records = pickle.load(f)
            self.df = pd.DataFrame(records)
            
            # Parse genres_original if it is stored as string representation of lists
            import ast
            def parse_genres(x):
                if isinstance(x, str):
                    try:
                        return ast.literal_eval(x)
                    except:
                        return []
                elif isinstance(x, list):
                    return x
                return []
            self.df['genres_original'] = self.df['genres_original'].apply(parse_genres)
            self.df['cast_original'] = self.df['cast_original'].apply(parse_genres)
            self.df['director_original'] = self.df['director_original'].apply(parse_genres)

        with open(similarity_cv_path, 'rb') as f:
            self.similarity_cv = pickle.load(f)

        with open(similarity_tfidf_path, 'rb') as f:
            self.similarity_tfidf = pickle.load(f)
            
        print("Recommender models loaded successfully.")

    def get_all_titles(self):
        if self.df is not None:
            return self.df['title'].tolist()
        return []

    def get_all_genres(self):
        if self.df is None:
            return []
        
        genres_set = set()
        for genres in self.df['genres_original']:
            if isinstance(genres, list):
                genres_set.update(genres)
        return sorted(list(genres_set))

    def recommend(self, movie_title, method="Count Vectorizer", genre_filter=None, top_n=5):
        """
        Recommends top_n similar movies based on input title.
        
        Parameters:
        - movie_title (str): Title of the movie.
        - method (str): "Count Vectorizer" or "TF-IDF".
        - genre_filter (str): Genre name to filter recommendations.
        - top_n (int): Number of recommendations to return.
        
        Returns:
        - list of dicts: List containing recommended movie records (movie_id, title, overview, genres_original)
        """
        if self.df is None:
            raise ValueError("Data not loaded!")

        # Select similarity matrix
        if method == "TF-IDF":
            similarity_matrix = self.similarity_tfidf
        else:
            similarity_matrix = self.similarity_cv

        # Find movie index
        # 1. Exact case-insensitive match
        match = self.df[self.df['title'].str.lower() == movie_title.lower()]
        
        # 2. Substring match fallback if exact match not found
        if match.empty:
            match = self.df[self.df['title'].str.lower().str.contains(movie_title.lower())]
            
        if match.empty:
            raise KeyError(f"Movie '{movie_title}' not found in dataset.")

        movie_idx = match.index[0]
        searched_title = self.df.iloc[movie_idx]['title']
        
        # Get similarities for the movie
        distances = similarity_matrix[movie_idx]
        
        # Sort based on similarity scores
        # movies_list is a list of tuples: (index, similarity_score)
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])
        
        recommended_movies = []
        for idx, score in movies_list:
            # Skip the searched movie itself
            if idx == movie_idx:
                continue
                
            candidate = self.df.iloc[idx].to_dict()
            
            # Apply genre filter if specified
            if genre_filter:
                genres = candidate.get('genres_original', [])
                if not isinstance(genres, list):
                    genres = []
                
                # Check case-insensitively
                if genre_filter.lower() not in [g.lower() for g in genres]:
                    continue
            
            # Add similarity score to output data
            candidate['similarity_score'] = float(score)
            recommended_movies.append(candidate)
            
            if len(recommended_movies) == top_n:
                break
                
        return searched_title, recommended_movies

# Quick self-test logic
if __name__ == "__main__":
    try:
        recommender = MovieRecommender()
        print("Self-Test Recommendation for 'Avatar':")
        orig, recs = recommender.recommend("Avatar", method="Count Vectorizer")
        print(f"Original matched title: {orig}")
        for r in recs:
            print(f"- {r['title']} (Similarity: {r['similarity_score']:.4f})")
    except Exception as e:
        print(f"Self-test failed (expected if models not trained yet): {e}")
