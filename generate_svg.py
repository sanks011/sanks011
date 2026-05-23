import json
import os
import re
import base64
import urllib.request
import ssl
from datetime import datetime
import glob

# Music Provider configuration: set to "ytmusic" or "spotify"
MUSIC_PROVIDER = os.environ.get("MUSIC_PROVIDER", "ytmusic")

# Make sure assets directory exists
os.makedirs("assets", exist_ok=True)

def fetch_lastfm_nowplaying(username, api_key):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={api_key}&limit=1&format=json"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
            res_data = json.loads(response.read().decode())
            tracks = res_data.get("recenttracks", {}).get("track", [])
            if tracks:
                track = tracks[0]
                is_playing = track.get("@attr", {}).get("nowplaying") == "true"
                name = track.get("name", "")
                artist = track.get("artist", {}).get("#text", "")
                album = track.get("album", {}).get("#text", "")
                
                images = track.get("image", [])
                image_url = ""
                for img in reversed(images):
                    if img.get("#text"):
                        image_url = img.get("#text")
                        break
                return is_playing, name, artist, album, image_url
    except Exception as e:
        print(f"Error fetching Last.fm track: {e}")
    return False, "", "", "", ""

def download_image_as_b64(url):
    if not url:
        return ""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            image_data = response.read()
            b64_data = base64.b64encode(image_data).decode("utf-8")
            mime_type = "image/png"
            if ".jpg" in url or ".jpeg" in url:
                mime_type = "image/jpeg"
            elif ".gif" in url:
                mime_type = "image/gif"
            return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Error downloading album art to base64: {e}")
    return ""

# Generate a unique cache buster based on execution timestamp
cache_buster = int(datetime.now().timestamp())

# Delete all old dynamic dashboard SVG files to keep the repo clean
for old_file in glob.glob("assets/contributions_*.svg") + glob.glob("assets/telemetry_*.svg") + glob.glob("assets/ytmusic_*.svg") + glob.glob("assets/contributions.svg") + glob.glob("assets/telemetry.svg") + glob.glob("assets/ytmusic.svg"):
    try:
        os.remove(old_file)
        print(f"Removed stale asset: {old_file}")
    except Exception as e:
        print(f"Error cleaning stale asset {old_file}: {e}")

# Fetch dynamic contributions from local prs.json
with open("prs.json") as f:
    data = json.load(f)

# Exclude personal repos and friends' repos
excluded_owners = ["sanks011", "sahnik0", "shovon0004", "abhijit5996", "shreyas0017"]

prs = data["data"]["user"]["pullRequests"]["nodes"]
orgs = {}

for pr in prs:
    repo = pr["repository"]
    owner = repo["owner"]["login"]
    
    if owner.lower() in [e.lower() for e in excluded_owners]:
        continue
    
    repo_name = repo["nameWithOwner"]
    if repo_name not in orgs:
        orgs[repo_name] = {
            "name": repo_name,
            "url": repo["url"],
            "description": repo.get("description", ""),
            "open": 0,
            "closed": 0,
            "merged": 0
        }
    
    state = pr["state"]
    if state == "OPEN":
        orgs[repo_name]["open"] += 1
    elif state == "CLOSED":
        orgs[repo_name]["closed"] += 1
    elif state == "MERGED":
        orgs[repo_name]["merged"] += 1

# Calculate total PRs across all repos
pr_total = sum(info["open"] + info["closed"] + info["merged"] for info in orgs.values())
repos_count = len(orgs)

# Count unique organizations
unique_orgs = set(org.split('/')[0] for org in orgs.keys())
orgs_count = len(unique_orgs)

# Function to fetch GitHub avatar and convert to base64
def get_base64_avatar(url):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
            content = response.read()
            encoded = base64.b64encode(content).decode('utf-8')
            mime = "image/png"
            if ".jpg" in url or ".jpeg" in url:
                mime = "image/jpeg"
            return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print(f"Error fetching avatar {url}: {e}")
        # Fallback to an empty base64 transparent 1x1 png pixel
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# Generate contributions SVG layout
grid_items = []
x_offsets = [25, 410]
start_y = 145
row_height = 56

