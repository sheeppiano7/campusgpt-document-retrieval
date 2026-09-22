import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class UiTests(unittest.TestCase):
    def test_initial_page_and_missing_document_prompt(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.button[0].disabled)
        app.button[1].click().run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertIn("建立索引", app.warning[0].value)

    def test_provider_selection_reveals_api_fields(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=20)
        app.selectbox[0].select("OpenAI 兼容接口").run(timeout=20)
        labels = [item.label for item in app.text_input]
        self.assertIn("API Key", labels)
        self.assertIn("模型名称", labels)


if __name__ == "__main__":
    unittest.main()
