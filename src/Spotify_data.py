# only used for the gDrive upload
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sqlite3
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


# creates an sql table if one isn't their yet
def create_table():
    try:
        sql_cursor.execute("CREATE TABLE spotify_data (played_at TEXT, artists TEXT, album TEXT, "
                           "track TEXT, artists_id TEXT, album_id TEXT, track_id TEXT, duration_ms INTEGER)")
        print("created spotify_data.db")

    except sqlite3.OperationalError:
        print("Database already exists")


# gets your last 50 songs you played
def spotify_parser():
    # scopes can be looked up here:
    # https://developer.spotify.com/documentation/general/guides/scopes/
    scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state user-read-recently-played"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    save_multiple_songs(sp.current_user_recently_played(limit=50))


# goes into sql database and adds at max the last 50 songs at the bottom of the list chronologically
# duplicates are ignored
def save_multiple_songs(current_user_recently_played):
    sql_cursor.execute("SELECT * FROM spotify_data ORDER BY played_at DESC LIMIT 1")
    last_played = sql_cursor.fetchone()
    i = len(current_user_recently_played["items"]) - 1

    # appends everything to the database
    # if the current added matches the last played the database is rolled back
    # this ensures that only the new plays are saved without looping two times through the list
    while i >= 0:
        track = current_user_recently_played["items"][i]
        artist_id = track["track"]["album"]["artists"][0]["id"]
        album_id = track["track"]["album"]["id"]
        track_id = track["track"]["id"]
        duration_ms = track["track"]["duration_ms"]
        played_at = track["played_at"]
        artist = track["track"]["album"]["artists"][0]["name"]
        album = track["track"]["album"]["name"]
        track = track["track"]["name"]

        spotipy_data = (played_at, artist, album, track, artist_id, album_id, track_id, duration_ms)
        sql_cursor.execute("INSERT INTO spotify_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)", spotipy_data)
        i -= 1

        # either you go through the list twice and check if the duplicate exists
        # or you through it once and rollback if you find it
        if spotipy_data == last_played:
            sql.rollback()

    sql.commit()


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

    # gets directory of this exact python file
    dir_path = os.path.dirname(os.path.realpath(__file__))

    sql = sqlite3.connect(dir_path + "/spotify_data.db")
    sql_cursor = sql.cursor()

    create_table()
    spotify_parser()
    # comment out if you don't want to upload it
    # google_drive_upload()

    print("Done")
