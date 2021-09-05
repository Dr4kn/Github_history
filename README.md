# Spotify-History
Uses the spotipy library to put your last played songs in a SQLLight database. 
Ideally run with crontab every 22 minutes. 

It uses spotipy to use the spotify api and pydrive to optionaly upload to gcloud.

<h2>Setup</h2>
You have to create a developer account at:
https://developer.spotify.com/
and go to your dashboard afterwords and create an application the name you choose doesn't matter. 
Go to Edit Settings and put http://127.0.0.1:9090 in the Redirect URI.

Create 4 enviromental variables:

**SPOTIPY_CLIENT_ID** for your spotify client id 

**SPOTIPY_CLIENT_SECRET** for your spotify secret

**SPOTIPY_REDIRECT_URI** use **http://127.0.0.1:9090**

**SPOTIPY_USERNAME** your spotify username




