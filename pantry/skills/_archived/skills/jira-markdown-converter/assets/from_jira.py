import sys
import re
import argparse

def convert_jira_to_md(text):
    # 1. Code blocks
    # Match {code}content{code} or {code:language}content{code}
    # Using non-greedy match for content
    text = re.sub(r'\{code(?::\w+)?\}(.*?)\{code\}', r'```\n\1\n```', text, flags=re.DOTALL)
    
    # 2. Inline code
    text = re.sub(r'\{\{([^}]+)\}\}', r'`\1`', text)
    
    # 3. Headings
    text = re.sub(r'^h1\. (.*)$', r'# \1', text, flags=re.MULTILINE)
    text = re.sub(r'^h2\. (.*)$', r'## \1', text, flags=re.MULTILINE)
    text = re.sub(r'^h3\. (.*)$', r'### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^h4\. (.*)$', r'#### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^h5\. (.*)$', r'##### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^h6\. (.*)$', r'###### \1', text, flags=re.MULTILINE)
    
    # 4. Bold and Italic
    # Jira Bold: *text* -> **text**
    text = re.sub(r'\*(.*?)\*', r'**\1**', text)
    # Jira Italic: _text_ -> *text*
    text = re.sub(r'_(.*?)_', r'*\1*', text)
    
    # 5. Links
    # [text|url] -> [text](url)
    text = re.sub(r'\[([^|\]]+)\|([^\]]+)\]', r'[\1](\2)', text)
    
    # 6. Lists
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        # Bullet lists: * item, ** item
        bullet_match = re.match(r'^(\*+)\s+(.*)$', line)
        if bullet_match:
            bullets, content = bullet_match.groups()
            level = len(bullets)
            indent = '  ' * (level - 1)
            new_lines.append(f"{indent}- {content}")
            continue
            
        # Numbered lists: # item, ## item
        num_match = re.match(r'^(#+)\s+(.*)$', line)
        if num_match:
            hashes, content = num_match.groups()
            level = len(hashes)
            indent = '  ' * (level - 1)
            # We use 1. for all levels in markdown, common practice
            new_lines.append(f"{indent}1. {content}")
            continue
            
        new_lines.append(line)
    
    text = '\n'.join(new_lines)
    
    # 7. Unescape braces
    text = text.replace(r'\{', '{').replace(r'\}', '}')
    
    return text

def main():
    parser = argparse.ArgumentParser(description='Convert Jira Wiki Markup to Markdown')
    parser.add_argument('file', nargs='?', help='Path to jira markup file (reads from stdin if omitted)')
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
        
    print(convert_jira_to_md(content))

if __name__ == "__main__":
    main()
