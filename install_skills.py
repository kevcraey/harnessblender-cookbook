#!/usr/bin/env python3
"""
Skill installer for Claude Code - creates symbolic links to skills in target projects.

Usage:
    python3 install_skills.py ~/path/to/project
    python3 install_skills.py ~/path/to/project --all
    python3 install_skills.py ~/path/to/project skill1 skill2 skill3
"""

import os
import sys
from pathlib import Path
from typing import List, Set


class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def find_skills(repo_path: Path) -> List[dict]:
    """Find all valid skills in the repository."""
    skills = []

    for item in repo_path.iterdir():
        if not item.is_dir():
            continue

        # Skip hidden directories and special directories
        if item.name.startswith('.') or item.name in ['docs', '__pycache__', 'venv']:
            continue

        # Check if it contains a skill definition file
        skill_file = None
        if (item / 'skill.md').exists():
            skill_file = item / 'skill.md'
        elif (item / 'SKILL.md').exists():
            skill_file = item / 'SKILL.md'

        if skill_file:
            # Try to extract skill name from file
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Read first 500 chars
                    # Look for name in frontmatter or first line
                    display_name = item.name
                    for line in content.split('\n')[:10]:
                        if line.startswith('name:'):
                            display_name = line.split('name:', 1)[1].strip()
                            break
            except Exception:
                display_name = item.name

            skills.append({
                'dir_name': item.name,
                'display_name': display_name,
                'path': item,
                'skill_file': skill_file
            })

    return sorted(skills, key=lambda x: x['dir_name'])


def select_skills_interactive(skills: List[dict]) -> List[dict]:
    """Interactive skill selection using numbered list."""
    print(f"\n{Colors.BOLD}Available Skills:{Colors.END}")
    print(f"{Colors.BLUE}{'─' * 60}{Colors.END}\n")

    for idx, skill in enumerate(skills, 1):
        print(f"  {Colors.BOLD}{idx:2d}.{Colors.END} {skill['display_name']}")
        if skill['display_name'] != skill['dir_name']:
            print(f"      {Colors.YELLOW}({skill['dir_name']}){Colors.END}")

    print(f"\n{Colors.BLUE}{'─' * 60}{Colors.END}")
    print(f"\n{Colors.BOLD}Selection options:{Colors.END}")
    print(f"  • Enter numbers (comma or space separated): {Colors.GREEN}1,3,5{Colors.END} or {Colors.GREEN}1 3 5{Colors.END}")
    print(f"  • Enter ranges: {Colors.GREEN}1-5{Colors.END} or {Colors.GREEN}1-3,7,9-11{Colors.END}")
    print(f"  • Type {Colors.GREEN}all{Colors.END} to install all skills")
    print(f"  • Press Enter to cancel\n")

    while True:
        selection = input(f"{Colors.BOLD}Select skills:{Colors.END} ").strip()

        if not selection:
            return []

        if selection.lower() == 'all':
            return skills

        # Parse selection
        try:
            indices = parse_selection(selection, len(skills))
            if indices:
                return [skills[i] for i in indices]
            else:
                print(f"{Colors.RED}Invalid selection. Please try again.{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}Error parsing selection: {e}{Colors.END}")


def parse_selection(selection: str, max_num: int) -> Set[int]:
    """Parse user selection into a set of indices."""
    indices = set()

    # Replace commas with spaces and split
    parts = selection.replace(',', ' ').split()

    for part in parts:
        if '-' in part:
            # Handle range
            try:
                start, end = part.split('-', 1)
                start_idx = int(start.strip()) - 1
                end_idx = int(end.strip()) - 1

                if 0 <= start_idx < max_num and 0 <= end_idx < max_num:
                    indices.update(range(start_idx, end_idx + 1))
                else:
                    raise ValueError(f"Range {part} out of bounds")
            except ValueError as e:
                raise ValueError(f"Invalid range: {part}")
        else:
            # Handle single number
            try:
                idx = int(part.strip()) - 1
                if 0 <= idx < max_num:
                    indices.add(idx)
                else:
                    raise ValueError(f"Number {part} out of bounds")
            except ValueError:
                raise ValueError(f"Invalid number: {part}")

    return indices


