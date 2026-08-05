import unittest

from japanese_language_core.reading import deinflect


def words(word: str) -> list[str]:
    return {item.word for item in deinflect(word)}


class DeinflectTests(unittest.TestCase):
    def test_polite(self):
        self.assertIn("食べる", words("食べます"))

    def test_polite_past(self):
        self.assertIn("行く", words("行きました"))

    def test_negative(self):
        self.assertIn("書く", words("書かない"))
        self.assertIn("食べる", words("食べない"))

    def test_te_form(self):
        self.assertIn("行く", words("行って"))
        self.assertIn("泳ぐ", words("泳いで"))
        self.assertIn("飲む", words("飲んで"))

    def test_past(self):
        self.assertIn("帰る", words("帰った"))
        self.assertIn("高い", words("高かった"))

    def test_adjective_te(self):
        self.assertIn("高い", words("高くて"))

    def test_progressive(self):
        self.assertIn("食べる", words("食べている"))

    def test_causative_potential(self):
        self.assertIn("食べる", words("食べさせられる"))


if __name__ == "__main__":
    unittest.main()
