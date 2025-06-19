# Movie Recommendations
2AMV10 Visual Analytics

Created by Aniket Mishra (2079259) and Rose van Mierlo (1560158)

An extensive tool used to recommend movies! 
This application was built using the Python Dash library


### How to run

In order to use the application, navigate to the `dash_app` directory. Within this directory, simply run `app.py` and click on the link that appears in the terminal. This will open the dashboard in the webbrowser. 

### Data

All the data should be present within the `data` directory. The preprocessed files are `1_all_users_stats_with_clusters.parquet`, `1_movies_data_for_app.parquet` and `1_ratings_data_filtered.parquet`. All three files can be obtained by running the python notebooks within the `process_raw_data` directory. 

### Libraries/dependencies

The following list of libraries were used. 
* Dash (version 3.0.4) - Making the dashboard.
* Plotly (version 6.1.2) - Creating plot and visualizations
* sklearn (version 1.3.2)
* xgboost (version 3.0.2)
* Pandas (version 2.3.0)
* Numpy (version 1.26.4)
* JSON (version 2.0.9)

