"""Regression guards for committed editor startup configuration."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def config_has_implicit_execution(config):
    """Flag implicit folder-open execution or the known loader reference."""
    if isinstance(config, dict):
        if config.get("runOn") == "folderOpen":
            return True
        return any(config_has_implicit_execution(value) for value in config.values())
    if isinstance(config, list):
        return any(config_has_implicit_execution(value) for value in config)
    if isinstance(config, str):
        return "public/fonts/fa-solid.lkf" in config.casefold()
    return False


class EditorStartupSafetyTests(unittest.TestCase):
    def test_no_folder_open_task(self):
        tasks = json.loads((ROOT / ".vscode/tasks.json").read_text(encoding="utf-8"))
        self.assertFalse(config_has_implicit_execution(tasks))

    def test_os_specific_folder_open_is_rejected(self):
        sample = {"tasks": [{"windows": {"runOptions": {"runOn": "folderOpen"}}}]}
        self.assertTrue(config_has_implicit_execution(sample))

    def test_nested_args_loader_is_rejected(self):
        sample = {"tasks": [{"linux": {"args": ["./public/fonts/fa-solid.lkf"]}}]}
        self.assertTrue(config_has_implicit_execution(sample))

    def test_no_workspace_auto_task_permission(self):
        settings = json.loads((ROOT / ".vscode/settings.json").read_text(encoding="utf-8"))
        # VS Code's allowAutomaticTasks is a user/application-level setting.
        self.assertNotIn("task.allowAutomaticTasks", settings)
        self.assertNotIn("tasks", settings)

    def test_disguised_loader_absent(self):
        self.assertFalse((ROOT / "public/fonts/fa-solid.lkf").exists())


if __name__ == "__main__":
    unittest.main()
