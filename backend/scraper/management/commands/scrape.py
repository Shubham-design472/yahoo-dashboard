import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from scraper.client import YahooFinanceError
from scraper.service import scrape_ticker


class Command(BaseCommand):
    help = "Scrape Yahoo Finance data for one or more ticker symbols."

    def add_arguments(self, parser):
        parser.add_argument("symbols", nargs="*", help="e.g. AAPL MSFT TSLA")
        parser.add_argument("--all", action="store_true", help="scrape every symbol in the seed file")
        parser.add_argument("--file", default="tickers.json", help="path to seed JSON (default: tickers.json)")

    def handle(self, *args, **options):
        if options["all"]:
            path = Path(settings.BASE_DIR) / options["file"]
            if not path.exists():
                raise CommandError(f"Seed file not found: {path}")
            data = json.loads(path.read_text())
            targets = [(row["symbol"], row.get("company_name", "")) for row in data]
        else:
            targets = [(s, "") for s in options["symbols"]]

        if not targets:
            raise CommandError(
                "Give at least one symbol or use --all. Example: python manage.py scrape AAPL"
            )

        for symbol, name in targets:
            self.stdout.write(f"Scraping {symbol} ...")
            try:
                result = scrape_ticker(symbol, company_name_hint=name)
            except YahooFinanceError as exc:
                self.stdout.write(self.style.ERROR(f"   FAILED: {exc}"))
                continue
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\nOperation cancelled by user."))
                break
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"   UNEXPECTED ERROR: {exc}"))
                continue

            status_str = str(result["status"]).lower()
            style = self.style.SUCCESS if status_str == "success" else self.style.WARNING
            self.stdout.write(style(f"   {result['status'].upper()} - {result['records']} records saved"))
            
            for note in result["errors"]:
                self.stdout.write(self.style.WARNING(f"     note: {note}"))
