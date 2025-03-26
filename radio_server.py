from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydub import AudioSegment
from pydub.playback import play
import threading
import random
import os
import asyncio

app = FastAPI()

# Mount static folder for CSS or future use
app.mount("/static", StaticFiles(directory="static"), name="static")

music_folder = "downloaded_songs"
current_song = ""

html_content = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>🎧 Radio Rockie 🎧</title>
    <script>
        let ws = new WebSocket("ws://localhost:8000/ws");
        ws.onmessage = (event) => {
            document.getElementById("current-song").innerText = `🎶 Now Playing: ${event.data}`;
        };
    </script>
    <style>
        body { font-family: sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; text-align: center; padding: 100px; }
        h1 { font-size: 3em; margin-bottom: 0.2em; }
        #current-song { font-size: 1.5em; margin-top: 1em; }
        .card { background: rgba(0, 0, 0, 0.4); padding: 20px; border-radius: 20px; display: inline-block; margin-top: 40px; }
    </style>
</head>
<body>
    <div class=\"card\">
        <h1>🎧 Radio Rockie Live</h1>
        <div id=\"current-song\">Waiting for music...</div>
    </div>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_text(current_song)
        await asyncio.sleep(2)

def play_radio():
    global current_song
    while True:
        all_songs = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]
        if not all_songs:
            print("هیچ آهنگی برای پخش پیدا نشد.")
            break

        random.shuffle(all_songs)
        for song in all_songs:
            current_song = song
            print(f"در حال پخش: {song}")
            audio = AudioSegment.from_mp3(os.path.join(music_folder, song))
            play(audio)

radio_thread = threading.Thread(target=play_radio)
radio_thread.start()