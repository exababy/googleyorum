"""Google yorumlarına Gemini ile otomatik cevap.

Komutlar:
  auth        Google hesabıyla giriş yap (bir kez)
  locations   Hesaptaki işletmeleri ve GOOGLE_LOCATION değerlerini listele
  models      Kullanılabilir Gemini modellerini listele
  test        Örnek bir yorum için cevap üret (Google'a dokunmaz)
  run         Cevapsız yorumları bir kez işle
  watch       Sürekli çalış, POLL_SECONDS'da bir yeni yorumları işle
"""
import argparse
import os
import sys
import time

from dotenv import load_dotenv

from .ai import ReplyGenerator
from .google_business import STARS, BusinessClient, get_credentials


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise SystemExit(f".env dosyasında {name} tanımlı değil")
    return value


def make_generator() -> ReplyGenerator:
    with open(env("PROMPT_FILE", "prompt.txt"), encoding="utf-8") as f:
        prompt = f.read()
    return ReplyGenerator(env("GEMINI_API_KEY"), env("GEMINI_MODEL", "gemini-flash-latest"), prompt)


def make_client(interactive: bool = False) -> BusinessClient:
    return BusinessClient(get_credentials(env("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json"), interactive))


def cmd_auth(_):
    make_client(interactive=True)
    print("Giriş başarılı, token.json kaydedildi.")


def cmd_locations(_):
    client = make_client()
    for acc in client.list_accounts():
        print(f"Hesap: {acc.get('accountName')} ({acc['name']})")
        for loc in client.list_locations(acc["name"]):
            loc_id = loc["name"]  # locations/456
            print(f"  {loc.get('title')}\n    GOOGLE_LOCATION={acc['name']}/{loc_id}")


def cmd_models(_):
    for name in make_generator().list_models():
        print(name.removeprefix("models/"))


def cmd_test(args):
    reply = make_generator().generate(args.name, args.stars, args.comment)
    print(reply)


def process_once(client: BusinessClient, gen: ReplyGenerator, dry_run: bool, min_stars: int) -> int:
    location = env("GOOGLE_LOCATION")
    count = 0
    for review in client.list_reviews(location):
        if review.get("reviewReply"):
            continue
        stars = STARS.get(review.get("starRating"), 0)
        reviewer = review.get("reviewer", {}).get("displayName", "")
        comment = review.get("comment", "")
        if stars < min_stars:
            print(f"- Atlandı ({stars}★, MIN_STARS={min_stars}): {reviewer}")
            continue
        try:
            reply = gen.generate(reviewer, stars, comment)
        except Exception as e:
            print(f"! Gemini hatası ({reviewer}): {e}", file=sys.stderr)
            continue
        print(f"\n[{stars}★] {reviewer}: {comment or '(yorumsuz)'}\n→ {reply}")
        if dry_run:
            print("  (DRY_RUN: gönderilmedi)")
        else:
            client.reply(review["name"], reply)
            print("  ✓ Gönderildi")
        count += 1
    return count


def run_settings():
    dry_run = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes", "evet")
    return dry_run, int(os.getenv("MIN_STARS", "1"))


def cmd_run(_):
    dry_run, min_stars = run_settings()
    n = process_once(make_client(), make_generator(), dry_run, min_stars)
    print(f"\n{n} yorum işlendi.")


def cmd_watch(_):
    dry_run, min_stars = run_settings()
    if dry_run:
        # Dry-run'da cevap gönderilmediği için aynı yorumlar her turda tekrar işlenirdi
        raise SystemExit("watch modu için .env içinde DRY_RUN=false olmalı. Denemek için 'run' kullanın.")
    client, gen = make_client(), make_generator()
    interval = int(os.getenv("POLL_SECONDS", "600"))
    while True:
        try:
            n = process_once(client, gen, dry_run, min_stars)
            print(f"[{time.strftime('%H:%M:%S')}] {n} yorum işlendi, {interval} sn bekleniyor...")
        except Exception as e:
            print(f"! Hata: {e}", file=sys.stderr)
        time.sleep(interval)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(prog="yorumbot", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth").set_defaults(func=cmd_auth)
    sub.add_parser("locations").set_defaults(func=cmd_locations)
    sub.add_parser("models").set_defaults(func=cmd_models)
    t = sub.add_parser("test")
    t.add_argument("--name", default="Ahmet Yılmaz")
    t.add_argument("--stars", type=int, default=5)
    t.add_argument("--comment", default="Yemekler çok lezzetliydi, personel çok ilgiliydi.")
    t.set_defaults(func=cmd_test)
    sub.add_parser("run").set_defaults(func=cmd_run)
    sub.add_parser("watch").set_defaults(func=cmd_watch)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
