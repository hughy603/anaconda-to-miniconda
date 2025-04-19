"""Tests for the CLI performance improvements."""

from unittest import mock

from conda_forge_converter.cli import main


class TestCLIPerformanceOptions:
    """Tests for CLI performance options."""

    @mock.patch("conda_forge_converter.cli.convert_environment")
    @mock.patch("conda_forge_converter.cli.list_all_conda_environments")
    def test_fast_solver_option(
        self, mock_list_envs: mock.MagicMock, mock_convert: mock.MagicMock
    ) -> None:
        """Test that the fast solver option is properly passed to convert_environment."""
        # Setup
        mock_list_envs.return_value = {"myenv": "/path/to/myenv"}
        mock_convert.return_value = True

        # Execute with fast solver enabled (default)
        main(["--source-env", "myenv", "--target-env", "myenv_forge"])

        # Verify
        mock_convert.assert_called_once()
        args, kwargs = mock_convert.call_args
        assert kwargs.get("use_fast_solver") is True

        # Reset mocks
        mock_convert.reset_mock()

        # Execute with fast solver disabled
        main(["--source-env", "myenv", "--target-env", "myenv_forge", "--no-fast-solver"])

        # Verify
        mock_convert.assert_called_once()
        args, kwargs = mock_convert.call_args
        assert kwargs.get("use_fast_solver") is False

    @mock.patch("conda_forge_converter.cli.convert_environment")
    @mock.patch("conda_forge_converter.cli.list_all_conda_environments")
    def test_batch_size_option(
        self, mock_list_envs: mock.MagicMock, mock_convert: mock.MagicMock
    ) -> None:
        """Test that the batch size option is properly passed to convert_environment."""
        # Setup
        mock_list_envs.return_value = {"myenv": "/path/to/myenv"}
        mock_convert.return_value = True

        # Execute with default batch size
        main(["--source-env", "myenv", "--target-env", "myenv_forge"])

        # Verify
        mock_convert.assert_called_once()
        args, kwargs = mock_convert.call_args
        assert kwargs.get("batch_size") == 20  # Default value

        # Reset mocks
        mock_convert.reset_mock()

        # Execute with custom batch size
        main(["--source-env", "myenv", "--target-env", "myenv_forge", "--batch-size", "30"])

        # Verify
        mock_convert.assert_called_once()
        args, kwargs = mock_convert.call_args
        assert kwargs.get("batch_size") == 30

    @mock.patch("conda_forge_converter.cli.convert_multiple_environments")
    def test_batch_conversion_options(self, mock_convert_multiple: mock.MagicMock) -> None:
        """Test that performance options are properly passed to convert_multiple_environments."""
        # Setup
        mock_convert_multiple.return_value = True

        # Execute with custom options
        main(
            [
                "--batch",
                "--pattern",
                "data*",
                "--batch-size",
                "15",
                "--no-fast-solver",
                "--max-parallel",
                "4",
            ]
        )

        # Verify
        mock_convert_multiple.assert_called_once()
        args, kwargs = mock_convert_multiple.call_args
        assert kwargs.get("batch_size") == 15
        assert kwargs.get("use_fast_solver") is False
        assert kwargs.get("max_parallel") == 4
        assert kwargs.get("env_pattern") == "data*"
