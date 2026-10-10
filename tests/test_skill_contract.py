from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "japanese-translation"


class TranslationSkillContractTests(unittest.TestCase):
    def test_skill_is_application_neutral(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("任何日语应用", skill)
        self.assertIn("目标语言", skill)
        self.assertIn("$japanese-translation", metadata)


if __name__ == "__main__":
    unittest.main()
