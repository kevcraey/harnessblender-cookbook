import sys
import re
import argparse
import subprocess
import shutil

def run_markdownlint(filepath):
    """
    Attempts to run 'markdownlint --fix' on the file.
    Returns (success, output)
    """
    if not shutil.which('markdownlint'):
        return False, "markdownlint executable not found"
        
    try:
        # Check if a config file exists in the directory tree? 
        # Usually markdownlint finds it automatically.
        # We run with --fix
        result = subprocess.run(
            ['markdownlint', '--fix', filepath],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, "markdownlint applied fixes successfully"
        else:
            return False, f"markdownlint failed: {result.stderr}"
    except Exception as e:
        return False, str(e)

def python_fix_markdown(text):
    """
    Fallback python implementation for basic fixes.
    """
    lines = text.splitlines()
    new_lines = []
    
    in_code_block = False
    
    for i, line in enumerate(lines):
        # Check code block state
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            
        if not in_code_block:
            # MD009: Trailing spaces
            line = line.rstrip()
            
            # MD018: Add space after hash for headings
            if re.match(r'^#+[^ \n]', line):
                line = re.sub(r'^(#+)([^ \n])', r'\1 \2', line)
            
            # MD004: Standardize list markers to '-'
            if re.match(r'^\s*[\*\+] ', line):
                line = re.sub(r'^(\s*)[\*\+] ', r'\1- ', line)
                
            # MD010: Hard tabs to spaces (assuming 2 spaces)
            line = line.replace('\t', '  ')

        new_lines.append(line)

    text = '\n'.join(new_lines)
    
    # MD031: Fenced code blocks should be surrounded by blank lines
    text = re.sub(r'([^\n])\n```', r'\1\n\n```', text)
    text = re.sub(r'```\n([^\n])', r'```\n\n\1', text)

    return text + '\n'

def main():
    parser = argparse.ArgumentParser(description='Auto-format Markdown file')
    parser.add_argument('file', nargs='?', help='Path to markdown file')
    parser.add_argument('--force-python', action='store_true', help='Force using the python fallback')
    args = parser.parse_args()
    
    content = ""
    
    # If no file is provided, we only support the python version on stdin
    if not args.file:
        content = sys.stdin.read()
        print(python_fix_markdown(content))
        return

    # If file is provided, try markdownlint first (unless forced otherwise)
    if not args.force_python:
        success, msg = run_markdownlint(args.file)
        if success:
            # If successful, markdownlint modified the file in place.
            # We can just read it out if we want to print it, or just exit.
            # The previous script printed to stdout. let's maintain that behavior if possible
            # or just inform user.
            # For consistent piping behavior, we should print the content.
             with open(args.file, 'r') as f:
                print(f.read())
             return
        else:
            # Silently fall back or log? 
            # Given the user asked about using the linter, maybe we should be explicit if it's missing.
            # But for a "fixer" script, fallback is nice.
            pass
            
    # Fallback
    try:
        with open(args.file, 'r') as f:
            content = f.read()
        
        fixed = python_fix_markdown(content)
        print(fixed)
        
    except FileNotFoundError:
        print(f"Error: File {args.file} not found", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
