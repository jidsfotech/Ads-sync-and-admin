import os
os.add_dll_directory(r"C:\Program Files\VideoLAN\VLC")
import vlc
import time

# Create VLC instance
instance = vlc.Instance("--quiet", "--no-xlib")
player = instance.media_player_new()

media = instance.media_new("https://res.cloudinary.com/jidsfotech/video/upload/v1756818825/wm2tuzwnuz5rp9otflj2.mp4", "demux=avformat")
player.set_media(media)

player.play()

time.sleep(35)  # keep alive for video to finish
