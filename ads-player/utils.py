import aiohttp
import platform
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import isodate
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt
import requests


API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/client?client_id=raspi-1"


async def downloadMedia(playerInstance, url: str, progressCallback=None) -> str:
    # Download media file to local cache
    cacheFilename = getCacheFilename(url)
    cachePath = playerInstance.cacheDir / cacheFilename

    # Return cached file if it exists and is valid
    if cachePath.exists() and cachePath.stat().st_size > 0:
        print(f"Using cached file: {cacheFilename}")
        return str(cachePath)

    print(f"Downloading: {url} -> {cacheFilename}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(
                        f"Failed to download {url}: HTTP {response.status}")
                    return None

                totalSize = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(cachePath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progressCallback and totalSize > 0:
                            progress = (downloaded / totalSize) * 100
                            progressCallback(progress, cacheFilename)

        print(
            f"Downloaded successfully: {cacheFilename} ({cachePath.stat().st_size} bytes)")
        return str(cachePath)

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        # Clean up partial download
        if cache_path.exists():
            cache_path.unlink()
        return None


def updateDownloadProgress(playerInstance, progress: float, filename: str):
    # Update UI with download progress
    playerInstance.imageWidget.setText(
        f"Downloading {filename}\n{progress:.1f}%")


def getExtensionFromUrl(url: str) -> str:
    # Get file extension based on URL or content type
    try:
        response = requests.head(url, timeout=10)
        contentType = response.headers.get('content-type', '').lower()

        if 'image/jpeg' in contentType or 'image/jpg' in contentType:
            return '.jpg'
        elif 'image/png' in contentType:
            return '.png'
        elif 'image/gif' in contentType:
            return '.gif'
        elif 'video/mp4' in contentType:
            return '.mp4'
        elif 'video/avi' in contentType:
            return '.avi'
        elif 'video/mov' in contentType:
            return '.mov'
        else:
            return '.tmp'
    except:
        return '.tmp'


def getCacheFilename(url: str) -> str:
    # Generate cache filename from URL
    # Create hash of URL for unique filename
    urlHash = hashlib.md5(url.encode()).hexdigest()

    # Try to get file extension from URL
    try:
        extension = Path(url).suffix
        if not extension or len(extension) > 5:
            # Fallback to content-type based extension
            extension = getExtensionFromUrl(url)
    except:
        extension = ""

    return f"{urlHash}{extension}"


async def cacheAllMedia(playerInstance, schedules):
    # Pre-download all media files for active schedules
    print("Starting media caching...")
    playerInstance.imageWidget.setText("Caching media files...")

    downloadTasks = []
    mediaUrls = set()

    # Collect all unique media URLs
    for schedule in schedules:
        adData = schedule.get("ad", {})
        mediaUrl = adData.get("file_path")
        if mediaUrl and mediaUrl not in mediaUrls:
            mediaUrls.add(mediaUrl)

    print(f"Found {len(mediaUrls)} unique media files to cache")

    # Download all media files
    cachedCount = 0
    for i, url in enumerate(mediaUrls, 1):
        try:
            playerInstance.imageWidget.setText(
                f"Caching media {i}/{len(mediaUrls)}")

            localPath = await downloadMedia(
                playerInstance,
                url,
                lambda p, f: updateDownloadProgress(playerInstance, p, f)
            )

            if localPath:
                playerInstance.cachedMedia[url] = localPath
                cachedCount += 1
                print(f"Cached: {url} -> {localPath}")
            else:
                print(f"Failed to cache: {url}")

        except Exception as e:
            print(f"Error caching {url}: {e}")

    print(
        f"Media caching complete: {cachedCount}/{len(mediaUrls)} files cached")
    playerInstance.imageWidget.setText(
        f"Cached {cachedCount}/{len(mediaUrls)} media files")

    return cachedCount > 0


def getLocalMediaPath(playerInstance, url: str) -> str:
    # Get local path for media URL
    # Fallback to URL if not cached
    return playerInstance.cachedMedia.get(url, url)


def cleanupOldCache(playerInstance):
    # Remove cached files that are no longer needed
    try:
        currentFiles = set(playerInstance.cachedMedia.values())

        for cacheFile in playerInstance.cacheDir.glob("*"):
            if str(cacheFile) not in currentFiles:
                print(f"Removing old cache file: {cacheFile.name}")
                cacheFile.unlink()

    except Exception as e:
        print(f"Error cleaning cache: {e}")


async def fetchSchedules(playerInstance):
    print("Fetching schedules...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/api/schedules?skip=0&limit=50") as resp:
                if resp.status != 200:
                    print(f"Error fetching schedules: {resp.status}")
                    playerInstance.imageWidget.setText(
                        f"Error fetching schedules: {resp.status}")
                    return []
                data = await resp.json()
                return data
    except Exception as e:
        print(f"Error fetching schedules: {e}")
        playerInstance.imageWidget.setText(f"Network error: {str(e)}")
        return []


def formatSchedules(schedules):
    # Filter schedules by current time and cache media
    formatted = []
    now = datetime.now(timezone.utc)

    for s in schedules:
        try:
            startTime = datetime.fromisoformat(
                s["start_time"]).replace(tzinfo=timezone.utc)
            endTime = datetime.fromisoformat(
                s["end_time"]).replace(tzinfo=timezone.utc)

            if startTime <= now <= endTime:
                formatted.append(s)
        except Exception as e:
            print(f"Error parsing schedule time: {e}")
            continue

    print(f"Active schedules: {len(formatted)}")
    return formatted


def formatDuration(rawDuration):
    durationSeconds = 10
    if isinstance(rawDuration, (int, float)):
        durationSeconds = float(rawDuration)
    elif isinstance(rawDuration, str):
        try:
            durationSeconds = isodate.parse_duration(
                rawDuration).total_seconds()
        except Exception:
            try:
                durationSeconds = float(rawDuration)
            except ValueError:
                durationSeconds = 10
    return int(durationSeconds * 1000)


def imageSlider(playerInstance, localPath: str):
    # Display image from local cache
    print(f"Displaying image: {localPath}")

    if playerInstance.isPlayingVideo:
        stopVideo(playerInstance)

    try:
        pixmap = QPixmap(localPath)
        if pixmap.isNull():
            playerInstance.imageWidget.setText("Failed to load image")
            print("Image could not be loaded.")
        else:
            scaledPixmap = pixmap.scaled(
                playerInstance.imageWidget.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            playerInstance.imageWidget.setPixmap(scaledPixmap)
    except Exception as e:
        print(f"Error displaying image: {e}")
        playerInstance.imageWidget.setText(f"Image error: {str(e)}")

    playerInstance.stackedWidget.setCurrentIndex(0)
    playerInstance.currentMediaType = "image"


def gifSlider(playerInstance, localPath: str):
    # Display GIF from local cache
    print(f"Displaying GIF: {localPath}")

    if playerInstance.isPlayingVideo:
        stopVideo(playerInstance)

    try:
        movie = QMovie(localPath)
        if not movie.isValid():
            playerInstance.imageWidget.setText("Invalid GIF")
            print("Invalid GIF data")
            return

        playerInstance.imageWidget.setMovie(movie)
        movie.start()
    except Exception as e:
        print(f"Error loading GIF: {e}")
        playerInstance.imageWidget.setText(f"GIF error: {str(e)}")


def videoplayer(playerInstance, localPath: str):
    # Play video from local cache
    print(f"Playing video: {localPath}")

    if playerInstance.isPlayingVideo:
        stopVideo(playerInstance)

    # Check if local file exists
    if not os.path.exists(localPath):
        print(f"Local video file not found: {localPath}")
        playerInstance.imageWidget.setText("Video file not found")
        playerInstance.stackedWidget.setCurrentIndex(0)
        return

    playerInstance.stackedWidget.setCurrentIndex(1)
    playerInstance.isPlayingVideo = True
    playerInstance.currentVideoPath = localPath
    playerInstance.currentMediaType = "video"

    try:
        # Create media from local file
        media = playerInstance.vlcInstance.media_new(localPath)

        # Set comprehensive loop options for local files
        media.add_option(":input-repeat=65535")  # Very high repeat count
        media.add_option(":loop")
        # 1 second cache for smooth playback
        media.add_option(":file-caching=1000")

        playerInstance.vlcPlayer.set_media(media)

        # Embed VLC player
        embedVLCPlayer(playerInstance)

        # Start playback
        result = playerInstance.vlcPlayer.play()

        if result == -1:
            print("Failed to start VLC playback")
            playerInstance.imageWidget.setText("Video playback failed")
            playerInstance.stackedWidget.setCurrentIndex(0)
            playerInstance.isPlayingVideo = False
        else:
            print("VLC playback started successfully")

    except Exception as e:
        print(f"Error in video playback: {e}")
        playerInstance.imageWidget.setText(f"Video error: {str(e)}")
        playerInstance.stackedWidget.setCurrentIndex(0)
        playerInstance.isPlayingVideo = False


def embedVLCPlayer(playerInstance):
    # Embed VLC player in the Qt widget based on platform
    try:
        if platform.system() == "Windows":
            playerInstance.vlcPlayer.set_hwnd(
                int(playerInstance.videoFrame.winId()))
        elif platform.system() == "Linux":
            playerInstance.vlcPlayer.set_xwindow(
                int(playerInstance.videoFrame.winId()))
        elif platform.system() == "Darwin":  # macOS
            playerInstance.vlcPlayer.set_nsobject(
                int(playerInstance.videoFrame.winId()))
    except Exception as e:
        print(f"Error embedding VLC player: {e}")


def stopVideo(playerInstance):
    # Stop video playback cleanly
    if playerInstance.isPlayingVideo:
        print("Stopping video playback...")
        playerInstance.videoloopTimer.stop()
        try:
            playerInstance.vlcPlayer.stop()
        except Exception as e:
            print(f"Error stopping VLC: {e}")
        playerInstance.isPlayingVideo = False
        playerInstance.currentVideoPath = None


def onVideoEnd(playerInstance):
    # Handle video end event from VLC
    print("Video ended, restarting...")
    if playerInstance.isPlayingVideo:
        playerInstance.videoloopTimer.start(100)  # 100ms delay


def restartVideo(playerInstance):
    # Restart the current video
    playerInstance.videoloopTimer.stop()
    if playerInstance.isPlayingVideo and playerInstance.currentVideoPath:
        print(f"Restarting video: {playerInstance.currentVideoPath}")
        try:
            # Stop and restart with local file
            playerInstance.vlcPlayer.stop()

            # Create media from local file path
            media = playerInstance.vlcInstance.media_new(
                playerInstance.currentVideoPath)

            # Set loop options for local playback
            # Large number for infinite loop
            media.add_option(":input-repeat=65535")
            media.add_option(":loop")

            playerInstance.vlcPlayer.set_media(media)
            playerInstance.vlcPlayer.play()

            print("Video restarted successfully")

        except Exception as e:
            print(f"Error restarting video: {e}")
