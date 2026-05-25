from __future__ import annotations

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from web.recommendation_engine import persist_recommendations_for_all_users, persist_recommendations_for_user


class Command(BaseCommand):
    help = "Rebuild content-based recommendations for one user or all active users."

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, help="Rebuild recommendations only for this username.")
        parser.add_argument("--limit", type=int, default=10, help="Maximum recommendations per user.")

    def handle(self, *args, **options):
        username = options["username"]
        limit = options["limit"]

        if username:
            user = User.objects.filter(username=username, is_active=True).first()
            if user is None:
                raise CommandError(f"User '{username}' not found.")
            created = persist_recommendations_for_user(user, limit=limit)
            self.stdout.write(self.style.SUCCESS(f"Rebuilt {len(created)} recommendations for {username}."))
            return

        stats = persist_recommendations_for_all_users(limit=limit)
        total = sum(stats.values())
        self.stdout.write(self.style.SUCCESS(f"Rebuilt {total} recommendations for {len(stats)} users."))
        for login, count in stats.items():
            self.stdout.write(f"{login}: {count}")
