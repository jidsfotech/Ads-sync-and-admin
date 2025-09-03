import vlc
import sys
import json
import asyncio
import aiohttp
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QFrame, QStackedWidget
from PyQt5.QtCore import QTimer, Qt, QSize
from qasync import QEventLoop
import utils

API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/client?client_id=raspi-1"


class BillboardPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billboard Player")
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(QSize(400, 300))

        # Setup local cache directory
        self.cacheDir = Path("media_cache")
        self.cacheDir.mkdir(exist_ok=True)
        print(f"Media cache directory: {self.cacheDir.absolute()}")

        # Use QStackedWidget for smooth transitions
        self.layout = QVBoxLayout(self)
        self.stackedWidget = QStackedWidget(self)
        self.layout.addWidget(self.stackedWidget)

        # Create separate widgets for different media types
        self.imageWidget = QLabel("Loading...", self)
        self.imageWidget.setAlignment(Qt.AlignCenter)
        self.imageWidget.setStyleSheet(
            "background-color: black; color: white;")

        self.videoFrame = QFrame(self)
        self.videoFrame.setStyleSheet("background-color: black;")
        self.onVideoEnd = utils.onVideoEnd

        # Add widgets to stack
        self.stackedWidget.addWidget(self.imageWidget)  # index 0
        self.stackedWidget.addWidget(self.videoFrame)   # index 1

        # VLC setup with proper options
        vlcArgs = [
            "--quiet",
            "--no-xlib",
            "--intf=dummy",
            "--extraintf=logger",
        ]
        self.vlcInstance = vlc.Instance(vlcArgs)
        self.vlcPlayer = self.vlcInstance.media_player_new()

        # VLC event manager for handling video end
        self.vlcEvents = self.vlcPlayer.event_manager()
        self.vlcEvents.event_attach(
            vlc.EventType.MediaPlayerEndReached, self.onVideoEnd)

        self.schedules = []
        self.currentIndex = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.playNext)

        # Video loop management
        self.videoloopTimer = QTimer()
        self.videoloopTimer.timeout.connect(utils.restartVideo)

        self.currentMediaType = None
        self.isPlayingVideo = False
        self.currentVideoPath = None

        # Cache management
        self.cachedMedia = {}  # URL -> local_path mapping

    def playNext(self):
        # Play next media from local cache
        if not self.schedules or self.currentIndex >= len(self.schedules):
            self.imageWidget.setText("No active schedules")
            self.stackedWidget.setCurrentIndex(0)
            return

        schedule = self.schedules[self.currentIndex]
        adData = schedule.get("ad", {})
        mediaUrl = adData.get("file_path", "")
        mediaType = adData.get("file_type", "")

        print(f"Playing media: {mediaUrl} (type: {mediaType})")

        # Get local path for media
        localPath = utils.getLocalMediaPath(self, mediaUrl)

        if not localPath or not os.path.exists(localPath):
            print(f"Local media file not found: {localPath}")
            self.imageWidget.setText("Media file not available")
            self.stackedWidget.setCurrentIndex(0)

        else:
            # Route to appropriate player based on media type
            if mediaType.startswith("image"):
                utils.imageSlider(self, localPath)
            elif mediaType.endswith("gif"):
                utils.gifSlider(localPath)
            elif mediaType.startswith("video"):
                utils.videoplayer(self, localPath)
            else:
                print(f"Unknown media type: {mediaType}")
                self.imageWidget.setText(f"Unsupported media: {mediaType}")
                self.stackedWidget.setCurrentIndex(0)

        # Set timer for duration
        duration = utils.formatDuration(schedule.get("duration", "PT10S"))
        print(f"Media will play for {duration/1000} seconds")
        self.timer.start(duration)

        # Move to next schedule
        self.currentIndex = (self.currentIndex + 1) % len(self.schedules)

    def stop(self):
        # Stop all playback
        self.timer.stop()
        utils.stopVideo(self)
        self.stackedWidget.setCurrentIndex(0)

    async def listenWs(self):
        # Listen for WebSocket updates and refresh cache
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(WS_URL) as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            newScheduleData = json.loads(msg.data)
                            print("New schedule received via WebSocket")

                            # Format new schedules
                            newSchedules = utils.formatSchedules(
                                newScheduleData)

                            if newSchedules != self.schedules:
                                print("Schedules changed, updating cache...")

                                # Update cache with new media
                                success = await utils.cacheAllMedia(self, schedules=newSchedules)

                                if success:
                                    oldCount = len(self.schedules)
                                    self.schedules = newSchedules

                                    # Reset index if needed
                                    if self.currentIndex >= len(self.schedules):
                                        self.currentIndex = 0

                                    print(
                                        f"Schedules updated: {oldCount} -> {len(self.schedules)}")

        except Exception as e:
            print(f"WebSocket error: {e}")

    async def run(self):
        # Initialize player with cached media
        print("Starting Billboard Player...")

        # Fetch initial schedules
        rawSchedules = await utils.fetchSchedules(self)
        if not rawSchedules:
            self.imageWidget.setText("No schedules available")
            return

        # Filter active schedules
        self.schedules = utils.formatSchedules(rawSchedules)

        if not self.schedules:
            self.imageWidget.setText("No active schedules found")
            return

        # Cache all media files
        print("Caching media files...")
        cache_success = await utils.cacheAllMedia(self, schedules=self.schedules)

        if cache_success:
            print(
                f"Starting playback with {len(self.schedules)} cached schedules")
            self.playNext()
        else:
            self.imageWidget.setText("Failed to cache media files")
            return

        # Start WebSocket listener
        asyncio.create_task(self.listenWs())

    def closeEvent(self, event):
        # Clean shutdown
        print("Shutting down player...")
        self.stop()
        try:
            self.vlcPlayer.release()
            self.vlcInstance.release()
        except:
            pass
        event.accept()


def runPlayer():
    """Main entry point"""
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    player = BillboardPlayer()
    player.showNormal()

    try:
        with loop:
            loop.create_task(player.run())
            loop.run_forever()
    except KeyboardInterrupt:
        print("Application interrupted")
    finally:
        app.quit()
