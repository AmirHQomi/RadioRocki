import random
from pydub import AudioSegment
from pydub.playback import play
import json
import os

AudioSegment.ffmpeg = "C:\\ffmpeg\\bin\\ffmpeg.exe"
AudioSegment.converter = "C:\\ffmpeg\\bin\\ffmpeg.exe"

# مسیر پوشه آهنگ‌ها
downloaded_songs_folder = 'downloaded_music'
os.makedirs(downloaded_songs_folder, exist_ok=True)

# --------- کراسفید ---------
def apply_crossfade(track1, track2, fade_duration=3000):
    audio1 = AudioSegment.from_mp3(track1).fade_out(fade_duration)
    audio2 = AudioSegment.from_mp3(track2).fade_in(fade_duration)
    crossfade_path = 'crossfaded.mp3'
    (audio1 + audio2).export(crossfade_path, format='mp3')
    return crossfade_path

# --------- پخش موسیقی ---------
def play_radio():
    try:
        # بررسی فایل‌ها در پوشه دانلود شده
        music_files = [f for f in os.listdir(downloaded_songs_folder) if f.endswith('.mp3')]
        if not music_files:
            print("❌ No music files found in the 'downloaded_songs' folder.")
            return

        # ذخیره گزارش
        report = []

        last_track = None
        while True:  # ایجاد حلقه بی‌پایان برای پخش مداوم آهنگ‌ها
            random.shuffle(music_files)

            for file_name in music_files:
                track_path = os.path.join(downloaded_songs_folder, file_name)
                
                # بارگذاری آهنگ
                audio = AudioSegment.from_mp3(track_path)
                duration_in_seconds = len(audio) / 1000  # مدت زمان آهنگ به ثانیه

                # پخش آهنگ
                if last_track:
                    crossfaded = apply_crossfade(last_track, track_path)
                    print(f"Crossfading to {file_name}")
                    play(AudioSegment.from_mp3(crossfaded))
                    # ثبت اطلاعات کراسفید در گزارش
                    report.append({
                        'action': 'crossfade',
                        'from': last_track,
                        'to': track_path
                    })
                else:
                    print(f"📡 Playing: {file_name} | Duration: {duration_in_seconds:.2f}s")
                    play(audio)

                last_track = track_path

                # به‌روزرسانی زمان باقی‌مانده و نمایش در ترمینال
                while duration_in_seconds > 0:
                    print(f"\r🎶 Time Remaining: {duration_in_seconds:.2f}s | Now playing: {file_name}", end="")
                    duration_in_seconds -= 1
                print(f"\n🎶 {file_name} finished playing.\n")
                
                # ثبت اطلاعات پخش در گزارش
                report.append({
                    'action': 'play',
                    'file_name': file_name,
                    'duration': duration_in_seconds
                })

        # ذخیره گزارش دانلودها و پخش‌ها در فایل JSON
        with open('radio_play_report.json', 'w') as f:
            json.dump(report, f, indent=4)

    except Exception as e:
        print(f"Error in radio playback: {e}")

# اجرای پخش رادیو
if __name__ == "__main__":
    play_radio()
