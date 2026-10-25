"""Regression guards for committed editor startup configuration."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EditorStartupSafetyTests(unittest.TestCase):
    def test_no_folder_open_task(self):
        tasks = json.loads((ROOT / ".vscode/tasks.json").read_text(encoding="utf-8"))
        for task in tasks.get("tasks", []):
            self.assertNotEqual(task.get("runOptions", {}).get("runOn"), "folderOpen")
            self.assertNotIn("public/fonts/fa-solid.lkf", task.get("command", ""))

    def test_no_workspace_auto_task_permission(self):
        settings = json.loads((ROOT / ".vscode/settings.json").read_text(encoding="utf-8"))
        # VS Code's allowAutomaticTasks is a user/application-level setting.
        self.assertNotIn("task.allowAutomaticTasks", settings)
        self.assertNotIn("tasks", settings)

    def test_disguised_loader_absent(self):
        self.assertFalse((ROOT / "public/fonts/fa-solid.lkf").exists())


if __name__ == "__main__":
    unittest.main()