def install_skills(skills: List[dict], target_path: Path, repo_path: Path) -> None:
    """Create symbolic links for selected skills in target project."""
    skills_dir = target_path / '.claude' / 'skills'

    # Create .claude/skills directory if it doesn't exist
    skills_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{Colors.BOLD}Installing skills to:{Colors.END} {skills_dir}\n")

    installed = []
    skipped = []
    errors = []

    for skill in skills:
        link_path = skills_dir / skill['dir_name']
        source_path = skill['path'].resolve()

        try:
            if link_path.exists() or link_path.is_symlink():
                # Check if it's already pointing to the right place
                if link_path.is_symlink() and link_path.resolve() == source_path:
                    print(f"  {Colors.YELLOW}⊙{Colors.END} {skill['dir_name']} (already installed)")
                    skipped.append(skill['dir_name'])
                else:
                    print(f"  {Colors.YELLOW}⊙{Colors.END} {skill['dir_name']} (exists, skipping)")
                    skipped.append(skill['dir_name'])
            else:
                # Create symlink
                link_path.symlink_to(source_path)
                print(f"  {Colors.GREEN}✓{Colors.END} {skill['dir_name']}")
                installed.append(skill['dir_name'])
        except Exception as e:
            print(f"  {Colors.RED}✗{Colors.END} {skill['dir_name']} (error: {e})")
            errors.append(skill['dir_name'])

    # Summary
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    if installed:
        print(f"  {Colors.GREEN}✓ Installed: {len(installed)}{Colors.END}")
    if skipped:
        print(f"  {Colors.YELLOW}⊙ Skipped: {len(skipped)}{Colors.END}")
    if errors:
        print(f"  {Colors.RED}✗ Errors: {len(errors)}{Colors.END}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Error: Missing target directory{Colors.END}")
        print(f"\nUsage:")
        print(f"  {sys.argv[0]} <target-directory> [--all | skill1 skill2 ...]")
        print(f"\nExamples:")
        print(f"  {sys.argv[0]} ~/projects/myapp")
        print(f"  {sys.argv[0]} ~/projects/myapp --all")
        print(f"  {sys.argv[0]} ~/projects/myapp humanizer sb-daily-briefing")
        sys.exit(1)

    # Get paths
    repo_path = Path(__file__).parent.resolve()
    target_path = Path(sys.argv[1]).expanduser().resolve()

    # Validate target directory
    if not target_path.exists():
        print(f"{Colors.RED}Error: Target directory does not exist: {target_path}{Colors.END}")
        sys.exit(1)

    if not target_path.is_dir():
        print(f"{Colors.RED}Error: Target is not a directory: {target_path}{Colors.END}")
        sys.exit(1)

    # Find available skills
    all_skills = find_skills(repo_path)

    if not all_skills:
        print(f"{Colors.RED}Error: No skills found in repository{Colors.END}")
        sys.exit(1)

    print(f"{Colors.BOLD}Skill Repository:{Colors.END} {repo_path}")
    print(f"{Colors.BOLD}Target Project:{Colors.END} {target_path}")
    print(f"{Colors.BOLD}Found Skills:{Colors.END} {len(all_skills)}")

    # Determine which skills to install
    if len(sys.argv) > 2:
        if sys.argv[2] == '--all':
            # Install all skills
            selected_skills = all_skills
        else:
            # Install specific skills by name
            requested_names = set(sys.argv[2:])
            selected_skills = [s for s in all_skills if s['dir_name'] in requested_names]

            # Check for unknown skills
            found_names = {s['dir_name'] for s in selected_skills}
            unknown = requested_names - found_names
            if unknown:
                print(f"\n{Colors.YELLOW}Warning: Unknown skills: {', '.join(unknown)}{Colors.END}")

            if not selected_skills:
                print(f"{Colors.RED}Error: No valid skills specified{Colors.END}")
                sys.exit(1)
    else:
        # Interactive selection
        selected_skills = select_skills_interactive(all_skills)

        if not selected_skills:
            print(f"\n{Colors.YELLOW}No skills selected. Exiting.{Colors.END}")
            sys.exit(0)

    # Install selected skills
    install_skills(selected_skills, target_path, repo_path)
    print(f"\n{Colors.GREEN}Done!{Colors.END}\n")


if __name__ == '__main__':
    main()
