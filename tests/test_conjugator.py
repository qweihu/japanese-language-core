import unittest

from japanese_language_core.reading import conjugate


class ConjugatorTests(unittest.TestCase):
    def test_ichidan(self):
        forms = conjugate("食べる")
        self.assertEqual("食べます", forms["polite"])
        self.assertEqual("食べない", forms["negative"])
        self.assertEqual("食べて", forms["te"])
        self.assertEqual("食べた", forms["past"])
        self.assertEqual("食べれば", forms["conditional"])

    def test_godan_kaku(self):
        forms = conjugate("書く")
        self.assertEqual("書きます", forms["polite"])
        self.assertEqual("書かない", forms["negative"])
        self.assertEqual("書いて", forms["te"])
        self.assertEqual("書いた", forms["past"])
        self.assertEqual("書けば", forms["conditional"])

    def test_godan_kau(self):
        forms = conjugate("買う")
        self.assertEqual("買います", forms["polite"])
        self.assertEqual("買わない", forms["negative"])
        self.assertEqual("買って", forms["te"])

    def test_godan_force(self):
        forms = conjugate("帰る", kind="godan")
        self.assertEqual("帰ります", forms["polite"])
        self.assertEqual("帰って", forms["te"])

    def test_irregular(self):
        self.assertEqual("します", conjugate("する")["polite"])
        self.assertEqual("来ます", conjugate("来る")["polite"])

    def test_adjective(self):
        forms = conjugate("高い")
        self.assertEqual("高くない", forms["negative"])
        self.assertEqual("高かった", forms["past"])
        self.assertEqual("高ければ", forms["conditional"])
        self.assertEqual("高そう", forms["apparent"])


if __name__ == "__main__":
    unittest.main()
