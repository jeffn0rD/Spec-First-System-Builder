# backend/cli/init.py

"""
Spec-First System Builder - Project Initialization CLI

This module provides the `sfsb-init` command to scaffold new SFSB projects.
"""
##  Customization Example
##  To add a custom step that creates a docs/ directory:
##
##      def custom_hook_register_steps(reg: StepRegistry):
##          @reg.register(order=65, name="create_docs", description="Create documentation directory")
##          def step_create_docs(ctx: InitContext):
##              print_progress("Creating documentation directory...")
##              docs_dir = ctx.project_path / "docs"
##              create_directory(docs_dir, ctx, "Project documentation")
##              
##              index_file = docs_dir / "index.md"
##              create_file(index_file, "# Documentation\n\nTODO: Add docs", ctx)
##

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Tuple
from dataclasses import dataclass, field


# ============================================================================
# Step Registration System
# ============================================================================

@dataclass
class InitStep:
    """Represents a single initialization step."""
    order: int
    name: str
    function: Callable
    description: str = ""


class StepRegistry:
    """Registry for initialization steps with ordering support."""
    
    def __init__(self):
        self._steps: List[InitStep] = []
    
    def register(self, order: int, name: str, description: str = ""):
        """Decorator to register a step function."""
        def decorator(func: Callable) -> Callable:
            step = InitStep(
                order=order,
                name=name,
                function=func,
                description=description
            )
            self._steps.append(step)
            return func
        return decorator
    
    def get_steps(self) -> List[InitStep]:
        """Return all steps sorted by order."""
        return sorted(self._steps, key=lambda s: s.order)


# Global registry instance
registry = StepRegistry()


# ============================================================================
# Context Object
# ============================================================================

@dataclass
class InitContext:
    """Shared context passed to all initialization steps."""
    project_name: str
    project_folder: str
    project_path: Path
    git_init: bool
    verbose: bool = False
    created_items: List[str] = field(default_factory=list)


# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_folder_name(name: str) -> str:
    """Convert project name to filesystem-safe folder name."""
    # Convert to lowercase
    safe_name = name.lower()
    # Replace spaces and special chars with hyphens
    safe_name = re.sub(r'[^\w\s-]', '', safe_name)
    safe_name = re.sub(r'[-\s]+', '-', safe_name)
    # Remove leading/trailing hyphens
    safe_name = safe_name.strip('-')
    return safe_name or "sfsb-project"


def print_progress(message: str, indent: int = 0):
    """Print a progress message with optional indentation."""
    prefix = "  " * indent
    print(f"{prefix}{message}")


def create_directory(path: Path, ctx: InitContext, description: str = ""):
    """Create a directory and log it."""
    path.mkdir(parents=True, exist_ok=False)
    display_path = path.relative_to(ctx.project_path.parent)
    ctx.created_items.append(f"📁 {display_path}/")
    if ctx.verbose and description:
        print_progress(f"✓ Created {display_path}/ - {description}", indent=1)
    else:
        print_progress(f"✓ Created {display_path}/", indent=1)


def create_file(path: Path, content: str, ctx: InitContext, description: str = ""):
    """Create a file with content and log it."""
    path.write_text(content, encoding='utf-8')
    display_path = path.relative_to(ctx.project_path.parent)
    ctx.created_items.append(f"📄 {display_path}")
    if ctx.verbose and description:
        print_progress(f"✓ Created {display_path} - {description}", indent=1)
    else:
        print_progress(f"✓ Created {display_path}", indent=1)


# ============================================================================
# File Content Templates
# ============================================================================

NL_SPEC_TEMPLATE = """# Natural Language Specification v1

## Project

**Name:**  
<!-- Enter project name -->

**Short Description:**  
<!-- 1-3 sentences describing what this project does -->

**Version Hint:**  
<!-- e.g., 0.1.0 (optional) -->

---

## Platforms and Stack

### Targets

<!-- List target platforms/languages. Example:
- Kind: backend
  Language: Python
  Runtime: CPython
  Framework: FastAPI
-->

### Persistence Preferences

<!-- e.g., "Must use PostgreSQL" or "In-memory only" (optional) -->

### LLM Usage Policy

<!-- e.g., "Translation and planning only" (optional) -->

---

## Core Functionality

### Primary Users or Actors

<!-- Who will use this system? -->

### Main Capabilities

<!-- What should the system do? List key features/use cases. -->

### Example Workflows

<!-- Optional: describe typical user flows -->

---

## Constraints and Policies

### Must-Haves

<!-- Hard requirements -->

### Nice-to-Haves

<!-- Optional features -->

### Known Non-Goals

<!-- What this project will NOT do -->

---

## Open Questions and Risks

### Open Questions

<!-- Unresolved design questions -->

### Risks

<!-- Known risks or concerns -->
"""

