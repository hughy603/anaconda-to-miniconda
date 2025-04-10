"""Tests for the VSCode setup script."""

import json
import os
import shutil

# Import the setup_vscode module
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, mock

sys.path.append(str(Path(__file__).parent.parent / "scripts"))
import setup_vscode


class TestVSCodeSetup(TestCase):
    """Test the VSCode setup script."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.vscode_dir = Path(self.test_dir) / ".vscode"

        # Mock get_project_root to return our test directory
        self.patcher = mock.patch.object(
            setup_vscode, "get_project_root", return_value=Path(self.test_dir)
        )
        self.mock_get_project_root = self.patcher.start()

        # Mock print_colored to avoid terminal output during tests
        self.print_patcher = mock.patch.object(setup_vscode, "print_colored")
        self.mock_print_colored = self.print_patcher.start()

    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patchers
        self.patcher.stop()
        self.print_patcher.stop()

        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_create_vscode_directory(self):
        """Test creating the .vscode directory."""
        # Call the function
        result = setup_vscode.create_vscode_directory()

        # Check that the directory was created
        self.assertTrue(self.vscode_dir.exists())
        self.assertTrue(self.vscode_dir.is_dir())

        # Check that the function returned the correct path
        self.assertEqual(result, self.vscode_dir)

    def test_create_launch_json(self):
        """Test creating the launch.json file."""
        # Create the .vscode directory
        self.vscode_dir.mkdir(exist_ok=True)

        # Call the function
        setup_vscode.create_launch_json(self.vscode_dir)

        # Check that the file was created
        launch_json_path = self.vscode_dir / "launch.json"
        self.assertTrue(launch_json_path.exists())

        # Check that the file contains valid JSON
        with launch_json_path.open() as f:
            launch_config = json.load(f)

        # Check that the configuration has the expected structure
        self.assertIn("version", launch_config)
        self.assertIn("configurations", launch_config)
        self.assertIsInstance(launch_config["configurations"], list)

        # Check that the configurations include the expected debug configurations
        config_names = [config["name"] for config in launch_config["configurations"]]
        self.assertIn("Debug CLI", config_names)
        self.assertIn("Debug Conda Integration", config_names)
        self.assertIn("Debug Mamba Integration", config_names)
        self.assertIn("Debug Tests", config_names)

    def test_create_settings_json(self):
        """Test creating the settings.json file."""
        # Create the .vscode directory
        self.vscode_dir.mkdir(exist_ok=True)

        # Call the function
        setup_vscode.create_settings_json(self.vscode_dir, "/path/to/python")

        # Check that the file was created
        settings_json_path = self.vscode_dir / "settings.json"
        self.assertTrue(settings_json_path.exists())

        # Check that the file contains valid JSON
        with settings_json_path.open() as f:
            settings_config = json.load(f)

        # Check that the configuration has the expected structure
        self.assertIn("python.defaultInterpreterPath", settings_config)
        self.assertEqual(settings_config["python.defaultInterpreterPath"], "/path/to/python")

    def test_create_tasks_json(self):
        """Test creating the tasks.json file."""
        # Create the .vscode directory
        self.vscode_dir.mkdir(exist_ok=True)

        # Call the function
        setup_vscode.create_tasks_json(self.vscode_dir, {"conda": True, "mamba": True})

        # Check that the file was created
        tasks_json_path = self.vscode_dir / "tasks.json"
        self.assertTrue(tasks_json_path.exists())

        # Check that the file contains valid JSON
        with tasks_json_path.open() as f:
            tasks_config = json.load(f)

        # Check that the configuration has the expected structure
        self.assertIn("version", tasks_config)
        self.assertIn("tasks", tasks_config)
        self.assertIsInstance(tasks_config["tasks"], list)

        # Check that the tasks include conda and mamba tasks
        task_labels = [task["label"] for task in tasks_config["tasks"]]
        self.assertIn("Check Conda Environment", task_labels)
        self.assertIn("Check Mamba Installation", task_labels)

    def test_create_extensions_json(self):
        """Test creating the extensions.json file."""
        # Create the .vscode directory
        self.vscode_dir.mkdir(exist_ok=True)

        # Call the function
        setup_vscode.create_extensions_json(self.vscode_dir)

        # Check that the file was created
        extensions_json_path = self.vscode_dir / "extensions.json"
        self.assertTrue(extensions_json_path.exists())

        # Check that the file contains valid JSON
        with extensions_json_path.open() as f:
            extensions_config = json.load(f)

        # Check that the configuration has the expected structure
        self.assertIn("recommendations", extensions_config)
        self.assertIsInstance(extensions_config["recommendations"], list)

        # Check that the recommendations include essential extensions
        self.assertIn("ms-python.python", extensions_config["recommendations"])
        self.assertIn("ms-python.vscode-pylance", extensions_config["recommendations"])
        self.assertIn("charliermarsh.ruff", extensions_config["recommendations"])

    def test_check_python_interpreter(self):
        """Test checking for Python interpreter."""
        # Mock subprocess.run to simulate conda info output
        with mock.patch("subprocess.run") as mock_run:
            # Configure the mock to return a successful result with conda info
            mock_run.return_value.stdout = json.dumps({"active_env_path": self.test_dir})
            mock_run.return_value.returncode = 0

            # Create a fake Python executable
            python_path = Path(self.test_dir) / "bin" / "python"
            os.makedirs(os.path.dirname(python_path), exist_ok=True)
            with open(python_path, "w") as f:
                f.write("#!/bin/bash\necho 'Python 3.11'")
            os.chmod(python_path, 0o755)

            # Call the function
            result = setup_vscode.check_python_interpreter()

            # Check that the function returned the correct path
            self.assertEqual(result, str(python_path))

    def test_check_conda_installation(self):
        """Test checking for conda and mamba installations."""
        # Mock subprocess.run to simulate conda and mamba being installed
        with mock.patch("subprocess.run") as mock_run:
            # Configure the mock to return success for conda and mamba
            mock_run.return_value.returncode = 0

            # Call the function
            result = setup_vscode.check_conda_installation()

            # Check that the function detected conda and mamba
            self.assertTrue(result["conda"])
            self.assertTrue(result["mamba"])

        # Mock subprocess.run to simulate only conda being installed
        with mock.patch("subprocess.run") as mock_run:
            # Configure the mock to return success for conda but failure for mamba
            def side_effect(cmd, **kwargs):
                if cmd[0] == "conda":
                    return mock.MagicMock(returncode=0)
                else:
                    raise FileNotFoundError("mamba not found")

            mock_run.side_effect = side_effect

            # Call the function
            result = setup_vscode.check_conda_installation()

            # Check that the function detected conda but not mamba
            self.assertTrue(result["conda"])
            self.assertFalse(result["mamba"])

    def test_main(self):
        """Test the main function."""
        # Mock all the functions called by main
        with mock.patch.multiple(
            setup_vscode,
            check_python_interpreter=mock.DEFAULT,
            check_conda_installation=mock.DEFAULT,
            create_vscode_directory=mock.DEFAULT,
            create_launch_json=mock.DEFAULT,
            create_settings_json=mock.DEFAULT,
            create_tasks_json=mock.DEFAULT,
            create_extensions_json=mock.DEFAULT,
            create_readme=mock.DEFAULT,
        ) as mocks:
            # Configure the mocks
            mocks["check_python_interpreter"].return_value = "/path/to/python"
            mocks["check_conda_installation"].return_value = {"conda": True, "mamba": True}
            mocks["create_vscode_directory"].return_value = self.vscode_dir

            # Call the main function
            setup_vscode.main()

            # Check that all the functions were called
            mocks["check_python_interpreter"].assert_called_once()
            mocks["check_conda_installation"].assert_called_once()
            mocks["create_vscode_directory"].assert_called_once()
            mocks["create_launch_json"].assert_called_once_with(self.vscode_dir)
            mocks["create_settings_json"].assert_called_once_with(
                self.vscode_dir, "/path/to/python"
            )
            mocks["create_tasks_json"].assert_called_once_with(
                self.vscode_dir, {"conda": True, "mamba": True}
            )
            mocks["create_extensions_json"].assert_called_once_with(self.vscode_dir)
            mocks["create_readme"].assert_called_once_with(self.vscode_dir)
