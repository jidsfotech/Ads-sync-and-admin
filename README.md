# Billboard advertisment Schedule Backend Service and the Ads media Player

📌 Overview

The Billboard Ad-Sync is a cross-platform digital signage solution designed to Schedule, fetch, and display multimedia advertisements (images, GIFs, and videos) on electronic billboards.

The project integrates with a backend API and WebSocket server to dynamically update active schedules in real-time. Each billboard device runs a lightweight player application that ensures synchronized playback of ads according to predefined schedules.

This system is designed to be flexible enough to run on Windows, Linux, and Raspberry Pi, making it deployable in diverse environments.

🎯 Aim & Objectives
Aim

To build a synchronized, cross-platform digital signage system that can fetch, schedule, and loop multimedia advertisements seamlessly, while ensuring billboards stay updated in real-time.

Objectives

# Advertisement Scheduling

- Fetch ad schedules from a backend API.

- Validate schedules based on start and end times.

- Ensure only active ads are displayed.

# Media Playback

- Display images (.jpg, .png) with scaling and smooth rendering.

- Animate GIFs directly from Cloudinary URLs.

- Play videos (.mp4, other supported formats) using VLC for maximum compatibility across platforms.

- Loop videos seamlessly until their allocated duration elapses.

- Real-time Updates

Listen to backend WebSocket channels for schedule updates.

- Update the playlist dynamically without restarting the player.

# Cross-Platform Support

- Windows (x64) using VLC integration.

- Linux-based systems (including Raspberry Pi) with PyQt5 + VLC.

- Raspberry Pi deployment as lightweight digital signage clients.

# Seamless User Experience

- Smooth transitions between different media types (image → video → GIF → image).

- Gapless video looping with VLC double-buffering.

- Fail-safe fallback if an ad fails to load (skip gracefully).

# ⚙️ Tech Stack

# Frontend/Player

PyQt5
– GUI framework

python-vlc
– Video playback backend

qasync
– Async event loop for PyQt5

aiohttp
– Async HTTP & WebSocket client

isodate
– ISO 8601 duration parsing

# Backend API (integrated with this player)

FastAPI (Python) – REST API + WebSockets

Cloudinary – Media storage (images, GIFs, videos)

MySQL/PostgreSQL – Schedule persistence

🔑 Key Features

✅ Display images, GIFs, and videos directly from Cloudinary.

✅ Schedule-based playback with ISO 8601 duration support.

✅ Real-time updates via WebSocket.

✅ Cross-platform compatibility (Windows, Linux, Raspberry Pi).

✅ Seamless video looping with VLC double-player approach.

✅ Failsafe fallback (skips broken media gracefully).

# 🚀 How It Works

Player Startup

Fetches the latest ad schedules from the backend.

Filters active schedules (valid start/end times).

Ad Playback

Starts from the first active schedule and plays media sequentially.

Each ad plays for its configured duration (e.g., 5 min, 1 min).

Images and GIFs are displayed using PyQt5.

Videos are played using VLC with gapless looping until duration elapses.

Continuous Loop

When the last ad in the schedule finishes, it cycles back to the first.

Dynamic Updates

If new schedules are pushed from the backend via WebSocket, the playlist updates in real-time.

# 🖥️ Target Use Case

Billboards / Digital Signage in public spaces.

Advertising Screens in malls, airports, and bus terminals.

IoT-style deployment on Raspberry Pi-powered kiosks.