PHASE1_SYSTEM_PROMPT = """# Phase 1: NLSpec System Prompt

You are assisting a designer in creating a formal Natural Language Specification (NLSpec) for a software project.

Your role:
- Ask targeted questions to fill out the NLSpec template sections.
- Clarify ambiguities in the designer's descriptions.
- Flag potential inconsistencies (e.g., conflicting platform choices or unclear requirements).
- Suggest concrete wording for each section.

The NLSpec must include:
- Project name and short description.
- Target platforms and stack (languages, runtimes, frameworks).
- Core functionality (primary users/actors, main capabilities).
- Optional: constraints, policies, open questions, and risks.

Be concise, professional, and focus on extracting the "core facts" needed for downstream CTO generation.
"""

PHASE1_QUESTIONS = """# Phase 1: Example Questions

Use these as a guide when refining the NLSpec with the designer:

1. What is the primary purpose of this project in one sentence?
2. Who are the main users or actors?
3. What are the top 3-5 capabilities or features this system must provide?
4. What platforms or languages should the generated code target? (e.g., Python backend, TypeScript frontend, etc.)
5. Are there any hard constraints? (e.g., must be offline-capable, must use a specific database, regulatory requirements)
6. Are there any known risks or open design questions?
"""

PHASE_PLACEHOLDER = """# Phase X: [Phase Name] System Prompt

(Placeholder – to be refined in future implementation phases.)
"""

GITIGNORE_CONTENT = """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
env/

# Node
node_modules/
dist/
build/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temp
*.tmp
"""

README_TEMPLATE = """# {project_name}

This project was initialized with the **Spec‑First System Builder**.

## Structure

- `spec/` – Natural language specs, CTO, architecture plans, module/function specs, diagrams.
- `.sfsb/` – Prompts, logs, and internal artifacts.
- `generators/` – Python generator scripts (created in Phase 4).
- `templates/` – Jinja2 templates for code generation.

## Next Steps

1. Run `sfsb-spec nl-init` to start Phase 1 (NLSpec refinement).
2. Follow the conversational prompts to complete your NLSpec.
3. Approve the NLSpec and proceed to CTO generation (Phase 2).

See the main Spec‑First System Builder documentation for details.
"""


# ============================================================================
# Initialization Steps
# ============================================================================

@registry.register(order=10, name="validate", description="Validate inputs and check for conflicts")
def step_validate(ctx: InitContext):
    """Validate project setup and check for existing directory."""
    print_progress(f"Validating project setup...")
    
    if ctx.project_path.exists():
        print(f"\n❌ Error: Directory '{ctx.project_path}' already exists.", file=sys.stderr)
        print(f"   Please choose a different project name or remove the existing directory.", file=sys.stderr)
        sys.exit(1)
    
    print_progress(f"✓ Project name: '{ctx.project_name}'", indent=1)
    print_progress(f"✓ Folder name: '{ctx.project_folder}'", indent=1)
    print_progress(f"✓ Location: {ctx.project_path}", indent=1)


@registry.register(order=20, name="create_root", description="Create project root directory")
def step_create_root(ctx: InitContext):
    """Create the root project directory."""
    print_progress(f"Creating project root...")
    create_directory(ctx.project_path, ctx, "Project root directory")


@registry.register(order=30, name="create_spec", description="Create spec/ directory and files")
def step_create_spec(ctx: InitContext):
    """Create spec directory and initial NLSpec template."""
    print_progress(f"Creating spec directory...")
    
    spec_dir = ctx.project_path / "spec"
    create_directory(spec_dir, ctx, "Specification documents")
    
    nl_spec_file = spec_dir / "nl_spec_v1.md"
    create_file(nl_spec_file, NL_SPEC_TEMPLATE, ctx, "Natural Language Specification template")


