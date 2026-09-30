import unittest
from unittest.mock import AsyncMock

from github_stats import Stats


def profile(name="Jon Fairbanks", login="jonfairbanks", more=False):
    return {"data": {"viewer": {
        "name": name,
        "login": login,
        "repositories": {
            "nodes": [],
            "pageInfo": {"hasNextPage": more, "endCursor": "next"},
        },
    }}}


class ProfileNameTests(unittest.IsolatedAsyncioTestCase):
    def stats(self, *responses):
        stats = Stats("jonfairbanks", "unused", None)
        stats.queries.query = AsyncMock(side_effect=responses)
        return stats

    async def test_display_name(self):
        stats = self.stats(profile())
        await stats.get_stats()
        self.assertEqual(await stats.name, "Jon Fairbanks")

    async def test_missing_name_uses_login(self):
        stats = self.stats(profile(name=None))
        await stats.get_stats()
        self.assertEqual(await stats.name, "jonfairbanks")

    async def test_missing_identity_uses_configured_username(self):
        stats = self.stats(profile(name="", login=None))
        await stats.get_stats()
        self.assertEqual(await stats.name, "jonfairbanks")

    async def test_later_page_cannot_replace_display_name(self):
        stats = self.stats(profile(more=True), profile(name=None))
        await stats.get_stats()
        self.assertEqual(await stats.name, "Jon Fairbanks")

    async def test_failed_later_page_stops_generation(self):
        for failure in ({}, {"data": None}, {"errors": [{"message": "Unavailable"}]}):
            with self.subTest(failure=failure):
                stats = self.stats(profile(more=True), failure)
                with self.assertRaisesRegex(RuntimeError, "incomplete profile statistics"):
                    await stats.get_stats()
                self.assertEqual(await stats.name, "Jon Fairbanks")

    async def test_failed_first_page_stops_generation(self):
        stats = self.stats({"data": None})
        with self.assertRaises(RuntimeError):
            await stats.get_stats()
        self.assertIsNone(stats._name)
