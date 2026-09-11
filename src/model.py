import os
import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer

# Initialize stemmer
ps = PorterStemmer()

def stem(text):
    if not isinstance(text, str):
        return ""
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)

def main():
    print("Starting feature engineering and model training...")
    
    # Paths
    input_path = os.path.join("data", "preprocessed_movies.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}! Run preprocess.py first.")
        
    # Load dataset
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} movies for training.")
    
    # Safeguard against NaNs
    df['tags'] = df['tags'].fillna('')
    
    # Apply Porter stemming on tags
    print("Applying stemming on tags...")
    df['tags_stemmed'] = df['tags'].apply(stem)
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # 1. Vectorization with CountVectorizer
    print("Vectorizing using CountVectorizer (Bag of Words)...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors_cv = cv.fit_transform(df['tags_stemmed']).toarray()
    
    print("Computing Cosine Similarity for CountVectorizer...")
    similarity_cv = cosine_similarity(vectors_cv).astype('float32')
    
    # 2. Vectorization with TfidfVectorizer (Bonus!)
    print("Vectorizing using TfidfVectorizer...")
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    vectors_tfidf = tfidf.fit_transform(df['tags_stemmed']).toarray()
    
    print("Computing Cosine Similarity for TfidfVectorizer...")
    similarity_tfidf = cosine_similarity(vectors_tfidf).astype('float32')
    
    # Data to save (exclude the raw tags and lists to keep it lightweight)
    df_to_save = df[['movie_id', 'title', 'overview', 'genres_original', 'cast_original', 'director_original', 'popularity', 'vote_average']]
    
    # Save the models
    movies_dict_path = os.path.join("models", "movies_dict.pkl")
    similarity_cv_path = os.path.join("models", "similarity_cv.pkl")
    similarity_tfidf_path = os.path.join("models", "similarity_tfidf.pkl")
    
    print("Saving models to 'models/' directory...")
    
    # Save as records list to ensure pandas version compatibility during loading
    with open(movies_dict_path, 'wb') as f:
        pickle.dump(df_to_save.to_dict(orient='records'), f)
        
    with open(similarity_cv_path, 'wb') as f:
        pickle.dump(similarity_cv, f)
        
    with open(similarity_tfidf_path, 'wb') as f:
        pickle.dump(similarity_tfidf, f)
        
    print("Training completed and models saved successfully!")

if __name__ == "__main__":
    main()
