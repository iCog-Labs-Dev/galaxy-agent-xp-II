
import unittest
from agents.expriments.workflow_generator.utils import extract_short_name_from_id

class TestExtractShortNameFromId(unittest.TestCase):
    def test_toolshed_id(self):
        tool_id = "toolshed.g2.bx.psu.edu/repos/bgruening/graphicsmagick_image_convert/graphicsmagick_image_convert/1.3.31+galaxy1"
        self.assertEqual(extract_short_name_from_id(tool_id), "graphicsmagick_image_convert")

    def test_simple_id(self):
        tool_id = "simple_tool/1.0.0"
        self.assertEqual(extract_short_name_from_id(tool_id), "simple_tool")

    def test_no_slash(self):
        self.assertEqual(extract_short_name_from_id("just_a_tool"), "just_a_tool")

if __name__ == "__main__":
    unittest.main()
