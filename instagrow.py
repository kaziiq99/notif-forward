#!/usr/bin/env python3
"""
instagrow.py — أداة زيادة متابعين إنستغرام (نسخة حديثة).
pip install instagrapi

الاستخدام:
    python3 instagrow.py grow -u USER -p PASS --hashtags "fitness,gym" -n 30
    python3 instagrow.py grow -u USER -s SESSIONID --hashtags "fitness,gym" -n 30
    python3 instagrow.py cleanup -u USER -p PASS -d 3
"""

from __future__ import annotations
import argparse, random, sqlite3, sys, time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        LoginRequired, PleaseWaitFewMinutes, RateLimitError,
        ChallengeRequired, ClientError, UserNotFound,
    )
except ImportError:
    sys.exit("ثبّت المكتبة: pip install instagrapi")


DB_PATH     = "instagrow.db"
SESSION_DIR = Path("sessions")

DEVICE = {
    "app_version": "329.0.0.41.93",
    "android_version": 30,
    "android_release": "11.0",
    "dpi": "480dpi",
    "resolution": "1080x1920",
    "manufacturer": "OnePlus",
    "device": "ONEPLUS A6003",
    "model": "ONEPLUS A6003",
    "cpu": "qcom",
    "version_code": "314665256",
}

LIMITS = {
    "follow":   {"hour": 50,  "day": 200},
    "like":     {"hour": 100, "day": 400},
    "comment":  {"hour": 15,  "day": 80},
    "unfollow": {"hour": 50,  "day": 150},
}

