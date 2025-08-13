# Customized Game Recommender System

A machine learning-powered Steam game recommendation system that provides personalized game suggestions using multiple recommendation algorithms including content-based filtering, collaborative filtering, and popularity-based recommendations.

## 🎮 Features

- **Multiple Recommendation Algorithms**:
  - **Popularity-Based**: Recommends games based on overall popularity and ownership statistics
  - **Content-Based**: Uses TF-IDF vectorization on game descriptions to find similar games
  - **Item-Based Collaborative Filtering**: Recommends games based on user purchase patterns
  - **ALS (Alternating Least Squares)**: Matrix factorization using Apache Spark for collaborative filtering

- **Web Interface**: Flask-based web application with responsive Bootstrap UI
- **Real Steam Data**: Uses actual Steam user data and game information
- **Dynamic Recommendations**: Personalized suggestions based on user's most played game

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Machine Learning**: scikit-learn, Apache Spark (PySpark)
- **Data Processing**: pandas, numpy
- **Database**: MySQL
- **Web Scraping**: BeautifulSoup, requests
- **Frontend**: HTML, CSS, Bootstrap
- **Data Sources**: Steam API, SteamSpy

## 📋 Prerequisites

- Python 3.x
- MySQL Server
- Apache Spark (for ALS recommendations)
- Required Python packages (see Installation)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd customized_game_recommender
   ```

2. **Install required packages**
   ```bash
   pip install flask sqlalchemy pymysql pandas numpy scikit-learn beautifulsoup4 requests pyspark
   ```

3. **Set up MySQL Database**
   - Create a database named `GameRecommend`
   - Update database credentials in `Model_jm.py` and `run.py`
   ```python
   engine = create_engine('mysql+pymysql://username:password@127.0.0.1/GameRecommend?charset=utf8mb4')
   ```

4. **Prepare Data**
   - Ensure you have the required data files in the `data/` directory:
     - `steam_user_id.txt` - List of Steam user IDs
     - `user_gamedata_jm.txt` - User game ownership and playtime data
     - `game_details_jm.txt` - Game details from Steam API
     - `steamspy_gameinfo.json` - Game statistics from SteamSpy

## 🔧 Usage

### Building the Recommendation Models

1. **Run the model building script**:
   ```bash
   python Model_jm.py
   ```
   This will:
   - Process game details and create the `tbl_app_info_jm` table
   - Identify each user's favorite (most played) game
   - Build all four recommendation models
   - Store results in MySQL database

### Running the Web Application

1. **Start the Flask server**:
   ```bash
   python run.py
   ```

2. **Access the application**:
   - Open your browser and navigate to `http://localhost:5000`
   - The system will randomly select a user and display their recommendations

## 📊 How It Works

### Data Processing
- **Game Information**: Extracts game details including name, price, description, platform support, and metadata
- **User Data**: Processes user game libraries and playtime information
- **Favorite Game Detection**: Identifies each user's most played game as their preference baseline

### Recommendation Algorithms

1. **Popularity-Based**: 
   - Uses SteamSpy ownership data to rank games by popularity
   - Provides fallback recommendations when user-specific data is unavailable

2. **Content-Based**:
   - Applies TF-IDF vectorization to game descriptions
   - Uses cosine similarity to find games with similar content
   - Based on the user's favorite game

3. **Item-Based Collaborative Filtering**:
   - Creates user-item purchase matrix
   - Finds games purchased by users with similar preferences
   - Uses cosine similarity between game purchase patterns

4. **ALS Matrix Factorization**:
   - Employs Apache Spark's ALS algorithm
   - Learns latent factors for users and games
   - Provides personalized recommendations based on implicit feedback

### Web Interface
- Displays user's favorite game with image and details
- Shows recommendations from each algorithm
- Provides direct links to Steam store pages
- Responsive design works on desktop and mobile

## 📁 Project Structure

```
customized_game_recommender/
├── run.py                          # Flask web application
├── Model_jm.py                     # ML model building and training
├── Web Scrapping in Python.ipynb   # Data collection notebook
├── data/
│   ├── steam_user_id.txt          # Steam user IDs
│   └── user_gamedata_jm.txt       # User game data
└── templates/
    └── recommendation.html         # Web interface template
```

## 🎯 Key Features

- **Hybrid Approach**: Combines multiple recommendation techniques for better coverage
- **Real-time Processing**: Generates recommendations on-the-fly for any user
- **Scalable Architecture**: Uses Spark for handling large datasets
- **User-Friendly Interface**: Clean, responsive web design
- **Steam Integration**: Direct links to purchase games on Steam

## 🔍 Database Schema

The system creates several MySQL tables:
- `tbl_app_info_jm`: Game information and metadata
- `tbl_user_favorite_app_jm`: User's most played games
- `tbl_results_popularity_based_jm`: Popularity-based recommendations
- `tbl_results_content_based_jm`: Content-based recommendations
- `tbl_results_item_based_jm`: Item-based collaborative filtering results
- `tbl_results_als_based_jm`: ALS-based recommendations

## 🚨 Notes

- The system requires substantial computational resources for model training
- ALS model training requires Apache Spark setup
- Game data should be regularly updated for current recommendations
- MySQL database must be properly configured and accessible

## 📝 License

This project is for educational and research purposes. Steam data usage should comply with Steam's terms of service.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.