for idx, (org_name, info) in enumerate(orgs.items()):
    col = idx % 2
    row = idx // 2
    x = x_offsets[col]
    y = start_y + (row * row_height)
    
    total = info["open"] + info["closed"] + info["merged"]
    owner = org_name.split('/')[0]
    repo = org_name.split('/')[1]
    
    avatar_url = f"https://github.com/{owner}.png?size=48"
    b64_avatar = get_base64_avatar(avatar_url)
    
    item_svg = f'''  <!-- Repo Card {idx} -->
  <g transform="translate({x}, {y})">
    <rect width="365" height="48" rx="6" fill="#110e2e" stroke="#1e1b4b" stroke-width="1"/>
    <clipPath id="avatar-clip-{idx}">
      <rect x="8" y="8" width="32" height="32" rx="4" />
    </clipPath>
    <image href="{b64_avatar}" x="8" y="8" width="32" height="32" clip-path="url(#avatar-clip-{idx})"/>
    
    <text x="48" y="21" class="repo-name">{repo}</text>
    <text x="48" y="36" class="repo-org">{owner}</text>
    
    <g transform="translate(295, 12)">
      <rect width="62" height="24" rx="4" fill="#1b153f" stroke="#8b5cf6" stroke-width="1" stroke-opacity="0.3"/>
      <text x="31" y="16" text-anchor="middle" class="pr-badge-txt">{total} PRs</text>
    </g>
  </g>'''
    grid_items.append(item_svg)

# Height calculated dynamically to comfortably fit all rows
total_rows = (len(orgs) + 1) // 2
svg_height = start_y + (total_rows * row_height) + 10
if svg_height < 420:
    svg_height = 420

