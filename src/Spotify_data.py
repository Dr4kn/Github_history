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

    except sqlite3.OperationalError:
        print("Sqlite Error")


def environment_variables():
    spotipy_client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    spotipy_client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    spotipy_redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')  # https://google.com/ can be used
    spotipy_username = os.environ.get('SPOTIPY_USERNAME')
    spotify_parser(spotipy_client_id, spotipy_client_secret, spotipy_redirect_uri, spotipy_username)


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
    # google_drive_upload()


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
    # gets directory of this python file
    dir_path = os.path.dirname(os.path.realpath(__file__))

    sql = sqlite3.connect(dir_path + "/spotify_data.db")
    sql_cursor = sql.cursor()
    create_table()

    environment_variables()

    print("Done")
