# Dash App - Plotly

## For the data:
1. create functions to get data for specific important columns
2. Create functions for dash interactions - Brushing etc -> Else the app will be way too big
3. Functionalise graphs
4. Separate each part of the app in separate files - plots.py, interactions.py, filters.py, common_functions.py, etc

## Plan for the app

1. 2 part app - 1. Movie information, 2. Recommendation based on users (We select an user) + Upload data for future section

2. Select top 10 genres and use them only. Too many will look weird.

## Movie Information

1. 4 graphs/boxes - >
   1.1. Info on genres - Avg rating per genre and no of movies in the genre -> Radar plot
   1.2. Info on the director of the movie -> Might change still - Top X actors based on rating and based on no of movies also.
   1.3. Info on lead actor - Top X actors based on rating and based on no of movies also.
   1.4. Top movies based on ratings

## Interactions

1. Each graph is connected.
2. Clicking on anything on the graphs, it will filter every other graph based on the click. E.g. if we click on a genre on the genre graph, the other 4 graphs change to filter to that selected genres.
3. Global filtering - Calculate the same for above but onthe global filtered subset.
   3.1. On the top - Release year - Time series on year. > 2001 etc.
   3.2. Could be done on other things. > 4 rating. > 3 rating.
   3.3.

## Recommender

1.  Use 2 users from our ratings table ezpz- Rose and Aniket. As and when we watch a new movie, we rate it, and it gets added to the df. And the recommendations change.
2.  Cluster the movies and visualise them
3.  Highlight the movies we have rated
4.  These clusters I like, these I do not, etc.
5.  Pick movies the user rated and highlight them in the cluster
6.  Pick users with 100-300 ratings or all users with similar ratings, else the heatmap becomes black

## Page graph setup

1. 1 big graph which will be the whole cluster -> Shows the cluster of movies, TSNE, PCA, ETC. Highlight the user's movies with different colors based on ratings.
2. Graph 2 will be top X recommended movies for the user. - Give movie specific info - Allactors, runtime, tags if not none, main_language if not none, overview - Nice to know if they want to know the movie.
3. Graph 3 - Why the movies were recommended. Shap values, etc

## Interactions

1. Hover to get info -> Movie title, release year + Zoom
2. Select cluster -> Could be from the legend. All g if not. Hover over the dot and drag or select a triangle or a square and zoom in specifically on that.
   2.1. If selected, recommended movies will change in the recommended movies.
   2.2. Or filters -> Director/etc
   2.3. List to movies -> Can potentially scroll down - IGNORE FOR NOW. TOO SLOW.
3. Hover and see specific values/info.
4. General global filters:
   4.1 Genre -> Dropdown
   4.2. Release year -> Before, after, between -> Slider
