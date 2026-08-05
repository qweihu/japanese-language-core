import unittest

from japanese_language_core.grammar import find_grammar, find_particles


class GrammarTests(unittest.TestCase):
    def test_particles(self):
        matches = find_particles("私は東京へ行きます。")
        particles = [match.particle for match in matches]
        self.assertIn("は", particles)
        self.assertIn("へ", particles)

    def test_patterns(self):
        matches = find_grammar("食べているところです。")
        self.assertTrue(any(match.name == "te-iru" for match in matches))
        matches = find_grammar("行かなければならない。")
        self.assertTrue(any(match.name == "obligation" for match in matches))


if __name__ == "__main__":
    unittest.main()
