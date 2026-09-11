import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Play, Plus, Check, ThumbsUp, ThumbsDown, 
  X, ChevronLeft, ChevronRight, Info, Sparkles, Heart, UserCircle 
} from 'lucide-react';
import SplashLoader from './components/SplashLoader';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000/api';
const ACTOR_PRESETS = [
  'Leonardo DiCaprio',
  'Johnny Depp',
  'Christian Bale',
  'Scarlett Johansson',
  'Brad Pitt'
];

export default function App() {
  // Navigation & Page State
  const [activeTab, setActiveTab] = useState('home');
  const [scrolled, setScrolled] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [showSplash, setShowSplash] = useState(true);
  
  // Movie Data Lists
  const [trendingMovies, setTrendingMovies] = useState([]);
  const [popularMovies, setPopularMovies] = useState([]);
  const [topRatedMovies, setTopRatedMovies] = useState([]);
  const [watchlistRecommendations, setWatchlistRecommendations] = useState([]);
  const [watchlistRecSourceTitle, setWatchlistRecSourceTitle] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  
  // Watchlist & Interactive Preferences
  const [watchlist, setWatchlist] = useState([]);
  const [likedMovies, setLikedMovies] = useState([]);
  const [dislikedMovies, setDislikedMovies] = useState([]);
  const [selectedActor, setSelectedActor] = useState('');
  
  // Auth / modal state
  const [user, setUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState(null);
  
  // Selected Movie / Detail Modal State
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [similarityMethod, setSimilarityMethod] = useState('Count Vectorizer');
  const [selectedGenreFilter, setSelectedGenreFilter] = useState('All Genres');
  const [genresList, setGenresList] = useState([]);
  const [modalRecommendations, setModalRecommendations] = useState([]);
  const [isModalLoading, setIsModalLoading] = useState(false);
  
  // Loading states
  const [loading, setLoading] = useState(true);

  // Sync scroll state for navbar background transparency
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 50) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);


  // Load Watchlist, Likes, and user session from LocalStorage on mount
  useEffect(() => {
    const savedWatchlist = localStorage.getItem('vloop_watchlist');
    if (savedWatchlist) {
      try { setWatchlist(JSON.parse(savedWatchlist)); } catch (e) {}
    }

    const savedLikes = localStorage.getItem('vloop_likes');
    if (savedLikes) {
      try { setLikedMovies(JSON.parse(savedLikes)); } catch (e) {}
    }

    const savedDislikes = localStorage.getItem('vloop_dislikes');
    if (savedDislikes) {
      try { setDislikedMovies(JSON.parse(savedDislikes)); } catch (e) {}
    }

    const savedUser = localStorage.getItem('vloop_user');
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)); } catch (e) {}
    }
  }, []);

  const persistLocalWatchlist = (updatedWatchlist) => {
    setWatchlist(updatedWatchlist);
    localStorage.setItem('vloop_watchlist', JSON.stringify(updatedWatchlist));
  };

  const persistLikes = (updatedLikes) => {
    setLikedMovies(updatedLikes);
    localStorage.setItem('vloop_likes', JSON.stringify(updatedLikes));
  };

  const persistDislikes = (updatedDislikes) => {
    setDislikedMovies(updatedDislikes);
    localStorage.setItem('vloop_dislikes', JSON.stringify(updatedDislikes));
  };

  const persistUser = (userData) => {
    setUser(userData);
    localStorage.setItem('vloop_user', JSON.stringify(userData));
  };

  // Fetch initial movie lists & genres
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        const [resTrend, resPop, resTop, resGenres] = await Promise.all([
          fetch(`${API_BASE}/movies/trending`).then(r => r.json()),
          fetch(`${API_BASE}/movies/popular`).then(r => r.json()),
          fetch(`${API_BASE}/movies/top-rated`).then(r => r.json()),
          fetch(`${API_BASE}/genres`).then(r => r.json())
        ]);
        
        setTrendingMovies(resTrend || []);
        setPopularMovies(resPop || []);
        setTopRatedMovies(resTop || []);
        setGenresList(resGenres || []);
      } catch (err) {
        console.error('Failed to fetch home catalogs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  // Generate Personalized Recommendations based on watchlist
  useEffect(() => {
    const fetchPersonalizedRecommendations = async () => {
      // Pick source for personalization:
      // If watchlist is not empty, use the latest item in watchlist.
      // Otherwise, use a default high-quality popular seed (e.g. Avatar)
      let seedTitle = '';
      if (watchlist.length > 0) {
        seedTitle = watchlist[watchlist.length - 1].title;
        setWatchlistRecSourceTitle(`Because you added "${seedTitle}"`);
      } else {
        seedTitle = 'Interstellar';
        setWatchlistRecSourceTitle('Trending Recommendations');
      }

      try {
        const response = await fetch(
          `${API_BASE}/recommend?title=${encodeURIComponent(seedTitle)}&method=TF-IDF&top_n=10`
        );
        if (response.ok) {
          const data = await response.json();
          setWatchlistRecommendations(data.recommendations || []);
        } else {
          // If seed fails, fallback to general popular list
          setWatchlistRecommendations(popularMovies.slice(0, 10));
        }
      } catch (e) {
        setWatchlistRecommendations([]);
      }
    };

    if (popularMovies.length > 0) {
      fetchPersonalizedRecommendations();
    }
  }, [watchlist, popularMovies]);

  const searchMovies = async (query) => {
    if (!query || query.trim().length === 0) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data || []);
      }
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  // Handle Search input change
  useEffect(() => {
    if (searchQuery.trim().length === 0) {
      setSearchResults([]);
      return;
    }

    const delayDebounce = setTimeout(() => {
      searchMovies(searchQuery);
    }, 300); // 300ms debounce

    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  // Handle selected movie recommendation updates (inside details modal)
  useEffect(() => {
    if (!selectedMovie) return;

    const fetchModalRecs = async () => {
      setIsModalLoading(true);
      try {
        let genreParam = selectedGenreFilter === 'All Genres' ? '' : `&genre=${encodeURIComponent(selectedGenreFilter)}`;
        const response = await fetch(
          `${API_BASE}/recommend?title=${encodeURIComponent(selectedMovie.title)}&method=${encodeURIComponent(similarityMethod)}${genreParam}&top_n=8`
        );
        if (response.ok) {
          const data = await response.json();
          setModalRecommendations(data.recommendations || []);
        } else {
          setModalRecommendations([]);
        }
      } catch (err) {
        console.error('Failed to load similar movies in modal:', err);
        setModalRecommendations([]);
      } finally {
        setIsModalLoading(false);
      }
    };

    fetchModalRecs();
  }, [selectedMovie, similarityMethod, selectedGenreFilter]);

  // Watchlist Toggle Helper
  const toggleWatchlist = (movie) => {
    let updated;
    const isExist = watchlist.some(m => m.movie_id === movie.movie_id);
    if (isExist) {
      updated = watchlist.filter(m => m.movie_id !== movie.movie_id);
    } else {
      updated = [...watchlist, movie];
    }
    persistLocalWatchlist(updated);
    if (user) {
      syncWatchlistToBackend(user.username, updated);
    }
  };

  // Like Toggle Helper
  const toggleLike = (movieId) => {
    let updated;
    if (likedMovies.includes(movieId)) {
      updated = likedMovies.filter(id => id !== movieId);
    } else {
      updated = [...likedMovies, movieId];
      const cleanedDislikes = dislikedMovies.filter(id => id !== movieId);
      setDislikedMovies(cleanedDislikes);
      persistDislikes(cleanedDislikes);
    }
    persistLikes(updated);
  };

  // Dislike Toggle Helper
  const toggleDislike = (movieId) => {
    let updated;
    if (dislikedMovies.includes(movieId)) {
      updated = dislikedMovies.filter(id => id !== movieId);
    } else {
      updated = [...dislikedMovies, movieId];
      const cleanedLikes = likedMovies.filter(id => id !== movieId);
      setLikedMovies(cleanedLikes);
      persistLikes(cleanedLikes);
    }
    persistDislikes(updated);
  };

  const syncWatchlistToBackend = async (username, currentWatchlist) => {
    try {
      await fetch(`${API_BASE}/auth/watchlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, watchlist: currentWatchlist }),
      });
    } catch (err) {
      console.warn('Could not sync watchlist to backend:', err);
    }
  };

  const handleAuthSuccess = (userData, backendWatchlist = []) => {
    persistUser(userData);
    if (backendWatchlist.length > 0) {
      persistLocalWatchlist(backendWatchlist);
    }
    setIsAuthModalOpen(false);
  };

  const handleRegister = async () => {
    setAuthError(null);
    if (!authUsername || !authPassword) {
      setAuthError('Please enter username and password');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername, password: authPassword }),
      });
      const data = await response.json();
      if (!response.ok) {
        setAuthError(data.detail || 'Registration failed');
        return;
      }
      handleAuthSuccess({ username: authUsername });
    } catch (err) {
      setAuthError('Unable to register at this time');
    }
  };

  const handleLogin = async () => {
    setAuthError(null);
    if (!authUsername || !authPassword) {
      setAuthError('Please enter username and password');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername, password: authPassword }),
      });
      const data = await response.json();
      if (!response.ok) {
        setAuthError(data.detail || 'Login failed');
        return;
      }
      handleAuthSuccess({ username: authUsername }, data.watchlist || []);
    } catch (err) {
      setAuthError('Unable to login at this time');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('vloop_user');
  };

  // Open Details Modal Helper
  const openMovieModal = (movie) => {
    setSelectedMovie(movie);
    setSimilarityMethod('Count Vectorizer'); // reset method
    setSelectedGenreFilter('All Genres'); // reset genre filter
  };

  // Close Details Modal Helper
  const closeMovieModal = () => {
    setSelectedMovie(null);
    setModalRecommendations([]);
  };

  // Hero movie (curated popular item from popular list)
  const heroMovie = popularMovies[1] || {
    movie_id: 19995,
    title: 'Avatar',
    overview: 'In the 22nd century, a paraplegic Marine is dispatched to the moon Pandora on a unique mission, but becomes torn between following orders and protecting an alien civilization.',
    genres: ['Action', 'Adventure', 'Fantasy', 'Science Fiction'],
    vote_average: 7.2,
    poster_url: 'https://image.tmdb.org/t/p/w500/kyeE2m2Xw6n42Cem56WTAzR46WL.jpg'
  };

  return (
    <div className="app-container">
      {showSplash && <SplashLoader onComplete={() => setShowSplash(false)} />}
      
      {/* 🧭 NAVIGATION BAR */}
      <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
        <div className="nav-left">
          <a href="#" className="logo brand-gradient" onClick={() => { setActiveTab('home'); setSearchQuery(''); }}>
            Vloop
          </a>
          <ul className="nav-links">
            <li 
              className={`nav-item ${activeTab === 'home' && searchQuery === '' ? 'active' : ''}`}
              onClick={() => { setActiveTab('home'); setSearchQuery(''); }}
            >
              Home
            </li>
            <li 
              className={`nav-item ${activeTab === 'watchlist' && searchQuery === '' ? 'active' : ''}`}
              onClick={() => { setActiveTab('watchlist'); setSearchQuery(''); }}
            >
              My List
            </li>
          </ul>
        </div>

        <div className="nav-right">
          {/* Expanding search container */}
          <div className={`search-container ${isSearchExpanded || searchQuery ? 'expanded' : ''}`}>
            <button className="search-btn" onClick={() => setIsSearchExpanded(!isSearchExpanded)}>
              <Search size={18} />
            </button>
            <input 
              type="text" 
              className="search-input" 
              placeholder="Search titles, genres, actors..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchExpanded(true)}
              onBlur={() => { if (!searchQuery) setIsSearchExpanded(false); }}
            />
            {searchQuery && (
              <button className="search-btn" onClick={() => setSearchQuery('')}>
                <X size={15} />
              </button>
            )}
          </div>
          
          {user ? (
            <div className="nav-profile-group">
              <button className="profile-btn" onClick={() => setActiveTab('watchlist')}>
                <UserCircle size={20} style={{ marginRight: '6px' }} /> {user.username}
              </button>
              <button className="logout-btn" onClick={handleLogout} style={{ marginLeft: '10px', background: 'transparent', color: '#fff', border: '1px solid rgba(255,255,255,0.3)', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>
                Logout
              </button>
            </div>
          ) : (
            <button className="auth-btn" onClick={() => { setIsAuthModalOpen(true); setAuthMode('login'); }}>
              Login / Signup
            </button>
          )}
        </div>
      </nav>

      {/* 🔍 SEARCH RESULTS GRID */}
      {searchQuery ? (
        <div className="search-grid-container">
          <h2 className="search-grid-title">
            Search results for: <span>{searchQuery}</span>
          </h2>
          {searchResults.length > 0 ? (
            <div className="movie-grid">
              {searchResults.map(movie => (
                <MovieCard 
                  key={movie.movie_id} 
                  movie={movie} 
                  onPlay={openMovieModal} 
                  watchlist={watchlist} 
                  onWatchlistToggle={toggleWatchlist}
                  likedMovies={likedMovies}
                  dislikedMovies={dislikedMovies}
                  onLikeToggle={toggleLike}
                  onDislikeToggle={toggleDislike}
                />
              ))}
            </div>
          ) : (
            <div className="search-fallback">
              <Sparkles size={48} style={{ color: 'var(--primary-red)', marginBottom: '15px', opacity: 0.8 }} />
              <h3>No matching movies found</h3>
              <p style={{ marginTop: '5px' }}>Try typing another title, keyword, or character name.</p>
            </div>
          )}
        </div>
      ) : activeTab === 'watchlist' ? (
        /* 👤 WATCHLIST (MY LIST) TAB */
        <div className="favorites-container">
          <h2 className="search-grid-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Heart size={24} fill="var(--primary-red)" color="var(--primary-red)" /> My Watchlist ({watchlist.length})
          </h2>
          {watchlist.length > 0 ? (
            <div className="movie-grid">
              {watchlist.map(movie => (
                <MovieCard 
                  key={movie.movie_id} 
                  movie={movie} 
                  onPlay={openMovieModal} 
                  watchlist={watchlist} 
                  onWatchlistToggle={toggleWatchlist}
                  likedMovies={likedMovies}
                  dislikedMovies={dislikedMovies}
                  onLikeToggle={toggleLike}
                  onDislikeToggle={toggleDislike}
                />
              ))}
            </div>
          ) : (
            <div className="search-fallback">
              <Plus size={48} style={{ color: 'var(--text-secondary)', marginBottom: '15px', opacity: 0.6 }} />
              <h3>Your Watchlist is empty</h3>
              <p style={{ marginTop: '5px' }}>Click the '+' icon on any movie card to add it to your list.</p>
            </div>
          )}
        </div>
      ) : (
        /* 🏠 HOME VIEW */
        <>
          {/* Hero Landing Banner */}
          <HeroSection movie={heroMovie} onDetailsClick={openMovieModal} onWatchlistToggle={toggleWatchlist} watchlist={watchlist} />

          {/* Core Movies Horizontal Carousels */}
          <div className="movie-section">
            {loading ? (
              // Shimmer loadings
              <>
                <SkeletonRow title="Trending Now" />
                <SkeletonRow title="Popular on Vloop" />
              </>
            ) : (
              <>
                {/* 1. Trending Now */}
                <MovieRow 
                  title="Trending Now" 
                  movies={trendingMovies} 
                  onPlayCard={openMovieModal} 
                  watchlist={watchlist}
                  onWatchlistToggle={toggleWatchlist}
                  likedMovies={likedMovies}
                  dislikedMovies={dislikedMovies}
                  onLikeToggle={toggleLike}
                  onDislikeToggle={toggleDislike}
                />

                {/* 2. Popular on CineMatch */}
                <MovieRow 
                  title="Popular on Vloop" 
                  movies={popularMovies} 
                  onPlayCard={openMovieModal} 
                  watchlist={watchlist}
                  onWatchlistToggle={toggleWatchlist}
                  likedMovies={likedMovies}
                  dislikedMovies={dislikedMovies}
                  onLikeToggle={toggleLike}
                  onDislikeToggle={toggleDislike}
                />

                {/* 3. Personalized Recommendation Engine Row */}
                {watchlistRecommendations.length > 0 && (
                  <MovieRow 
                    title="Recommended For You" 
                    subtitle={watchlistRecSourceTitle}
                    movies={watchlistRecommendations} 
                    onPlayCard={openMovieModal} 
                    watchlist={watchlist}
                    onWatchlistToggle={toggleWatchlist}
                    likedMovies={likedMovies}
                    dislikedMovies={dislikedMovies}
                    onLikeToggle={toggleLike}
                    onDislikeToggle={toggleDislike}
                  />
                )}

                {/* 4. Top Rated on CineMatch */}
                <MovieRow 
                  title="Top Rated Classics" 
                  movies={topRatedMovies} 
                  onPlayCard={openMovieModal} 
                  watchlist={watchlist}
                  onWatchlistToggle={toggleWatchlist}
                  likedMovies={likedMovies}
                  dislikedMovies={dislikedMovies}
                  onLikeToggle={toggleLike}
                  onDislikeToggle={toggleDislike}
                />

                {/* 5. Watchlist Quick Row if user has elements */}
                {watchlist.length > 0 && (
                  <MovieRow 
                    title="Recently Added to List" 
                    movies={[...watchlist].reverse()} 
                    onPlayCard={openMovieModal} 
                    watchlist={watchlist}
                    onWatchlistToggle={toggleWatchlist}
                    likedMovies={likedMovies}
                    dislikedMovies={dislikedMovies}
                    onLikeToggle={toggleLike}
                    onDislikeToggle={toggleDislike}
                  />
                )}
              </>
            )}
          </div>
        </>
      )}

      {/* 🎯 DETAIL OVERLAY MODAL */}
      <AnimatePresence>
        {selectedMovie && (
          <DetailModal 
            movie={selectedMovie} 
            onClose={closeMovieModal} 
            similarityMethod={similarityMethod}
            setSimilarityMethod={setSimilarityMethod}
            selectedGenreFilter={selectedGenreFilter}
            setSelectedGenreFilter={setSelectedGenreFilter}
            genresList={genresList}
            recommendations={modalRecommendations}
            isLoading={isModalLoading}
            watchlist={watchlist}
            onWatchlistToggle={toggleWatchlist}
            onSelectSimilarMovie={openMovieModal}
          />
        )}
      </AnimatePresence>

      {/* 🔐 AUTH MODAL */}
      <AnimatePresence>
        {isAuthModalOpen && (
          <div className="modal-backdrop" onClick={(e) => { if (e.target.className === 'modal-backdrop') setIsAuthModalOpen(false); }}>
            <motion.div 
              className="auth-modal-content"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{ background: '#181818', padding: '40px', borderRadius: '12px', width: '100%', maxWidth: '400px', position: 'relative' }}
            >
              <button className="modal-close-btn" onClick={() => setIsAuthModalOpen(false)}>
                <X size={20} />
              </button>
              <h2 style={{ color: '#fff', marginBottom: '20px', fontSize: '24px' }}>
                {authMode === 'login' ? 'Sign In' : 'Sign Up'}
              </h2>
              {authError && <div style={{ background: '#e50914', color: '#fff', padding: '10px', borderRadius: '4px', marginBottom: '15px', fontSize: '14px' }}>{authError}</div>}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <input 
                  type="text" 
                  placeholder="Username" 
                  value={authUsername} 
                  onChange={e => setAuthUsername(e.target.value)}
                  style={{ padding: '12px', borderRadius: '4px', border: 'none', background: '#333', color: '#fff', outline: 'none' }}
                />
                <input 
                  type="password" 
                  placeholder="Password" 
                  value={authPassword} 
                  onChange={e => setAuthPassword(e.target.value)}
                  style={{ padding: '12px', borderRadius: '4px', border: 'none', background: '#333', color: '#fff', outline: 'none' }}
                />
                <button 
                  onClick={authMode === 'login' ? handleLogin : handleRegister}
                  style={{ padding: '14px', background: '#e50914', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}
                >
                  {authMode === 'login' ? 'Sign In' : 'Sign Up'}
                </button>
              </div>
              <div style={{ marginTop: '20px', color: '#aaa', fontSize: '14px', textAlign: 'center' }}>
                {authMode === 'login' ? "New to Vloop? " : "Already have an account? "}
                <span 
                  onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setAuthError(null); }}
                  style={{ color: '#fff', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  {authMode === 'login' ? 'Sign up now.' : 'Sign in.'}
                </span>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ----------------------------------------------------
// 🎬 HERO BANNER COMPONENT
// ----------------------------------------------------
function HeroSection({ movie, onDetailsClick, onWatchlistToggle, watchlist }) {
  const isExist = watchlist.some(m => m.movie_id === movie.movie_id);
  
  // Custom backdrop resolution from TMDB
  const backdropUrl = movie.movie_id === 19995 
    ? "https://image.tmdb.org/t/p/original/tM4j4K1Dvcj7BD67ZAmCLLqH6c2.jpg" 
    : movie.poster_url;

  return (
    <div 
      className="hero-banner"
      style={{ backgroundImage: `url(${backdropUrl})` }}
    >
      <div className="hero-overlay"></div>
      <motion.div 
        className="hero-content"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      >
        <h1 className="hero-title">{movie.title}</h1>
        <div className="hero-meta">
          <span className="match-tag">98% Match</span>
          <span className="rating-tag">⭐ {movie.vote_average.toFixed(1)}</span>
          <span className="genre-tags">
            {Array.isArray(movie.genres) ? movie.genres.slice(0, 3).join(', ') : 'Sci-Fi'}
          </span>
        </div>
        <p className="hero-description">{movie.overview}</p>
        <div className="hero-buttons">
          <button className="btn btn-primary" onClick={() => onDetailsClick(movie)}>
            <Play size={18} fill="#fff" /> Play Details
          </button>
          <button className="btn btn-secondary" onClick={() => onWatchlistToggle(movie)}>
            {isExist ? <Check size={18} /> : <Plus size={18} />} Watchlist
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ----------------------------------------------------
// 🎞️ MOVIE ROW COMPONENT
// ----------------------------------------------------
function MovieRow({ 
  title, subtitle, movies, onPlayCard, watchlist, onWatchlistToggle, 
  likedMovies, dislikedMovies, onLikeToggle, onDislikeToggle 
}) {
  const rowRef = useRef(null);

  const scroll = (direction) => {
    if (rowRef.current) {
      const { scrollLeft, clientWidth } = rowRef.current;
      const scrollTo = direction === 'left' 
        ? scrollLeft - clientWidth * 0.75 
        : scrollLeft + clientWidth * 0.75;
      rowRef.current.scrollTo({ left: scrollTo, behavior: 'smooth' });
    }
  };

  return (
    <div className="row-container">
      <div style={{ display: 'flex', alignItems: 'baseline' }}>
        <h3 className="row-header">{title}</h3>
        {subtitle && <span className="row-header-accent">{subtitle}</span>}
      </div>
      
      <button className="slider-arrow left" onClick={() => scroll('left')}>
        <ChevronLeft size={24} />
      </button>

      <div className="scroll-container" ref={rowRef}>
        {movies.map(movie => (
          <MovieCard 
            key={movie.movie_id} 
            movie={movie} 
            onPlay={onPlayCard}
            watchlist={watchlist}
            onWatchlistToggle={onWatchlistToggle}
            likedMovies={likedMovies}
            dislikedMovies={dislikedMovies}
            onLikeToggle={onLikeToggle}
            onDislikeToggle={onDislikeToggle}
          />
        ))}
      </div>

      <button className="slider-arrow right" onClick={() => scroll('right')}>
        <ChevronRight size={24} />
      </button>
    </div>
  );
}

// ----------------------------------------------------
// 🎞️ MOVIE CARD COMPONENT
// ----------------------------------------------------
function MovieCard({ 
  movie, onPlay, watchlist, onWatchlistToggle, 
  likedMovies, dislikedMovies, onLikeToggle, onDislikeToggle 
}) {
  const isWatchlist = watchlist.some(m => m.movie_id === movie.movie_id);
  const isLiked = likedMovies.includes(movie.movie_id);
  const isDisliked = dislikedMovies.includes(movie.movie_id);

  return (
    <motion.div 
      className="movie-card-wrapper"
      whileHover={{ 
        scale: 1.12, 
        y: -10, 
        zIndex: 50,
        transition: { duration: 0.3, ease: 'easeInOut' }
      }}
    >
      <div className="card-img-container">
        <img 
          src={movie.poster_url || "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=300"} 
          className="card-img" 
          alt={movie.title}
          loading="lazy"
        />
        
        {/* Card hover overlay details */}
        <div className="card-overlay">
          <h4 className="card-title">{movie.title}</h4>
          
          <div className="card-meta">
            {movie.similarity_score !== undefined ? (
              <span className="card-match">{(movie.similarity_score * 100).toFixed(0)}% Match</span>
            ) : (
              <span className="card-match">{(85 + (movie.vote_average * 2)).toFixed(0)}% Match</span>
            )}
            <span className="card-rating">⭐ {movie.vote_average.toFixed(1)}</span>
          </div>

          <div className="card-genres">
            {Array.isArray(movie.genres) ? movie.genres.slice(0, 2).join(' • ') : ''}
          </div>

          <div className="card-actions">
            <button className="icon-btn active" onClick={(e) => { e.stopPropagation(); onPlay(movie); }}>
              <Play size={12} fill="#fff" />
            </button>
            <button 
              className={`icon-btn ${isWatchlist ? 'active' : ''}`} 
              onClick={(e) => { e.stopPropagation(); onWatchlistToggle(movie); }}
              title={isWatchlist ? "Remove from watchlist" : "Add to watchlist"}
            >
              {isWatchlist ? <Check size={12} /> : <Plus size={12} />}
            </button>
            <button 
              className={`icon-btn ${isLiked ? 'active' : ''}`} 
              onClick={(e) => { e.stopPropagation(); onLikeToggle(movie.movie_id); }}
              title="Like"
            >
              <ThumbsUp size={12} fill={isLiked ? "#fff" : "none"} />
            </button>
            <button 
              className={`icon-btn ${isDisliked ? 'active' : ''}`} 
              onClick={(e) => { e.stopPropagation(); onDislikeToggle(movie.movie_id); }}
              title="Not for me"
            >
              <ThumbsDown size={12} fill={isDisliked ? "#fff" : "none"} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ----------------------------------------------------
// 🎯 MOVIE DETAIL MODAL
// ----------------------------------------------------
function DetailModal({ 
  movie, onClose, similarityMethod, setSimilarityMethod, 
  selectedGenreFilter, setSelectedGenreFilter, genresList,
  recommendations, isLoading, watchlist, onWatchlistToggle, onSelectSimilarMovie 
}) {
  const isWatchlist = watchlist.some(m => m.movie_id === movie.movie_id);

  // Close when clicking background backdrop
  const handleBackdropClick = (e) => {
    if (e.target.className === 'modal-backdrop') {
      onClose();
    }
  };

  return (
    <motion.div 
      className="modal-backdrop"
      onClick={handleBackdropClick}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="modal-content-wrapper"
        initial={{ scale: 0.9, y: 50 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 50 }}
        transition={{ type: 'spring', damping: 25, stiffness: 220 }}
      >
        <button className="modal-close-btn" onClick={onClose}>
          <X size={20} />
        </button>

        {/* Modal Hero Banner */}
        <div 
          className="modal-hero"
          style={{ backgroundImage: `url(${movie.poster_url})` }}
        >
          <div className="modal-hero-overlay"></div>
          <div className="modal-hero-content">
            <h2 className="modal-title">{movie.title}</h2>
            <div className="hero-buttons">
              <button className="btn btn-primary" onClick={() => alert("Simulating play movie. Recommender connected successfully!")}>
                <Play size={18} fill="#fff" /> Play Movie
              </button>
              <button className="btn btn-secondary" onClick={() => onWatchlistToggle(movie)}>
                {isWatchlist ? <Check size={18} /> : <Plus size={18} />} Watchlist
              </button>
            </div>
          </div>
        </div>

        {/* Modal Info & Similarity Controller */}
        <div className="modal-body">
          <div className="modal-info-grid">
            <div className="modal-synopsis">
              <h3 style={{ marginBottom: '10px', color: '#fff' }}>Synopsis</h3>
              <p>{movie.overview || "No overview available for this movie."}</p>
            </div>
            
            <div className="modal-metadata">
              <div className="meta-item">
                <strong>Match Score:</strong> <span className="match-tag">97% Match</span>
              </div>
              <div className="meta-item">
                <strong>Rating:</strong> ⭐ {movie.vote_average.toFixed(1)}/10
              </div>
              <div className="meta-item">
                <strong>Popularity Rank:</strong> {movie.popularity.toFixed(1)} pts
              </div>
              {movie.director && movie.director.length > 0 && (
                <div className="meta-item">
                  <strong>Director:</strong> {movie.director.join(', ')}
                </div>
              )}
              {movie.cast && movie.cast.length > 0 && (
                <div className="meta-item">
                  <strong>Cast:</strong> {movie.cast.slice(0, 5).join(', ')}
                </div>
              )}
              <div>
                {Array.isArray(movie.genres) && movie.genres.map(genre => (
                  <span key={genre} className="genre-badge">{genre}</span>
                ))}
              </div>
            </div>
          </div>

          {/* ⚙️ RECOMMENDER CONFIGURATION CONTROLS */}
          <div className="recommender-settings-panel">
            <div className="settings-header">
              <Sparkles size={18} color="var(--primary-red)" />
              <span>Real-Time Recommender Configuration</span>
            </div>
            <div className="settings-controls">
              <div className="control-group">
                <span className="control-label">SIMILARITY PIPELINE</span>
                <select 
                  className="select-control"
                  value={similarityMethod}
                  onChange={(e) => setSimilarityMethod(e.target.value)}
                >
                  <option value="Count Vectorizer">Count Vectorizer (Bag of Words)</option>
                  <option value="TF-IDF">TF-IDF Vectorizer (Weighted terms)</option>
                </select>
              </div>

              <div className="control-group">
                <span className="control-label">GENRE FILTER</span>
                <select 
                  className="select-control"
                  value={selectedGenreFilter}
                  onChange={(e) => setSelectedGenreFilter(e.target.value)}
                >
                  <option value="All Genres">All Genres</option>
                  {genresList.map(genre => (
                    <option key={genre} value={genre}>{genre}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 🎞️ DYNAMIC RECOMMENDATIONS WITHIN MODAL */}
          <div className="modal-recs-title">
            Similar Movies You May Like
          </div>
          {isLoading ? (
            <div className="modal-recs-grid">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="rec-card-mini skeleton" style={{ height: '240px' }}></div>
              ))}
            </div>
          ) : recommendations.length > 0 ? (
            <div className="modal-recs-grid">
              {recommendations.map(rec => (
                <div 
                  key={rec.movie_id} 
                  className="rec-card-mini"
                  onClick={() => onSelectSimilarMovie(rec)}
                >
                  <img src={rec.poster_url} alt={rec.title} />
                  <div className="rec-card-info">
                    <span className="rec-card-title">{rec.title}</span>
                    <span className="rec-card-score">{(rec.similarity_score * 100).toFixed(0)}% Match</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="search-fallback" style={{ padding: '20px 0' }}>
              <p>No similar movies found matching the active genre filter.</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// ----------------------------------------------------
// 💀 LOADING SKELETON ROW COMPONENT
// ----------------------------------------------------
function SkeletonRow({ title }) {
  return (
    <div style={{ marginBottom: '35px' }}>
      <h3 className="row-header">{title}</h3>
      <div className="skeleton-row">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="skeleton-card skeleton"></div>
        ))}
      </div>
    </div>
  );
}
