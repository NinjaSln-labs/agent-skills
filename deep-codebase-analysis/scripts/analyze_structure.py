#!/usr/bin/env python3
import os
import argparse
import fnmatch

def list_files(startpath, max_depth=2, excludes=None):
    """
    Displays the project's directory structure for preliminary architectural analysis, 
    with support for excluding specific directories or files.
    """
    if excludes is None:
        excludes = []
    
    # Normalize the starting path
    startpath = os.path.abspath(startpath)
    print(f"--- Project Structure: {startpath} ---")
    
    for root, dirs, files in os.walk(startpath):
        # Calculate relative path to compare against exclusion patterns
        rel_path = os.path.relpath(root, startpath)
        if rel_path == '.':
            rel_path = ''

        # Filter directories based on excludes
        # dirs[:] modifies the list in-place so os.walk doesn't recurse into excluded directories
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) or fnmatch.fnmatch(os.path.join(rel_path, d), pattern) for pattern in excludes)]

        level = 0 if not rel_path else rel_path.count(os.sep) + 1
        
        if level > max_depth:
            continue
            
        indent = ' ' * 4 * level
        print(f'{indent}{os.path.basename(root) or os.path.basename(startpath)}/')
        
        if level < max_depth:
            subindent = ' ' * 4 * (level + 1)
            # Filter files based on excludes
            filtered_files = [f for f in files if not any(fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch(os.path.join(rel_path, f), pattern) for pattern in excludes)]
            for f in filtered_files:
                print(f'{subindent}{f}')

def main():
    parser = argparse.ArgumentParser(description='Analyze project directory structure.')
    parser.add_argument('path', nargs='?', default='.', help='Path to the project (default: current directory)')
    parser.add_argument('--depth', type=int, default=2, help='Maximum depth to display (default: 2)')
    parser.add_argument('--exclude', nargs='*', default=['node_modules', 'vendor', '.git', '__pycache__', '.DS_Store'], 
                        help='List of directories or patterns to exclude (e.g., node_modules .git *.log)')
    
    args = parser.parse_args()
    list_files(args.path, args.depth, args.exclude)

if __name__ == "__main__":
    main()
