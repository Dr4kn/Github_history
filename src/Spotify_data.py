# only used for the gDrive upload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import os

# necessary for the authentication and getting the json from spotify
# pip install spotipy
import spotipy
import spotipy.util as util
import spotipy.oauth2 as oauth2
import sqlite3
import sys
import time

# creates an sql table if one isn't their yet
def create_table():
    try:
        sql_cursor.execute("CREATE TABLE spotify_data (played_at TEXT, artists TEXT, album TEXT, "
                            "track TEXT, artists_id TEXT, album_id TEXT, track_id TEXT, duration_ms INTEGER)")
        print("This program saves Your last 50 played Spotify songs in a sqlite database\n"
              "If you don't already have a spotify developer account you can create your variables here:\n"
              "https://developer.spotify.com/dashboard/applications\n"
              "You can create environmental variables with these names:\n"
              "SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SPOTIPY_USERNAME\n"
              "You can type your variables in the console\n"
              "or put them in the code to have them permanently in it\n")
    except sqlite3.OperationalError:
        print()

def environment_variables():
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')
    username = os.environ.get('SPOTIPY_USERNAME')
    spotify_parser(client_id, client_secret, redirect_uri, username)


# can be put in if you want to choose every time otherwise insert the variant you want to use in main
def choose_variables():
    number = input("For environmental variables type 1.\n"
                    "For console Type 2\n"
                    "For hard coded Type 3: ")
    select_variable_import(number)

def select_variable_import(number):
    if number == "1":
        environment_variables()
    if number == "2":
        console_variables()
    if number == "3":
        hard_coded_variables()
    else:
        print("\n" "Only 1, 2 and 3 are recognised")
        choose_variables()

def console_variables():
    print("Type in your created variables")
    client_id = input("client_id: ")
    client_secret = input("client_secret: ")
    redirect_uri = input("redirect_uri: ")
    username = input("username: ")
    spotify_parser(client_id, client_secret, redirect_uri, username)

def hard_coded_variables():
    client_id = "" # spotify client ID
    client_secret = "" # spotify secret ID
    redirect_uri = "https://google.com/" # could be something else
    username = "" # spotify username
    spotify_parser(client_id, client_secret, redirect_uri, username)

def spotify_parser(client_id, client_secret, redirect_uri, username):
    scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state user-read-recently-played"
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    spotify_object = spotipy.Spotify(auth=token)
    spotify_object.trace = False
    save_multiple_songs(spotify_object.current_user_recently_played(limit=50))

# goes into sql database and adds at max the last 50 songs at the bottom of the list chronologically
# duplicates are ignored
def save_multiple_songs(current_user_recently_played):
    current_user_recently_played = spotipy()

    # no idea how efficient it is but it doesn't matter much
    # You run the script at at maximum every 15 minutes 
    # If it would take one minute (which it doesn't) it really doesn't matter
    sql_cursor.execute("SELECT * FROM spotify_data ORDER BY played_at DESC LIMIT 1")
    last_played = sql_cursor.fetchone()
    i = len(current_user_recently_played["items"]) - 1

    # appends everything to the database
    # if the current added matches the last played the database is rolled back
    # this ensures that only the new plays are saved without looping two times through the list
    while i >= 0:
        track = current_user_recently_played["items"][i]
        time = track["played_at"]
        artist = track["track"]["album"]["artists"][0]["name"]
        album = track["track"]["album"]["name"]
        song = track["track"]["name"]
        artist_id = track["track"]["album"]["artists"][0]["id"]
        album_id = track["track"]["album"]["id"]
        song_id = track["track"]["id"]
        duration_ms = track["track"]["duration_ms"]
        spotipy_data = (time, artist, album, song, artist_id, album_id, song_id, duration_ms)
        sql_cursor.execute("INSERT INTO spotify_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)", spotipy_data)
        i -= 1

        if spotipy_data == last_played:
            sql.rollback()

    sql.commit()
    
    # comment out if you don't want to upload it
    google_drive_upload()

# creates gDrive credentials if they don't exist and uploads it automatically to it after that
def google_drive_upload():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("google_drive_credentials.txt")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile("google_drive_credentials.txt")
    elif gauth.access_token_expired:
        gauth.Refresh()
        gauth.SaveCredentialsFile("google_drive_credentials.txt")
    else:
        gauth.Authorize()

    drive = GoogleDrive(gauth)

    google_drive_file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for files in google_drive_file_list:
        if files['title'] == "spotify_data.db":
            files.Trash()

    file1 = drive.CreateFile({'title': 'spotify_data.db'})
    file1.SetContentFile("spotify_data.db")
    file1.Upload()
    print("Uploaded")

if __name__ == "__main__":
    # path to where you data file is
    # sql = sqlite3.connect("/home/pi/Documents/Spotify_info/spotify_data.db")
    sql = sqlite3.connect("spotify_data.db")
    sql_cursor = sql.cursor()
    create_table()

    # choose one of the four option below

    # choose_variables()
    # environment_variables
    # console_variables
    hard_coded_variables()
    
    print("Done")
