import sys
import re
import argparse

def convert_md_to_jira(text):
    # --- 1. Protect Code Blocks ---
    # we replace code blocks with a placeholder to avoid formatting inside them
    code_blocks = {}
    
    def code_block_sub(match):
        key = f"___CODE_BLOCK_{len(code_blocks)}___"
        # Jira code block format: {code:language}\n...\n{code} or {code}\n...\n{code}
        # Markdown: ```language\n...\n```
        lang = match.group(1) or ""
        content = match.group(2)
        
        jira_block = f"{{code:{lang}}}\n{content.strip()}\n{{code}}" if lang else f"{{code}}\n{content.strip()}\n{{code}}"
        code_blocks[key] = jira_block
        return key

    # Match ```lang\ncontent``` 
    text = re.sub(r'```(\w+)?\n?(.*?)\n?```', code_block_sub, text, flags=re.DOTALL)

    # --- 2. Process Line by Line ---
    lines = text.split('\n')
    new_lines = []
    
    # State for tables
    in_table = False
    table_header_buffer = None
    
    for i, line in enumerate(lines):
        # Skip placeholder lines (optimization)
        if line.strip() in code_blocks:
            new_lines.append(line)
            continue
            
        stripped = line.strip()
        
        # --- Tables ---
        # rudimentary table detection
        if stripped.startswith('|') and stripped.endswith('|'):
            # It's a table row
            # Regex must match lines like |---| or | :--- | :--- |
            # Note: dash - must be escaped or at end of class to be a literal dash
            is_separator = re.match(r'^\|[\s:|\-]+\|$', stripped)
            
            if is_separator:
                # If we have a buffered header, convert it to Jira Header ||
                if table_header_buffer:
                    # Convert | cell | -> || cell ||
                    # simple replace of | with ||, but be careful of escaped pipes?
                    # assuming simple markdown tables for now
                    header_line = table_header_buffer
                    # replace the outer pipes and inner pipes
                    # | a | b | -> || a || b ||
                    # easiest: replace all | with ||
                    # But first apply inline formatting to the buffer
                    header_line = apply_inline_formatting(header_line)
                    header_line = header_line.replace('|', '||')
                    new_lines.append(header_line)
                    table_header_buffer = None
                continue # Skip the separator line itself
            else:
                # It's a data row or potential header
                # logic: if next line is separator, this is a header.
                # look ahead
                is_header_row = False
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line.startswith('|') and next_line.endswith('|') and re.match(r'^\|[\s:|\-]+\|$', next_line):
                        is_header_row = True
                
                if is_header_row:
                    table_header_buffer = line
                    continue # Wait to print until we confirm separator
                else:
                    # Normal row
                    # Apply inline formatting
                    line = apply_inline_formatting(line)
                    new_lines.append(line)
                    in_table = True
            continue
        
        in_table = False
        
        # --- Headers ---
        header_match = re.match(r'^(#+) (.*)$', line)
        if header_match:
            level = len(header_match.group(1))
            content = header_match.group(2)
            content = apply_inline_formatting(content)
            new_lines.append(f"h{level}. {content}")
            continue

        # --- Lists ---
        # Bullets (*, -)
        bullet_match = re.match(r'^(\s*)([-*])\s+(.*)$', line)
        if bullet_match:
            indent, marker, content = bullet_match.groups()
            # level heuristic: 2 spaces = 1 level. 0 spaces = level 1.
            level = (len(indent) // 2) + 1
            content = apply_inline_formatting(content)
            new_lines.append(f"{'*' * level} {content}")
            continue
            
        # Numbered (1.)
        num_match = re.match(r'^(\s*)(\d+)\.\s+(.*)$', line)
        if num_match:
            indent, num, content = num_match.groups()
            level = (len(indent) // 2) + 1
            content = apply_inline_formatting(content)
            new_lines.append(f"{'#' * level} {content}")
            continue

        # --- Normal Text ---
        # Apply formatting
        new_lines.append(apply_inline_formatting(line))

    # Reassemble
    result = '\n'.join(new_lines)
    
    # --- 3. Restore Code Blocks ---
    for key, block in code_blocks.items():
        result = result.replace(key, block)
        
    return result

def apply_inline_formatting(text):
    # 1. Inline Code: `text` -> {{text}}
    text = re.sub(r'`([^`]+)`', r'{{\1}}', text)
    
    # 2. Bold: **text** -> *text*
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    
    # 3. Italic: *text* -> _text_
    # Note: Logic here is simpler because we stripped list markers already!
    # But we must be careful not to mess up existing * from bold replacement.
    # Actually, Markdown is **bold**, *italic*. Jira is *bold*, _italic_.
    # If we already converted ** -> *, we now have *bold*.
    # If original was *italic*, we now have *italic*.
    # Ambiguity!
    # SOLUTION: Use placeholders for bold first.
    
    return text

def apply_inline_formatting_robust(text):
    # Protect `code`
    parts = []
    last_idx = 0
    # simple split by backticks to protect code
    # This regex splits by `code` but captures delimiters
    # actually let's use the same placeholder strategy locally for robust parsing
    
    # A. Backticks `code` -> {{code}}
    text = re.sub(r'`([^`]+)`', r'{{\1}}', text)
    
    # B. Links [text](url) -> [text|url]
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1|\2]', text)

    # C. Bold **text** -> {BOLD}text{BOLD} (placeholder)
    text = re.sub(r'\*\*(.*?)\*\*', r'___BOLD_START___\1___BOLD_END___', text)
    
    # D. Italic *text* -> _text_
    # Now it's safe to touch single stars because bold stars are hidden
    text = re.sub(r'\*(.*?)\*', r'_\1_', text)
    
    # E. Restore Bold
    text = text.replace('___BOLD_START___', '*')
    text = text.replace('___BOLD_END___', '*')
    
    return text

# Monkey patch the simple function with the robust one
apply_inline_formatting = apply_inline_formatting_robust

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to Jira Wiki Markup')
    parser.add_argument('file', nargs='?', help='Path to markdown file (reads from stdin if omitted)')
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File {args.file} not found", file=sys.stderr)
            sys.exit(1)
    else:
        content = sys.stdin.read()
        
    print(convert_md_to_jira(content))

if __name__ == "__main__":
    main()
