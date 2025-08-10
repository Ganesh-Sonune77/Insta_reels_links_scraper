from flask import Flask, render_template, request
import instaloader
import os
import re
import urllib.parse
import time
import random
from datetime import datetime

app = Flask(__name__)
OUTPUT_FILE = "scraped_reels.txt"
SESSION_FILE = "session-your_instagram_username"  # <- CLI से जो filename बना था

def extract_username(link_or_username):
    if link_or_username.startswith("http"):
        parsed = urllib.parse.urlparse(link_or_username)
        username = parsed.path.strip("/").split("/")[0]
    else:
        username = link_or_username
    username = re.sub(r'[@/?#&=]+.*', '', username).strip(".").strip("/")
    return username

def get_loader():
    L = instaloader.Instaloader()
    # Load existing session instead of login each time
    try:
        L.load_session_from_file(None, SESSION_FILE)
        print("[✅] Loaded session from file")
    except Exception as e:
        print("[⚠] Could not load session file:", e)
    # Always set a real user agent
    L.context._session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    return L

def scrape_reels_links(username, start, end):
    username = extract_username(username)
    L = get_loader()

    # Rate-limit check: अगर session invalid, तुरंत user को बताएं
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.LoginRequiredException:
        raise Exception("Authentication required. Please re-run instaloader -l your_instagram_username to refresh session.")
    except Exception as e:
        raise Exception(f"Profile fetch failed: {e}")

    posts = list(profile.get_posts())
    reels = [p for p in posts if p.typename == "GraphVideo"][::-1]
    if start < 1 or end > len(reels) or start > end:
        raise Exception("Invalid start/end range.")

    selected = reels[start-1:end]
    links = [f"https://www.instagram.com/reel/{p.shortcode}/" for p in selected]

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write("\n\n")
        f.write(f"🕒 {datetime.now():%d-%m-%Y %H:%M:%S} | Start:{start} End:{end}\n")
        for i, link in enumerate(links, 1):
            f.write(link+"\n")
            if i % 10 == 0:
                f.write("\n")
            time.sleep(random.uniform(1.5, 3.5))
    return links

@app.route("/", methods=["GET", "POST"])
def home():
    links, error = [], None
    if request.method == "POST":
        user = request.form["username"]
        try:
            s = int(request.form["start"]); e = int(request.form["end"])
            links = scrape_reels_links(user, s, e)
        except Exception as ex:
            error = str(ex)
    return render_template("index.html", links=links, error=error)

if __name__ == "__main__":
    app.run(debug=True)