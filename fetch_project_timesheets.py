import glob
import os
import re
import subprocess
import time

OUT = os.path.dirname(os.path.abspath(__file__))
LESSONS = [
    "Project basics and your first task", "Project stages and statuses", "Customize projects", "Top bar",
    "Creating tasks from emails and web forms", "Creating tasks from sales orders", "Subtasks",
    "Task dependencies", "Recurring tasks", "Visibility and collaboration", "Automations", "Milestones",
    "Timesheets basics", "Timesheets configuration and leaderboard", "Invoicing project tasks",
    "Project dashboard", "Measuring project's profitability", "Customer ratings",
]
BASE = ["yt-dlp", "--js-runtimes", "node", "--extractor-args", "youtube:player_client=android"]

def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")

def choose_video(title):
    p = run(BASE + [f"ytsearch5:{title} Odoo", "--flat-playlist", "--print", "%(id)s|||%(title)s|||%(channel)s", "--no-playlist"])
    rows = [line.split("|||", 2) for line in p.stdout.splitlines() if "|||" in line]
    candidates = [r for r in rows if len(r) == 3 and "odoo" in r[2].lower() and title.lower() in r[1].lower()]
    if not candidates:
        candidates = [r for r in rows if len(r) == 3 and "odoo" in r[2].lower()]
    return (candidates[0][0], candidates[0][1]) if candidates else (None, None)

def clean_vtt(path):
    seen, lines = set(), []
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or re.fullmatch(r"\d+", s) or "-->" in s:
                continue
            s = re.sub(r"<[^>]+>", "", s).strip()
            if s and s not in seen:
                seen.add(s)
                lines.append(s)
    return " ".join(lines)

results = []
for n, title in enumerate(LESSONS, 1):
    vid, found_title = choose_video(title)
    if not vid:
        print(f"[{n}/{len(LESSONS)}] NOT FOUND: {title}", flush=True)
        results.append((title, None, None, "video not found"))
        continue
    print(f"[{n}/{len(LESSONS)}] {title} => {vid} ({found_title})", flush=True)
    prefix = os.path.join(OUT, f"Project-Timesheets-{vid}")
    p = run(BASE + ["--skip-download", "--write-sub", "--write-auto-sub", "--sub-lang", "en", "--sub-format", "vtt/best", "--output", prefix + ".%(ext)s", f"https://www.youtube.com/watch?v={vid}"])
    vtts = glob.glob(prefix + "*.vtt")
    text = clean_vtt(vtts[0]) if vtts else None
    results.append((title, vid, found_title, text))
    print(f"    {'OK: '+str(len(text))+' chars' if text else 'NO ENGLISH SUBTITLES'}", flush=True)
    if n < len(LESSONS):
        time.sleep(2)

out = os.path.join(OUT, "Project-Timesheets.txt")
with open(out, "w", encoding="utf-8") as f:
    for i, (title, vid, found_title, text) in enumerate(results):
        f.write(f"{title}\n{'='*len(title)}\n")
        if vid:
            f.write(f"https://www.youtube.com/watch?v={vid}\n")
            if found_title and title.lower() not in found_title.lower():
                f.write(f"Matched video title: {found_title}\n")
        f.write("\n" + (text if text else "[No English subtitles available or video not found]") + "\n")
        if i < len(results)-1:
            f.write("\n\n")
print(f"SAVED: {out}")
