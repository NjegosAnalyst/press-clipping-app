"""Pozadinski (background) poslovi koji periodično provjeravaju RSS feedove."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import CHECK_INTERVAL_HOURS, DEEP_CHECK_HOUR, YOUTUBE_CHECK_INTERVAL_HOURS
from fetcher import check_feeds, check_feeds_deep
from youtube_fetcher import check_youtube

_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        check_feeds,
        trigger=IntervalTrigger(hours=CHECK_INTERVAL_HOURS),
        id="rss_check",
        replace_existing=True,
    )
    # YouTube provjera na svoj, rjeđi interval (odvojeno od RSS/Google News
    # provjere) zbog dnevne kvote YouTube Data API-ja.
    _scheduler.add_job(
        check_youtube,
        trigger=IntervalTrigger(hours=YOUTUBE_CHECK_INTERVAL_HOURS),
        id="youtube_check",
        replace_existing=True,
    )
    # Duboka provjera (Google News "when:30d") - jednom dnevno, van redovnog
    # intervala, da uhvati članke propuštene u redovnim provjerama.
    _scheduler.add_job(
        check_feeds_deep,
        trigger=CronTrigger(hour=DEEP_CHECK_HOUR, minute=0),
        id="rss_check_deep",
        replace_existing=True,
    )
    _scheduler.start()
    return _scheduler
