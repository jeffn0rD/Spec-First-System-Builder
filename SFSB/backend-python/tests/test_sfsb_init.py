# tests/test_sfsb_init.py

import sys
import tempfile
from pathlib import Path

import pytest

from sfsb.cli.init import main as sfsb_init_main


def run_cli(args, cwd: Path | None = None):
    """
    Helper to run the CLI by patching sys.argv and capturing exit codes.
    """
    old_argv = sys.argv
    old_cwd = Path.cwd()
    try:
        sys.argv = ["sfsb-init", *args]
        if cwd is not None:
            # Change current working directory for the duration of the call
            import os
            os.chdir(cwd)
        sfsb_init_main()
        return 0
    except SystemExit as e:
        # argparse and our error conditions may call sys.exit()
        return e.code
    finally:
        sys.argv = old_argv
        if cwd is not None:
            import os
            os.chdir(old_cwd)


def test_sfsb_init_creates_project_structure():
    """
    Verify that running `sfsb-init` creates the expected folder structure and files.
    """
    project_name = "My Test Project"
    safe_name = "my-test-project"  # expected sanitized folder name

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Run CLI with: sfsb-init -f <tmpdir> "<project_name>"
        exit_code = run_cli(["-f", str(tmp_path), project_name])
        assert exit_code == 0

        project_path = tmp_path / safe_name
        assert project_path.exists() and project_path.is_dir()

        # --- Check core directories ---
        assert (project_path / "spec").is_dir()
        assert (project_path / ".sfsb").is_dir()
        assert (project_path / "generators").is_dir()
        assert (project_path / "templates").is_dir()

        # .sfsb substructure
        prompts_dir = project_path / ".sfsb" / "prompts"
        logs_dir = project_path / ".sfsb" / "logs"
        artifacts_dir = project_path / ".sfsb" / "artifacts"

        assert prompts_dir.is_dir()
        assert logs_dir.is_dir()
        assert artifacts_dir.is_dir()

        # Check phase prompt directories
        for sub in [
            "phase1_nl_spec",
            "phase2_cto",
            "phase2_diagrams",
            "phase3_arch_plan",
            "phase3_module_specs",
            "phase3_function_specs",
            "phase4_generators",
        ]:
            assert (prompts_dir / sub).is_dir()

        # --- Check key files ---
        nl_spec = project_path / "spec" / "nl_spec_v1.md"
        assert nl_spec.is_file()
        nl_text = nl_spec.read_text(encoding="utf-8")
        assert "# Natural Language Specification v1" in nl_text

        gitignore = project_path / ".gitignore"
        assert gitignore.is_file()
        gi_text = gitignore.read_text(encoding="utf-8")
        assert "__pycache__/" in gi_text

        readme = project_path / "README.md"
        assert readme.is_file()
        readme_text = readme.read_text(encoding="utf-8")
        # README should contain the project name and SFSB reference
        assert project_name in readme_text
        assert "Spec‑First System Builder" in readme_text

        # .sfsb logs and artifacts gitkeeps
        assert (logs_dir / "phase1_conversations" / ".gitkeep").is_file()
        assert (logs_dir / "llm_calls" / ".gitkeep").is_file()
        assert (artifacts_dir / ".gitkeep").is_file()

        # Generators/templates gitkeep
        assert (project_path / "generators" / ".gitkeep").is_file()
        assert (project_path / "templates" / ".gitkeep").is_file()


def test_sfsb_init_fails_if_directory_exists():
    """
    Verify that sfsb-init fails gracefully if the project directory already exists.
    """
    project_name = "Existing Project"
    safe_name = "existing-project"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        project_path = tmp_path / safe_name

        # Manually create the directory to simulate existing project
        project_path.mkdir()

        # Expect non-zero exit code (due to sys.exit(1))
        exit_code = run_cli(["-f", str(tmp_path), project_name])
        assert exit_code != 0
        # Directory should still exist but not be modified/removed
        assert project_path.exists() and project_path.is_dir()