@registry.register(order=40, name="create_sfsb", description="Create .sfsb/ directory structure")
def step_create_sfsb(ctx: InitContext):
    """Create .sfsb directory with prompts, logs, and artifacts."""
    print_progress(f"Creating .sfsb directory structure...")
    
    sfsb_dir = ctx.project_path / ".sfsb"
    create_directory(sfsb_dir, ctx, "SFSB internal directory")
    
    # Prompts directory
    prompts_dir = sfsb_dir / "prompts"
    create_directory(prompts_dir, ctx, "LLM prompts for all phases")
    
    # Phase 1: NL Spec
    phase1_dir = prompts_dir / "phase1_nl_spec"
    create_directory(phase1_dir, ctx)
    create_file(phase1_dir / "system.md", PHASE1_SYSTEM_PROMPT, ctx)
    create_file(phase1_dir / "questions.md", PHASE1_QUESTIONS, ctx)
    
    # Phase 2: CTO and Diagrams
    phase2_cto_dir = prompts_dir / "phase2_cto"
    create_directory(phase2_cto_dir, ctx)
    create_file(phase2_cto_dir / "system.md", PHASE_PLACEHOLDER, ctx)
    
    phase2_diagrams_dir = prompts_dir / "phase2_diagrams"
    create_directory(phase2_diagrams_dir, ctx)
    create_file(phase2_diagrams_dir / "system.md", PHASE_PLACEHOLDER, ctx)
    
    # Phase 3: Architecture, Modules, Functions
    phase3_arch_dir = prompts_dir / "phase3_arch_plan"
    create_directory(phase3_arch_dir, ctx)
    create_file(phase3_arch_dir / "system.md", PHASE_PLACEHOLDER, ctx)
    
    phase3_modules_dir = prompts_dir / "phase3_module_specs"
    create_directory(phase3_modules_dir, ctx)
    create_file(phase3_modules_dir / "system.md", PHASE_PLACEHOLDER, ctx)
    
    phase3_functions_dir = prompts_dir / "phase3_function_specs"
    create_directory(phase3_functions_dir, ctx)
    create_file(phase3_functions_dir / "system.md", PHASE_PLACEHOLDER, ctx)
    
    # Phase 4: Generators
    phase4_dir = prompts_dir / "phase4_generators"
    create_directory(phase4_dir, ctx)
    create_file(phase4_dir / "system.md", PHASE_PLACEHOLDER, ctx)
    
    # Logs directory
    logs_dir = sfsb_dir / "logs"
    create_directory(logs_dir, ctx, "Conversation and LLM call logs")
    
    phase1_logs_dir = logs_dir / "phase1_conversations"
    create_directory(phase1_logs_dir, ctx)
    create_file(phase1_logs_dir / ".gitkeep", "", ctx)
    
    llm_logs_dir = logs_dir / "llm_calls"
    create_directory(llm_logs_dir, ctx)
    create_file(llm_logs_dir / ".gitkeep", "", ctx)
    
    # Artifacts directory
    artifacts_dir = sfsb_dir / "artifacts"
    create_directory(artifacts_dir, ctx, "Generated artifacts and intermediate files")
    create_file(artifacts_dir / ".gitkeep", "", ctx)


@registry.register(order=50, name="create_generators", description="Create generators/ directory")
def step_create_generators(ctx: InitContext):
    """Create generators directory for Phase 4."""
    print_progress(f"Creating generators directory...")
    
    generators_dir = ctx.project_path / "generators"
    create_directory(generators_dir, ctx, "Python generator scripts")
    create_file(generators_dir / ".gitkeep", "", ctx)


@registry.register(order=60, name="create_templates", description="Create templates/ directory")
def step_create_templates(ctx: InitContext):
    """Create templates directory for Jinja2 templates."""
    print_progress(f"Creating templates directory...")
    
    templates_dir = ctx.project_path / "templates"
    create_directory(templates_dir, ctx, "Jinja2 code generation templates")
    create_file(templates_dir / ".gitkeep", "", ctx)


@registry.register(order=70, name="create_config_files", description="Create .gitignore and README.md")
def step_create_config_files(ctx: InitContext):
    """Create configuration files (.gitignore, README.md)."""
    print_progress(f"Creating configuration files...")
    
    gitignore_file = ctx.project_path / ".gitignore"
    create_file(gitignore_file, GITIGNORE_CONTENT, ctx, "Git ignore rules")
    
    readme_content = README_TEMPLATE.format(project_name=ctx.project_name)
    readme_file = ctx.project_path / "README.md"
    create_file(readme_file, readme_content, ctx, "Project documentation")


