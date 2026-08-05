import tempfile
import unittest
from pathlib import Path

from japanese_language_core.sentences import SentenceBank


class SentenceBankTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        sentences = self.root / "sentences.tsv"
        links = self.root / "links.tsv"
        sentences.write_text(
            "1\tjpn\t明日は晴れる。\n"
            "2\tjpn\t一緒に歩こう。\n"
            "3\tcmn\t明天会放晴。\n"
            "4\tcmn\t一起走吧。\n",
            encoding="utf-8",
        )
        links.write_text("1\t3\n2\t4\n", encoding="utf-8")
        self.bank = SentenceBank.from_tatoeba(sentences, links)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_lookup(self):
        results = self.bank.lookup("明日")
        self.assertEqual(["1"], [sentence.id for sentence in results])

    def test_translations(self):
        translations = self.bank.translations("1")
        self.assertEqual(["3"], [sentence.id for sentence in translations])
        self.assertEqual("明天会放晴。", translations[0].text)


if __name__ == "__main__":
    unittest.main()
