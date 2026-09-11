import os
import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer

# Initialize stemmer
ps = PorterStemmer()

TOP_N = 50          # store top-50 similar movies per movie
BATCH_SIZE = 200    # process 200 rows at a time to limit peak RAM


def stem(text):
    if not isinstance(text, str):
        return ""
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)


def compute_top_n_similarity(vectors, top_n=TOP_N, batch_size=BATCH_SIZE):
    """
    Compute cosine similarity in row-batches and keep only the
    top-N most similar indices + scores for each movie.
    Returns a dict: {movie_idx: [(similar_idx, score), ...]}
    Peak RAM ≈ batch_size × n_movies × 4 bytes (float32) — e.g. ~4 MB per batch.
    """
    n = vectors.shape[0]
    top_indices = {}

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        # batch_sim shape: (batch_size, n_movies)
        batch_sim = cosine_similarity(vectors[start:end], vectors).astype("float32")

        for local_i, row in enumerate(batch_sim):
            movie_idx = start + local_i
            # Argsort descending — skip self (score == 1.0 at own index)
            ranked = np.argsort(row)[::-1]
            results = []
            for j in ranked:
                if int(j) == movie_idx:
                    continue
                results.append((int(j), float(row[j])))
                if len(results) == top_n:
                    break
            top_indices[movie_idx] = results

        del batch_sim  # free memory immediately after each batch

    return top_indices


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

    # 1. CountVectorizer
    print("Vectorizing using CountVectorizer...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors_cv = cv.fit_transform(df['tags_stemmed']).toarray().astype("float32")

    print("Computing top-N similarity for CountVectorizer (batch mode)...")
    similarity_cv = compute_top_n_similarity(vectors_cv)
    del vectors_cv  # free RAM immediately

    # 2. TF-IDF
    print("Vectorizing using TfidfVectorizer...")
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    vectors_tfidf = tfidf.fit_transform(df['tags_stemmed']).toarray().astype("float32")

    print("Computing top-N similarity for TfidfVectorizer (batch mode)...")
    similarity_tfidf = compute_top_n_similarity(vectors_tfidf)
    del vectors_tfidf  # free RAM immediately

    # Data to save
    df_to_save = df[['movie_id', 'title', 'overview', 'genres_original',
                      'cast_original', 'director_original', 'popularity', 'vote_average']]

    # Save models
    print("Saving models to 'models/' directory...")
    with open(os.path.join("models", "movies_dict.pkl"), 'wb') as f:
        pickle.dump(df_to_save.to_dict(orient='records'), f)

    with open(os.path.join("models", "similarity_cv.pkl"), 'wb') as f:
        pickle.dump(similarity_cv, f)

    with open(os.path.join("models", "similarity_tfidf.pkl"), 'wb') as f:
        pickle.dump(similarity_tfidf, f)

    print("Training completed and models saved successfully!")


if __name__ == "__main__":
    main()
