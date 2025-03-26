from flask import Flask, render_template_string, send_from_directory, Response
from flask_socketio import SocketIO
import os
import time
import threading
import librosa
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_123!'
socketio = SocketIO(app, cors_allowed_origins="*")

# تنظیمات پوشه موزیک
MUSIC_DIR = os.path.abspath('downloaded_music')
os.makedirs(MUSIC_DIR, exist_ok=True)

class AudioStreamer:
    def __init__(self):
        self.current_track = None
        self.start_time = 0
        self.paused_at = 0
        self.is_playing = False
        self.duration = 0
        self.lock = threading.Lock()
        self.stream_thread = None

    def load_track(self, filename):
        try:
            filepath = os.path.join(MUSIC_DIR, filename)
            self.duration = librosa.get_duration(path=filepath)
            self.current_track = filename
            self.start_time = time.time()
            self.paused_at = 0
            self.is_playing = True
            logging.info(f"Loaded track: {filename}")
            return True
        except Exception as e:
            logging.error(f"Error loading track: {str(e)}")
            return False

    def get_current_time(self):
        if self.is_playing:
            return time.time() - self.start_time + self.paused_at
        return self.paused_at

    def toggle_play(self):
        with self.lock:
            if self.is_playing:
                self.paused_at = self.get_current_time()
                self.is_playing = False
            else:
                self.start_time = time.time() - self.paused_at
                self.is_playing = True

    def get_state(self):
        return {
            'track': self.current_track,
            'position': self.get_current_time(),
            'duration': self.duration,
            'is_playing': self.is_playing
        }

streamer = AudioStreamer()

def get_playlist():
    try:
        return [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3', '.wav'))]
    except Exception as e:
        logging.error(f"Playlist error: {str(e)}")
        return []

def stream_generator():
    while True:
        if streamer.current_track and streamer.is_playing:
            filepath = os.path.join(MUSIC_DIR, streamer.current_track)
            try:
                with open(filepath, 'rb') as f:
                    while True:
                        data = f.read(1024 * 16)
                        if not data:
                            break
                        yield data
            except Exception as e:
                logging.error(f"Stream error: {str(e)}")
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>رادیو راک - استریم زنده</title>
        <style>
            /* استایل‌های پیشرفته */
            body {
                font-family: 'Tahoma', sans-serif;
                background: #1a1a1a;
                color: #fff;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: #2a2a2a;
                border-radius: 15px;
                padding: 20px;
            }
            #player {
                width: 100%;
                margin: 20px 0;
                background: #333;
                border-radius: 8px;
            }
            .playlist {
                list-style: none;
                padding: 0;
            }
            .playlist li {
                padding: 15px;
                margin: 10px 0;
                background: #3a3a3a;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .playlist li:hover {
                background: #4a4a4a;
                transform: translateX(10px);
            }
            .current {
                background: #3498db !important;
            }
            .controls {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            button {
                padding: 10px 20px;
                background: #3498db;
                border: none;
                border-radius: 5px;
                color: white;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎧 رادیو راک - استریم زنده</h1>
            <div class="controls">
                <button onclick="playPause()">⏯️ پخش/مکث</button>
                <button onclick="nextTrack()">⏭️ بعدی</button>
            </div>
            <div id="nowPlaying">🎵 در حال پخش: <span id="currentTrack">-</span></div>
            <audio id="player" controls></audio>
            <h2>📜 لیست آهنگ‌ها</h2>
            <ul class="playlist" id="playlist"></ul>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js"></script>
        <script>
            const socket = io();
            const player = document.getElementById('player');
            let currentTrack = null;

            // اتصال اولیه
            socket.on('connect', () => {
                socket.emit('get_state');
                socket.emit('get_playlist');
            });

            // دریافت وضعیت فعلی
            socket.on('state_update', (state) => {
                updatePlayer(state);
            });

            // دریافت لیست آهنگ‌ها
            socket.on('playlist_update', (playlist) => {
                updatePlaylist(playlist);
            });

            // به روزرسانی پخش کننده
            function updatePlayer(state) {
                document.getElementById('currentTrack').textContent = state.track || '-';
                
                // تغییر آهنگ اگر لازم باشد
                if(state.track && state.track !== currentTrack) {
                    currentTrack = state.track;
                    player.src = `/stream/${encodeURIComponent(state.track)}`;
                }

                // همگام‌سازی وضعیت پخش
                if(state.is_playing && player.paused) {
                    player.play().catch(e => showError('برای پخش نیاز به کلیک کاربر است'));
                } else if(!state.is_playing && !player.paused) {
                    player.pause();
                }

                // همگام‌سازی زمان
                if(Math.abs(player.currentTime - state.position) > 2) {
                    player.currentTime = state.position;
                }
            }

            // به روزرسانی لیست آهنگ‌ها
            function updatePlaylist(playlist) {
                const list = document.getElementById('playlist');
                list.innerHTML = playlist.map(song => `
                    <li class="${song === currentTrack ? 'current' : ''}" 
                        onclick="playTrack('${song}')">
                        ${song}
                    </li>
                `).join('');
            }

            // کنترل‌های کاربر
            function playTrack(track) {
                socket.emit('play_track', track);
            }

            function playPause() {
                socket.emit('toggle_play');
            }

            function nextTrack() {
                socket.emit('next_track');
            }

            // نمایش خطاها
            function showError(message) {
                alert('خطا: ' + message);
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/stream/<filename>')
def stream_file(filename):
    return Response(stream_generator(), mimetype='audio/mpeg')

@app.route('/music/<filename>')
def serve_file(filename):
    return send_from_directory(MUSIC_DIR, filename)

# Socket.IO Handlers
@socketio.on('get_state')
def handle_get_state():
    socketio.emit('state_update', streamer.get_state())

@socketio.on('get_playlist')
def handle_get_playlist():
    socketio.emit('playlist_update', get_playlist())

@socketio.on('play_track')
def handle_play_track(track):
    if track in get_playlist():
        streamer.load_track(track)
        broadcast_updates()

@socketio.on('toggle_play')
def handle_toggle_play():
    streamer.toggle_play()
    broadcast_updates()

@socketio.on('next_track')
def handle_next_track():
    playlist = get_playlist()
    if playlist:
        current_index = playlist.index(streamer.current_track) if streamer.current_track in playlist else -1
        new_index = (current_index + 1) % len(playlist)
        streamer.load_track(playlist[new_index])
        broadcast_updates()

def broadcast_updates():
    socketio.emit('state_update', streamer.get_state())
    socketio.emit('playlist_update', get_playlist())

def monitor_player():
    while True:
        if streamer.is_playing and streamer.get_current_time() >= streamer.duration:
            handle_next_track()
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=monitor_player, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)