contributions_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{svg_height}" viewBox="0 0 800 {svg_height}" fill="none">
  <style>
    .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800; font-size: 19px; fill: #a78bfa; letter-spacing: 0.5px; }}
    .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; fill: #64748b; font-weight: 500; }}
    .stat-val {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-weight: 800; font-size: 22px; fill: #f8fafc; }}
    .stat-label {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 9px; fill: #94a3b8; font-weight: 700; letter-spacing: 0.8px; }}
    .repo-name {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-weight: 700; font-size: 12px; fill: #f1f5f9; }}
    .repo-org {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 10px; fill: #64748b; font-weight: 600; }}
    .pr-badge-txt {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-size: 10.5px; font-weight: bold; fill: #a78bfa; }}
  </style>

  <!-- Frame border with glowing margins -->
  <rect x="1" y="1" width="798" height="{svg_height - 2}" rx="10" fill="#0d0b21" stroke="#1e1b4b" stroke-width="1.5"/>

  <!-- Header -->
  <g transform="translate(25, 28)">
    <text x="0" y="10" class="title">OPEN SOURCE TELEMETRY</text>
    <text x="0" y="26" class="subtitle">Distributed telemetry stream covering multi-tenant modules and integration pipelines</text>
  </g>

  <!-- Online status badge -->
  <g transform="translate(625, 25)">
    <rect width="150" height="22" rx="4" fill="#110e2e" stroke="#1e1b4b" stroke-width="1"/>
    <circle cx="15" cy="11" r="3.5" fill="#10b981"/>
    <text x="26" y="14.5" font-family="monospace" font-size="9" font-weight="bold" fill="#34d399">SYS_STATUS: LIVE</text>
  </g>

  <!-- Metrics row -->
  <g transform="translate(25, 72)">
    <rect width="240" height="52" rx="6" fill="#110e2e" stroke="#1e1b4b" stroke-width="1"/>
    <rect width="3.5" height="52" rx="1.5" fill="#8b5cf6"/>
    <text x="18" y="21" class="stat-label">REPOSITORIES INTEGRATED</text>
    <text x="18" y="42" class="stat-val">{repos_count}</text>
  </g>

  <g transform="translate(280, 72)">
    <rect width="240" height="52" rx="6" fill="#110e2e" stroke="#1e1b4b" stroke-width="1"/>
    <rect width="3.5" height="52" rx="1.5" fill="#c084fc"/>
    <text x="18" y="21" class="stat-label">AGGREGATED PULL REQUESTS</text>
    <text x="18" y="42" class="stat-val">{pr_total}</text>
  </g>

  <g transform="translate(535, 72)">
    <rect width="240" height="52" rx="6" fill="#110e2e" stroke="#1e1b4b" stroke-width="1"/>
    <rect width="3.5" height="52" rx="1.5" fill="#38bdf8"/>
    <text x="18" y="21" class="stat-label">ORGANIZATIONS IMPACTED</text>
    <text x="18" y="42" class="stat-val">{orgs_count}</text>
  </g>

  <!-- Grid rendering -->
{chr(10).join(grid_items)}
</svg>'''

with open(f"assets/contributions_{cache_buster}.svg", "w") as f:
    f.write(contributions_svg)

# Calculate uptime days since March 31, 2005
birthday = datetime(2005, 3, 31)
today = datetime.now()
days_delta = (today - birthday).days

# Generate Telemetry Dashboard Console SVG
telemetry_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="340" viewBox="0 0 800 340" fill="none">
  <style>
    .term-title {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 11px; fill: #94a3b8; font-weight: 600; }}
    .log-tag {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 11.5px; font-weight: bold; }}
    .log-val {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 11.5px; fill: #e2e8f0; }}
    .chart-label {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 10px; fill: #64748b; font-weight: bold; }}
    .chart-bar-bg {{ fill: #070514; stroke: #1e1b4b; stroke-width: 1; }}
  </style>

  <!-- Outer shell -->
  <rect x="1" y="1" width="798" height="338" rx="10" fill="#0d0b21" stroke="#1e1b4b" stroke-width="1.5"/>
  
  <!-- Terminal Top Bar -->
  <rect x="2" y="2" width="796" height="28" rx="8" fill="#110e2e" stroke="#1e1b4b" stroke-width="1"/>
  
  <!-- Colored Window Controls -->
  <circle cx="16" cy="16" r="4.5" fill="#ef4444"/>
  <circle cx="30" cy="16" r="4.5" fill="#eab308"/>
  <circle cx="44" cy="16" r="4.5" fill="#22c55e"/>
  
  <text x="400" y="19" text-anchor="middle" class="term-title">sankalpa@telemetry: ~ (v2.1.0-live)</text>

  <!-- Grid Separator Line -->
  <line x1="390" y1="45" x2="390" y2="320" stroke="#1e1b4b" stroke-dasharray="4 4"/>

  <!-- LEFT PANEL: Core Node Telemetry -->
  <g transform="translate(25, 55)">
    <!-- System Status -->
    <g transform="translate(0, 0)">
      <text x="0" y="15" class="log-tag" fill="#a78bfa">SYS_STATUS:</text>
      <rect x="110" y="2" width="135" height="18" rx="4" fill="#064e3b" stroke="#10b981" stroke-width="1" stroke-opacity="0.4"/>
      <text x="120" y="14" font-family="monospace" font-size="10.5" font-weight="bold" fill="#34d399">FULLY_OPERATIONAL</text>
    </g>

    <!-- Uptime -->
    <g transform="translate(0, 32)">
      <text x="0" y="15" class="log-tag" fill="#a78bfa">SYS_UPTIME:</text>
      <text x="110" y="15" class="log-val">{days_delta} days (since 31.03.2005)</text>
    </g>

    <!-- Energy Source -->
    <g transform="translate(0, 64)">
      <text x="0" y="15" class="log-tag" fill="#a78bfa">POWER_SRC:</text>
      <text x="110" y="15" class="log-val" fill="#fb7185">Caffeine Latte [100% active]</text>
    </g>

    <!-- Neural Correlation Threads -->
    <g transform="translate(0, 96)">
      <text x="0" y="15" class="log-tag" fill="#a78bfa">SYS_THREADS:</text>
      <text x="110" y="15" class="log-val">42 active neural subthreads</text>
    </g>
    
    <!-- Focus Matrix state -->
    <g transform="translate(0, 128)">
      <text x="0" y="15" class="log-tag" fill="#a78bfa">FOCUS_MODE:</text>
      <text x="110" y="15" class="log-val" fill="#c084fc">Hyper-Focus [Soundtrack: Active]</text>
    </g>
  </g>

  <!-- LEFT PANEL: Technical Load Graphs -->
  <g transform="translate(25, 230)">
    <text x="0" y="10" font-family="monospace" font-size="11" font-weight="bold" fill="#94a3b8">REALTIME SYSTEMS LOAD:</text>
    
    <!-- Graph 1: AI Models -->
    <g transform="translate(0, 20)">
      <text x="0" y="12" class="chart-label">AI_MODELS</text>
      <rect x="90" y="2" width="180" height="12" rx="3" class="chart-bar-bg"/>
      <rect x="91" y="3" width="144" height="10" rx="2" fill="#8b5cf6"/>
      <text x="280" y="12" font-family="monospace" font-size="10.5" font-weight="bold" fill="#a78bfa">80%</text>
    </g>

    <!-- Graph 2: MERN DB -->
    <g transform="translate(0, 40)">
      <text x="0" y="12" class="chart-label">MERN_DB</text>
      <rect x="90" y="2" width="180" height="12" rx="3" class="chart-bar-bg"/>
      <rect x="91" y="3" width="180" height="10" rx="2" fill="#38bdf8"/>
      <text x="280" y="12" font-family="monospace" font-size="10.5" font-weight="bold" fill="#38bdf8">PEAK</text>
    </g>

    <!-- Graph 3: GIT SYNC -->
    <g transform="translate(0, 60)">
      <text x="0" y="12" class="chart-label">GIT_MERGE</text>
      <rect x="90" y="2" width="180" height="12" rx="3" class="chart-bar-bg"/>
      <rect x="91" y="3" width="90" height="10" rx="2" fill="#10b981"/>
      <text x="280" y="12" font-family="monospace" font-size="10.5" font-weight="bold" fill="#34d399">ACTIVE</text>
    </g>
  </g>

  <!-- RIGHT PANEL: Live Processes daemon logs -->
  <g transform="translate(415, 55)">
    <text x="0" y="12" font-family="monospace" font-size="11" font-weight="bold" fill="#94a3b8">RUNNING PROCESS DAEMON:</text>
    
    <!-- Logging Terminal Box -->
    <rect x="0" y="22" width="360" height="235" rx="6" fill="#070514" stroke="#1e1b4b" stroke-width="1"/>
    
    <!-- Console Logs -->
    <g transform="translate(15, 45)">
      <text x="0" y="0" font-family="monospace" font-size="10.5" fill="#64748b">[sys] initialization protocol fully complete.</text>
      <text x="0" y="22" font-family="monospace" font-size="10.5" fill="#38bdf8">[sys] indexing_brain_database: active</text>
      <text x="0" y="44" font-family="monospace" font-size="10.5" fill="#38bdf8">[sys] compiling_future_ventures: active</text>
      <text x="0" y="66" font-family="monospace" font-size="10.5" fill="#38bdf8">[sys] fine_tuning_personality_matrices: active</text>
      <text x="0" y="88" font-family="monospace" font-size="10.5" fill="#8b5cf6">[sys] tethering LangChain autonomous web agents...</text>
      <text x="0" y="110" font-family="monospace" font-size="10.5" fill="#10b981">[sys] docker containers protected against env-bugs.</text>
      <text x="0" y="132" font-family="monospace" font-size="10.5" fill="#a78bfa">[sys] telemetry dashboard refresh: completed successfully.</text>
      <text x="0" y="154" font-family="monospace" font-size="10.5" fill="#64748b">[sys] sleeping for 86400s (telemetry engine daemon idle)...</text>
      
      <!-- Blinking Cursor -->
      <text x="0" y="176" font-family="monospace" font-size="11" font-weight="bold" fill="#34d399">sankalpa@telemetry:~$ _</text>
    </g>
  </g>
</svg>'''

with open(f"assets/telemetry_{cache_buster}.svg", "w") as f:
    f.write(telemetry_svg)

# Fetch Last.fm details for music scrobbling
lastfm_username = os.environ.get("LASTFM_USERNAME", "sankalpasarkar")
lastfm_api_key = os.environ.get("LASTFM_API_KEY", "0fb784e9ef782d1cd606c15d21dee184")

is_playing, song_title, artist, album, art_url = fetch_lastfm_nowplaying(lastfm_username, lastfm_api_key)

# Sanitize details for XML safety
song_title = song_title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
artist = artist.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
album = album.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

b64_art = download_image_as_b64(art_url) if is_playing else ""

# Set brand-specific styling variables based on MUSIC_PROVIDER configuration
if MUSIC_PROVIDER == "spotify":
    theme_color = "#1db954"
    brand_badge_text = "SPOTIFY SESSION"
    badge_bg_color = "rgba(29, 185, 84, 0.12)"
    badge_txt_color = "#1db954"
    shadow_fill = "#1db954"
    border_stop1 = "#1db954"
    border_stop2 = "#8b5cf6"
    brand_logo_svg = '''
    <g transform="translate(415, 20)">
      <circle cx="15" cy="15" r="14" fill="#1db954" />
      <path d="M 7.5 11 C 12 8.5, 18 8.5, 22.5 11" stroke="#0a0817" stroke-width="2.5" stroke-linecap="round" fill="none" />
      <path d="M 9 15 C 13 13, 17 13, 21 15" stroke="#0a0817" stroke-width="2" stroke-linecap="round" fill="none" />
      <path d="M 10.5 19 C 13.5 17.5, 16.5 17.5, 19.5 19" stroke="#0a0817" stroke-width="1.8" stroke-linecap="round" fill="none" />
    </g>'''
else:  # Default: "ytmusic"
    theme_color = "#ff0000"
    brand_badge_text = "YOUTUBE MUSIC"
    badge_bg_color = "rgba(255, 0, 0, 0.12)"
    badge_txt_color = "#ff0000"
    shadow_fill = "#ff0000"
    border_stop1 = "#ff0000"
    border_stop2 = "#8b5cf6"
    brand_logo_svg = '''
    <g transform="translate(415, 20)">
      <circle cx="15" cy="15" r="14" fill="#ff0000" />
      <circle cx="15" cy="15" r="9" fill="#0a0817" stroke="#ff0000" stroke-width="1" />
      <path d="M 13 11 L 19 15 L 13 19 Z" fill="#ffffff" />
    </g>'''

if is_playing:
    status_label = brand_badge_text
    spinning_class = "vinyl-record"
    progress_bar_animate = '<animate attributeName="width" from="0" to="260" dur="240s" repeatCount="indefinite"/>'
    progress_dot_animate = '<animate attributeName="cx" from="0" to="260" dur="240s" repeatCount="indefinite"/>'
    active_play_stroke = theme_color
    timer_right = "04:20"
    progress_bar_color = theme_color
else:
    status_label = "DEV FOCUS MODE"
    spinning_class = ""
    progress_bar_animate = ""
    progress_dot_animate = ""
    active_play_stroke = "#64748b"
    timer_right = "--:--"
    progress_bar_color = "#475569"
    song_title = "Caffeine &amp; Neural Networks"
    artist = "Sankalpa Sarkar — Dev Focus Vibe"

if is_playing and b64_art:
    album_art_rendering = f'''
    <!-- Album Art: Glowing Spinning Vinyl Record -->
    <g class="{spinning_class}">
      <circle cx="60" cy="70" r="42" fill="#18142c" stroke="{theme_color}" stroke-width="1.5" />
      <circle cx="60" cy="70" r="32" fill="#0d0a1b" stroke="#3b0764" stroke-width="1" />
      
      <clipPath id="circle-art-clip">
        <circle cx="60" cy="70" r="28" />
      </clipPath>
      <image href="{b64_art}" x="32" y="42" width="56" height="56" clip-path="url(#circle-art-clip)"/>
      
      <circle cx="60" cy="70" r="28" fill="none" stroke="#2e2b42" stroke-width="0.5" stroke-dasharray="10 5" />
      <circle cx="60" cy="70" r="18" fill="none" stroke="#2e2b42" stroke-width="0.5" stroke-dasharray="4 2" />
      <circle cx="60" cy="70" r="6" fill="#0d0a1b" stroke="{theme_color}" stroke-width="0.5" />
      <circle cx="60" cy="70" r="1.5" fill="#ffffff" />
    </g>'''
else:
    album_art_rendering = f'''
    <!-- Album Art: Glowing Spinning Vinyl Record -->
    <g class="{spinning_class}">
      <circle cx="60" cy="70" r="42" fill="#18142c" stroke="{theme_color}" stroke-width="1.5" />
      <circle cx="60" cy="70" r="32" fill="#0d0a1b" stroke="#3b0764" stroke-width="1" />
      <circle cx="60" cy="70" r="24" fill="none" stroke="#2e2b42" stroke-width="0.5" stroke-dasharray="10 5" />
      <circle cx="60" cy="70" r="16" fill="none" stroke="#2e2b42" stroke-width="0.5" stroke-dasharray="4 2" />
      <circle cx="60" cy="70" r="12" fill="{theme_color}" />
      <circle cx="60" cy="70" r="3" fill="#0d0a1b" />
    </g>'''

ytmusic_svg = f'''<svg width="480" height="140" viewBox="0 0 480 140" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .song-title {{ font: 700 15px 'Inter', system-ui, sans-serif; fill: #ffffff; }}
    .artist {{ font: 500 12px 'Inter', system-ui, sans-serif; fill: #a78bfa; }}
    .time {{ font: 500 10px monospace; fill: #94a3b8; }}
    .badge {{ font: 600 9px monospace; fill: {badge_txt_color}; letter-spacing: 1px; }}
    .vinyl-record {{ transform-origin: 60px 70px; animation: spin 8s linear infinite; }}
    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
  </style>

  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="480" y2="140" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0a0817" />
      <stop offset="100%" stop-color="#120e2e" />
    </linearGradient>
    <linearGradient id="borderGrad" x1="0" y1="0" x2="480" y2="140" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{border_stop1}" stop-opacity="0.8" />
      <stop offset="100%" stop-color="{border_stop2}" stop-opacity="0.4" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Glowing background drop shadow -->
  <rect x="8" y="8" width="464" height="124" rx="16" fill="{shadow_fill}" opacity="0.1" filter="url(#glow)" />

  <!-- Main Player Container -->
  <rect x="8" y="8" width="464" height="124" rx="16" fill="url(#bgGrad)" stroke="url(#borderGrad)" stroke-width="1.5" />

  {album_art_rendering}

  <!-- Track Information -->
  <g transform="translate(120, 28)">
    <!-- Dynamic Playing Badge -->
    <rect x="0" y="0" width="125" height="18" rx="9" fill="{badge_bg_color}" />
    <circle cx="11" cy="9" r="3.5" fill="{badge_txt_color}">
      <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite" />
    </circle>
    <text x="22" y="10" dominant-baseline="middle" class="badge">{status_label}</text>

    <!-- Song & Artist Details -->
    <text x="0" y="36" class="song-title">{song_title}</text>
    <text x="0" y="54" class="artist">{artist}</text>
  </g>

  <!-- Player Controls (Bottom Progress Section) -->
  <g transform="translate(120, 95)">
    <!-- Progress Bar Background -->
    <rect x="0" y="6" width="260" height="4" rx="2" fill="#334155" />
    <!-- Active Progress Bar -->
    <rect x="0" y="6" width="0" height="4" rx="2" fill="{progress_bar_color}">
      {progress_bar_animate}
    </rect>
    <!-- Active slider node -->
    <circle cx="0" cy="8" r="5" fill="#ffffff">
      {progress_dot_animate}
    </circle>
    
    <!-- Track Timers -->
    <text x="0" y="24" class="time">00:00</text>
    <text x="260" y="24" text-anchor="end" class="time">{timer_right}</text>
  </g>

  <!-- Interactive Control Icons -->
  <g transform="translate(395, 78)" stroke="#94a3b8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <!-- Skip Back -->
    <path d="M 4 6 L 4 18 M 12 6 L 6 12 L 12 18" stroke="#94a3b8" />
    <!-- Play/Pause Button -->
    <circle cx="28" cy="12" r="10" fill="{theme_color}" fill-opacity="0.1" stroke="{theme_color}" />
    <path d="M 25 8 V 16 M 31 8 V 16" stroke="{active_play_stroke}" stroke-width="2" />
    <!-- Skip Forward -->
    <path d="M 44 6 L 50 12 L 44 18" />
    <path d="M 52 6 L 52 18" />
  </g>

  <!-- Brand Accent Icon -->
  {brand_logo_svg}
</svg>'''

with open(f"assets/ytmusic_{cache_buster}.svg", "w") as f:
    f.write(ytmusic_svg)

# Update README
with open("README.md") as f:
    content = f.read()

start = "<!-- OSS_CONTRIBUTIONS_START -->"
end = "<!-- OSS_CONTRIBUTIONS_END -->"
new_block = f"{start}\n<!-- auto-updated by .github/workflows/update-contributions.yml -->\n\n<p align=\"center\">\n  <img src=\"./assets/contributions_{cache_buster}.svg\" alt=\"Open Source Contributions Telemetry\" width=\"100%\" />\n</p>\n\n{end}"

updated = re.sub(
    rf"{re.escape(start)}.*?{re.escape(end)}",
    new_block,
    content,
    flags=re.DOTALL
)

# Replace telemetry block with beautiful terminal console SVG
telemetry_start = "<!-- TELEMETRY_START -->"
telemetry_end = "<!-- TELEMETRY_END -->"
new_telemetry_block = f"{telemetry_start}\n<!-- auto-updated by .github/workflows/update-contributions.yml -->\n\n<p align=\"center\">\n  <img src=\"./assets/telemetry_{cache_buster}.svg\" alt=\"System Status Telemetry Console\" width=\"100%\" />\n</p>\n\n{telemetry_end}"

updated = re.sub(
    rf"{re.escape(telemetry_start)}.*?{re.escape(telemetry_end)}",
    new_telemetry_block,
    updated,
    flags=re.DOTALL
)

# Replace music block with beautiful YouTube Music SVG
music_start = "<!-- MUSIC_START -->"
music_end = "<!-- MUSIC_END -->"
new_music_block = f"{music_start}\n<!-- auto-updated by .github/workflows/update-contributions.yml -->\n\n<p align=\"center\">\n  <img src=\"./assets/ytmusic_{cache_buster}.svg\" alt=\"YouTube Music Player\" width=\"480\" />\n</p>\n\n{music_end}"

updated = re.sub(
    rf"{re.escape(music_start)}.*?{re.escape(music_end)}",
    new_music_block,
    updated,
    flags=re.DOTALL
)

with open("README.md", "w") as f:
    f.write(updated)

print(f"Successfully compiled contributions, telemetry, and YT Music SVGs! Cache buster: {cache_buster}")