@registry.register(order=80, name="git_init", description="Initialize Git repository (if requested)")
def step_git_init(ctx: InitContext):
    """Initialize Git repository and create initial commit."""
    if not ctx.git_init:
        return
    
    print_progress(f"Initializing Git repository...")
    
    try:
        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=ctx.project_path,
            check=True,
            capture_output=True,
            text=True
        )
        print_progress(f"✓ Git repository initialized", indent=1)
        
        # Add all files
        subprocess.run(
            ["git", "add", "."],
            cwd=ctx.project_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create initial commit
        subprocess.run(
            ["git", "commit", "-m", "Initial project structure via sfsb-init"],
            cwd=ctx.project_path,
            check=True,
            capture_output=True,
            text=True
        )
        print_progress(f"✓ Initial commit created", indent=1)
        
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️  Warning: Git initialization failed: {e}", file=sys.stderr)
        print(f"   You can manually initialize git later with: cd {ctx.project_folder} && git init", file=sys.stderr)
    except FileNotFoundError:
        print(f"\n⚠️  Warning: Git not found in PATH", file=sys.stderr)
        print(f"   Install git to enable version control.", file=sys.stderr)


# ============================================================================
# Custom Hook System
# ============================================================================

def custom_hook_before_step(step: InitStep, ctx: InitContext):
    """
    Custom hook called BEFORE each step executes.
    
    Use this to add custom logic before specific steps.
    
    Example:
        if step.name == "create_spec":
            # Do something before creating spec directory
            print("About to create spec directory!")
    
    Args:
        step: The step about to be executed
        ctx: The initialization context
    """
    # Add your custom pre-step logic here
    pass


def custom_hook_after_step(step: InitStep, ctx: InitContext):
    """
    Custom hook called AFTER each step executes.
    
    Use this to add custom logic after specific steps.
    
    Example:
        if step.name == "create_sfsb":
            # Add custom files to .sfsb directory
            custom_file = ctx.project_path / ".sfsb" / "custom.txt"
            create_file(custom_file, "Custom content", ctx)
    
    Args:
        step: The step that was just executed
        ctx: The initialization context
    """
    # Add your custom post-step logic here
    pass


def custom_hook_register_steps(reg: StepRegistry):
    """
    Custom hook to register additional initialization steps.
    
    Use this to add completely new steps to the initialization process.
    
    Example:
        @reg.register(order=75, name="create_custom", description="Create custom files")
        def step_create_custom(ctx: InitContext):
            print_progress("Creating custom files...")
            custom_dir = ctx.project_path / "custom"
            create_directory(custom_dir, ctx, "Custom directory")
    
    Args:
        reg: The step registry to add steps to
    """
    # Add your custom step registrations here
    pass


# ============================================================================
# Main Execution Logic
# ============================================================================

def execute_initialization(ctx: InitContext):
    """Execute all registered initialization steps in order."""
    steps = registry.get_steps()
    
    print(f"\n🚀 Initializing project '{ctx.project_name}'...")
    print(f"   Location: {ctx.project_path}\n")
    
    for step in steps:
        try:
            # Call custom pre-step hook
            custom_hook_before_step(step, ctx)
            
            # Execute the step
            step.function(ctx)
            
            # Call custom post-step hook
            custom_hook_after_step(step, ctx)
            
        except Exception as e:
            print(f"\n❌ Error during step '{step.name}': {e}", file=sys.stderr)
            print(f"   Initialization failed. You may need to manually clean up {ctx.project_path}", file=sys.stderr)
            sys.exit(1)
    
    # Success message
    print(f"\n✓ Project '{ctx.project_name}' initialized successfully.")
    print(f"✓ Next: cd {ctx.project_folder} && sfsb-spec nl-init\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sfsb-init",
        description="Initialize a new Spec-First System Builder project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sfsb-init 'My Project'                    # Create project in ./my-project/
  sfsb-init -g 'My Project'                 # Create with git init
  sfsb-init -f /path/to/projects 'My App'   # Create in specific location
  sfsb-init -g -f ~/projects 'My App'       # Combine options
        """
    )
    
    parser.add_argument(
        "project_name",
        help="Name of the project (will be sanitized for folder name)"
    )
    
    parser.add_argument(
        "-g", "--git",
        action="store_true",
        help="Initialize a git repository and create initial commit"
    )
    
    parser.add_argument(
        "-f", "--folder",
        type=str,
        default=".",
        help="Parent folder path where project will be created (default: current directory)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with detailed descriptions"
    )
    
    args = parser.parse_args()
    
    # Prepare context
    project_folder = sanitize_folder_name(args.project_name)
    parent_path = Path(args.folder).resolve()
    
    if not parent_path.exists():
        print(f"❌ Error: Parent folder '{parent_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    if not parent_path.is_dir():
        print(f"❌ Error: '{parent_path}' is not a directory.", file=sys.stderr)
        sys.exit(1)
    
    project_path = parent_path / project_folder
    
    ctx = InitContext(
        project_name=args.project_name,
        project_folder=project_folder,
        project_path=project_path,
        git_init=args.git,
        verbose=args.verbose
    )
    
    # Allow custom step registration
    custom_hook_register_steps(registry)
    
    # Execute initialization
    execute_initialization(ctx)


if __name__ == "__main__":
    main()