COMMENTS_AR = [
    "ماشاء الله 🔥", "إبداع حقيقي 👏", "استمر 🌟", "جميل جداً ❤️",
    "تحياتي لك 🙌", "أحسنت 👌", "روعة 💯", "كل التوفيق ✨",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT NOT NULL, ts TEXT NOT NULL, kind TEXT NOT NULL,
    target TEXT, ok INTEGER
);
CREATE INDEX IF NOT EXISTS idx_a ON actions(account, kind, ts);
CREATE TABLE IF NOT EXISTS followed (
    account TEXT NOT NULL, user_id TEXT NOT NULL, username TEXT,
    followed_at TEXT NOT NULL, unfollowed_at TEXT,
    followed_back INTEGER DEFAULT 0,
    PRIMARY KEY (account, user_id)
);
"""


class Store:
    def __init__(self, path=DB_PATH):
        self.con = sqlite3.connect(path)
        self.con.executescript(SCHEMA)
        self.con.commit()

    def log(self, account, kind, target, ok):
        self.con.execute(
            "INSERT INTO actions (account, ts, kind, target, ok) VALUES (?,?,?,?,?)",
            (account, datetime.utcnow().isoformat(), kind, target, 1 if ok else 0))
        self.con.commit()

    def count_since(self, account, kind, delta):
        since = (datetime.utcnow() - delta).isoformat()
        return self.con.execute(
            "SELECT COUNT(*) FROM actions WHERE account=? AND kind=? AND ts>=? AND ok=1",
            (account, kind, since)).fetchone()[0]

    def mark_followed(self, account, uid, username):
        self.con.execute(
            "INSERT OR REPLACE INTO followed (account, user_id, username, followed_at) "
            "VALUES (?,?,?,?)",
            (account, uid, username, datetime.utcnow().isoformat()))
        self.con.commit()

    def is_followed(self, account, uid):
        return self.con.execute(
            "SELECT 1 FROM followed WHERE account=? AND user_id=? AND unfollowed_at IS NULL",
            (account, uid)).fetchone() is not None

    def mark_unfollowed(self, account, uid):
        self.con.execute(
            "UPDATE followed SET unfollowed_at=? WHERE account=? AND user_id=?",
            (datetime.utcnow().isoformat(), account, uid))
        self.con.commit()

    def pending_unfollow(self, account, days):
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return self.con.execute(
            "SELECT user_id, username FROM followed "
            "WHERE account=? AND unfollowed_at IS NULL AND followed_back=0 AND followed_at<?",
            (account, cutoff)).fetchall()


class RateLimiter:
    def __init__(self, account, store):
        self.account = account
        self.store = store
        self.limits = {k: dict(v) for k, v in LIMITS.items()}

    def can(self, kind):
        lim = self.limits.get(kind)
        if not lim:
            return True
        if self.store.count_since(self.account, kind, timedelta(hours=1)) >= lim["hour"]:
            return False
        if self.store.count_since(self.account, kind, timedelta(days=1)) >= lim["day"]:
            return False
        return True

    def penalize(self, kind, factor=0.8):
        if kind in self.limits:
            self.limits[kind]["hour"] = max(1, int(self.limits[kind]["hour"] * factor))
            self.limits[kind]["day"]  = max(1, int(self.limits[kind]["day"]  * factor))

    def pause(self, mean=45.0, sd=20.0):
        time.sleep(max(5.0, random.gauss(mean, sd)))

    def warmup_pause(self):
        time.sleep(random.uniform(180, 420))


class InstaGrow:
    def __init__(self, username, password=None, sessionid=None, lang="ar"):
        self.username = username
        self.password = password
        self.sessionid = sessionid
        SESSION_DIR.mkdir(exist_ok=True)
        self.session_file = SESSION_DIR / f"{username}.json"
        self.store = Store()
        self.limiter = RateLimiter(username, self.store)
        self.lang = lang
        self.cl = None

    def _configure(self, cl):
        cl.set_device(DEVICE)
        try:
            cl.set_settings({"override_app_version": True})
        except Exception:
            pass

    def login(self):
        cl = Client()
        self._configure(cl)

        if self.sessionid:
            try:
                cl.login_by_sessionid(self.sessionid)
                cl.dump_settings(str(self.session_file))
                self.cl = cl
                print(f"[*] داخل (sessionid): @{self.username}")
                return cl
            except Exception as e:
                print(f"[!] فشل login بـsessionid: {e}")

        if self.session_file.exists():
            try:
                cl.load_settings(str(self.session_file))
                cl.login(self.username, self.password or "")
                self.cl = cl
                print(f"[*] داخل (session): @{self.username}")
                return cl
            except LoginRequired:
                pass
            except Exception as e:
                print(f"[!] فشل session: {e}")

        if not self.password:
            raise SystemExit("لازم -p PASSWORD أو -s SESSIONID")
        cl.login(self.username, self.password)
        cl.dump_settings(str(self.session_file))
        self.cl = cl
        print(f"[*] داخل: @{self.username}")
        return cl

    def collect_from_hashtags(self, tags, per_tag=25):
        out, seen = [], set()
        for tag in tags:
            try:
                medias = self.cl.hashtag_medias_recent(tag, amount=per_tag)
            except (ClientError, RateLimitError) as e:
                print(f"[!] hashtag {tag}: {e}")
                self.limiter.penalize("like")
                continue
            for m in medias:
                if m.user and str(m.user.pk) not in seen:
                    seen.add(str(m.user.pk))
                    out.append({
                        "uid": str(m.user.pk),
                        "username": m.user.username,
                        "media_pk": str(m.pk),
                    })
            self.limiter.pause(30, 15)
        return out

    def collect_from_followers(self, accounts, per_acc=40):
        out, seen = [], set()
        for acc in accounts:
            try:
                uid = self.cl.user_id_from_username(acc)
                followers = self.cl.user_followers(uid, amount=per_acc)
            except (ClientError, RateLimitError, UserNotFound) as e:
                print(f"[!] followers {acc}: {e}")
                self.limiter.penalize("follow")
                continue
            for pk, u in followers.items():
                if str(pk) not in seen:
                    seen.add(str(pk))
                    out.append({"uid": str(pk), "username": u.username})
            self.limiter.pause(45, 20)
        return out

    def do_follow(self, uid, username):
        if self.store.is_followed(self.username, uid):
            return False
        if not self.limiter.can("follow"):
            return False
        try:
            self.cl.user_follow(uid)
            self.store.mark_followed(self.username, uid, username)
            self.store.log(self.username, "follow", username or uid, True)
            print(f"[+] follow @{username or uid}")
            return True
        except PleaseWaitFewMinutes:
            print("[!] إنستغرام: استنى — ننام 15 دقيقة")
            self.limiter.penalize("follow")
            time.sleep(900)
            return False
        except (RateLimitError, ClientError) as e:
            print(f"[!] follow فشل: {e}")
            self.store.log(self.username, "follow", username or uid, False)
            self.limiter.penalize("follow")
            return False

    def do_like(self, media_pk):
        if not self.limiter.can("like"):
            return False
        try:
            self.cl.media_like(media_pk)
            self.store.log(self.username, "like", media_pk, True)
            return True
        except (RateLimitError, ClientError):
            self.store.log(self.username, "like", media_pk, False)
            self.limiter.penalize("like")
            return False

    def do_comment(self, media_pk):
        if not self.limiter.can("comment"):
            return False
        text = random.choice(COMMENTS_AR)
        try:
            self.cl.media_comment(media_pk, text)
            self.store.log(self.username, "comment", media_pk, True)
            print(f"[+] comment: {text}")
            return True
        except (RateLimitError, ClientError):
            self.store.log(self.username, "comment", media_pk, False)
            self.limiter.penalize("comment")
            return False

    def do_unfollow(self, uid):
        if not self.limiter.can("unfollow"):
            return False
        try:
            self.cl.user_unfollow(uid)
            self.store.mark_unfollowed(self.username, uid)
            self.store.log(self.username, "unfollow", uid, True)
            return True
        except (RateLimitError, ClientError):
            self.store.log(self.username, "unfollow", uid, False)
            return False

    def grow(self, hashtags=None, competitors=None,
             target_follows=30, like_ratio=3, comment_ratio=8):
        print(f"[*] {self.username}: جلسة نمو")
        targets = []
        if hashtags:
            targets += self.collect_from_hashtags(hashtags)
        if competitors:
            targets += self.collect_from_followers(competitors)
        random.shuffle(targets)
        print(f"[*] {len(targets)} هدف")

        followed = liked = commented = 0
        for t in targets:
            if followed >= target_follows:
                break
            if self.do_follow(t["uid"], t.get("username")):
                followed += 1
                if t.get("media_pk"):
                    for _ in range(like_ratio):
                        if self.do_like(t["media_pk"]):
                            liked += 1
                    if followed % comment_ratio == 0:
                        if self.do_comment(t["media_pk"]):
                            commented += 1
                self.limiter.pause(45, 20)
                if followed % 10 == 0:
                    print(f"[~] warmup pause بعد {followed}")
                    self.limiter.warmup_pause()

        print(f"[*] خلصت — follows={followed} likes={liked} comments={commented}")

    def cleanup(self, days=3, max_count=150):
        pending = self.store.pending_unfollow(self.username, days)[:max_count]
        print(f"[*] {len(pending)} حساب")
        n = 0
        for uid, username in pending:
            try:
                info = self.cl.user_info(uid)
                if not info.is_private:
                    following = self.cl.user_following(self.cl.user_id, uid)
                    if not following and self.do_unfollow(uid):
                        n += 1
                        print(f"[-] unfollow @{username}")
            except (ClientError, UserNotFound):
                pass
            self.limiter.pause(40, 15)
        print(f"[*] unfollowed {n}")


def cmd_grow(args):
    bot = InstaGrow(args.username, args.password, args.sessionid, lang=args.lang)
    bot.login()
    hashtags    = [t.strip() for t in args.hashtags.split(",")]    if args.hashtags    else None
    competitors = [c.strip() for c in args.competitors.split(",")] if args.competitors else None
    bot.grow(hashtags=hashtags, competitors=competitors, target_follows=args.follows)


def cmd_cleanup(args):
    bot = InstaGrow(args.username, args.password, args.sessionid)
    bot.login()
    bot.cleanup(days=args.days, max_count=args.max)


def build_parser():
    p = argparse.ArgumentParser(prog="instagrow")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grow")
    g.add_argument("-u", "--username", required=True)
    g.add_argument("-p", "--password", default=None)
    g.add_argument("-s", "--sessionid", default=None)
    g.add_argument("--hashtags", default=None)
    g.add_argument("--competitors", default=None)
    g.add_argument("-n", "--follows", type=int, default=30)
    g.add_argument("--lang", choices=["ar", "en"], default="ar")
    g.set_defaults(func=cmd_grow)

    c = sub.add_parser("cleanup")
    c.add_argument("-u", "--username", required=True)
    c.add_argument("-p", "--password", default=None)
    c.add_argument("-s", "--sessionid", default=None)
    c.add_argument("-d", "--days", type=int, default=3)
    c.add_argument("-m", "--max", type=int, default=150)
    c.set_defaults(func=cmd_cleanup)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] اتوقف")
        sys.exit(130)

