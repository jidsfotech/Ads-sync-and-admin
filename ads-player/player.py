import vlc
import sys
import json
import asyncio
import aiohttp
import platform
from datetime import datetime, timezone
import isodate
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QFrame
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QTimer, Qt, QByteArray
import requests
from qasync import QEventLoop


API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/client?client_id=raspi-1"


class BillboardPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billboard Player")
        self.setGeometry(0, 0, 800, 600)

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Loading...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # VLC video frame
        self.video_frame = QFrame(self)
        self.layout.addWidget(self.video_frame)
        self.video_frame.hide()  # hidden until video plays

        # VLC setup
        self.vlc_instance = vlc.Instance("--quiet")
        self.vlc_player = self.vlc_instance.media_player_new()

        self.schedules = []
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.playNext)

        self.current_media_type = None
        self.is_playing_video = False

    async def fetchSchedules(self):
        print("Fetching schedules...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/api/schedules?skip=0&limit=20") as resp:
                    if resp.status != 200:
                        print(f"Error fetching schedules: {resp.status}")
                        self.label.setText("Error fetching schedules")
                        return
                    data = await resp.json()
                    self.schedules = self.formatSchedules(schedules=data)
        except Exception as e:
            print("Error fetching schedules:", e)

    def formatSchedules(self, schedules):
        formatted = []
        now = datetime.now(timezone.utc)
        for s in schedules:
            startTime = datetime.fromisoformat(s["start_time"]).replace(tzinfo=timezone.utc)
            endTime = datetime.fromisoformat(s["end_time"]).replace(tzinfo=timezone.utc)
            if startTime <= now <= endTime:
                formatted.append(s)
        return formatted

    def formatDuration(self, rawDuration):
        duration_seconds = 10
        if isinstance(rawDuration, (int, float)):
            duration_seconds = float(rawDuration)
        elif isinstance(rawDuration, str):
            try:
                duration_seconds = isodate.parse_duration(rawDuration).total_seconds()
            except Exception:
                try:
                    duration_seconds = float(rawDuration)
                except ValueError:
                    duration_seconds = 10
        return int(duration_seconds * 1000)

    def loadPixmapFromUrl(self, url: str) -> QPixmap:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            return pixmap
        except Exception as e:
            print(f"Failed to load image from {url}: {e}")
        return QPixmap()

    def imageSlider(self, media_url: str):
        self.stop()  # stop video if running
        self.video_frame.hide()
        self.label.show()
        self.is_playing_video = False

        pixmap = self.loadPixmapFromUrl(media_url)
        if pixmap.isNull():
            print("Image could not be loaded.")
        else:
            self.label.setPixmap(pixmap.scaled(
                self.label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    def gifSlider(self, media_url: str):
        self.stop()  # stop video if running
        self.video_frame.hide()
        self.label.show()
        self.is_playing_video = False
        try:
            response = requests.get(media_url, stream=True)
            response.raise_for_status()
            gif_data = QByteArray(response.content)
            movie = QMovie(gif_data, b"gif")
            if not movie.isValid():
                print("Invalid GIF data")
                return
            self.label.setMovie(movie)
            movie.start()
        except Exception as e:
            print(f"Error loading GIF: {e}")

    def videoplayer(self, media_url: str):
        self.stop()
        self.label.hide()
        self.video_frame.show()
        self.is_playing_video = True

        media = self.vlc_instance.media_new(media_url)
        media.add_option("input-repeat=-1")
        self.vlc_player.set_media(media)

        # Embed VLC video into Qt widget
        if platform.system() == "Windows":
            self.vlc_player.set_hwnd(int(self.video_frame.winId()))
        elif platform.system() == "Linux":
            self.vlc_player.set_xwindow(int(self.video_frame.winId()))
        elif platform.system() == "Darwin":  # macOS
            self.vlc_player.set_nsobject(int(self.video_frame.winId()))

        print(f"Starting video with VLC: {media_url}")
        self.vlc_player.play()

    def stop(self):
        self.timer.stop()
        if self.is_playing_video:
            self.vlc_player.stop()
            self.video_frame.hide()
            self.label.show()
            self.is_playing_video = False

    def playNext(self):

        if not self.schedules or self.current_index >= len(self.schedules):
            self.label.setText("No active schedules")
            return

        schedule = self.schedules[self.current_index]
        ad_data = schedule.get("ad", {})
        media_url = ad_data.get("file_path", "test.jpg")
        media_type = schedule.get("ad", {}).get("file_type", "jpg")

        print(f"Playing media: {media_url} (type: {media_type})")

        if media_type.startswith("image"):
            self.imageSlider(media_url)
        elif media_type.endswith("gif"):
            self.gifSlider(media_url)
        elif media_type.startswith("video"):
            self.videoplayer(media_url)

        duration = self.formatDuration(schedule.get("duration", "PT10S"))
        self.timer.start(duration)
        self.current_index = (self.current_index + 1) % len(self.schedules)

    async def listenWs(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        newSchedule = json.loads(msg.data)
                        print("New schedule received:", newSchedule)
                        self.schedules = self.formatSchedules(schedules=newSchedule)

    async def run(self):
        await self.fetchSchedules()
        if self.schedules:
            self.playNext()
        asyncio.create_task(self.listenWs())


def runPlayer():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    player = BillboardPlayer()
    player.showNormal()

    with loop:
        loop.create_task(player.run())
        loop.run_forever()