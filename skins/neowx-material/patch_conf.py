#!/usr/bin/env python3
"""
Configuration Patcher for neowx-material skin

This script reads configuration values from skin.conf.patch and applies them to skin.conf
while preserving the original structure, comments, and indentation.

Features:
- Preserves original file structure, comments, and indentation
- Handles hierarchical sections (e.g., [Extras], [[Header]], [[[iFrame1]]])
- Updates existing key-value pairs
- Adds new sections and keys when they don't exist
- Reports all changes made

Usage:
    cd /path/to/neowx-material/skins/neowx-material
    python3 patch_conf.py

Requirements:
- skin.conf.patch file with the configuration changes
- skin.conf file to be patched
- Must be run from skins/neowx-material directory

The skin.conf.patch file should follow the same format as skin.conf:
    [Extras]
        [[Header]]
            custom1_label = My Label
            custom1_url = https://example.com
        [[Footer]]
            name = My Station Name

Author: GitHub Copilot
"""

import re
import os
import sys
from collections import OrderedDict
import configparser


class ConfigPatcher:
    def __init__(self, patch_file="skin.conf.patch",
                 target_file="skin.conf"):
        self.patch_file = patch_file
        self.target_file = target_file
        self.patch_data = {}
        self.target_lines = []

    def parse_patch_file(self):
        """Parse the patch file to extract sections and key-value pairs."""
        print(f"Reading patch file: {self.patch_file}")

        if not os.path.exists(self.patch_file):
            raise FileNotFoundError(f"Patch file not found: {self.patch_file}")

        with open(self.patch_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse hierarchical sections using regex
        current_section = []

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for section headers
            section_match = re.match(r'^(\[+)([^\]]+)(\]+)$', line)
            if section_match:
                level = len(section_match.group(1))
                section_name = section_match.group(2)

                # Adjust current section based on level
                current_section = current_section[:level-1] + [section_name]
                continue

            # Check for key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Store in nested dictionary structure
                section_path = tuple(current_section)
                if section_path not in self.patch_data:
                    self.patch_data[section_path] = {}
                self.patch_data[section_path][key] = value

    def read_target_file(self):
        """Read the target file line by line."""
        print(f"Reading target file: {self.target_file}")

        if not os.path.exists(self.target_file):
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

        with open(self.target_file, 'r', encoding='utf-8') as f:
            self.target_lines = f.readlines()

    def find_section_boundaries(self, section_path):
        """Find the start and end lines of a section in the target file."""
        section_levels = []
        target_level = len(section_path)

        # Build section hierarchy as we go through the file
        for i, line in enumerate(self.target_lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check for section headers
            section_match = re.match(r'^(\s*)(\[+)([^\]]+)(\]+)', line)
            if section_match:
                indent = section_match.group(1)
                level = len(section_match.group(2))
                section_name = section_match.group(3)

                # Adjust current section levels
                section_levels = section_levels[:level-1] + [(section_name, i, indent)]

                # Check if this matches our target section
                current_path = tuple(item[0] for item in section_levels)
                if current_path == section_path:
                    # Find the end of this section by looking for the next section at same or higher level
                    end_line = len(self.target_lines)
                    for j in range(i + 1, len(self.target_lines)):
                        next_line = self.target_lines[j]
                        next_stripped = next_line.strip()
                        if not next_stripped or next_stripped.startswith('#'):
                            continue

                        next_section_match = re.match(r'^(\s*)(\[+)([^\]]+)(\]+)', next_line)
                        if next_section_match:
                            next_level = len(next_section_match.group(2))
                            # End section when we find a section at the same level or higher (lower number)
                            if next_level <= target_level:
                                end_line = j
                                break

                    return i, end_line, indent

        return None, None, None

    def find_key_in_section(self, section_start, section_end, key):
        """Find a key within a specific section."""
        for i in range(section_start + 1, section_end):
            line = self.target_lines[i]
            stripped = line.strip()

            if not stripped or stripped.startswith('#'):
                continue

            # Stop if we hit a subsection
            if re.match(r'^\s*\[', line):
                break

            if '=' in line:
                line_key = line.split('=')[0].strip()
                if line_key == key:
                    return i

        return None

    def get_line_indentation(self, line_num):
        """Get the indentation of the line or estimate from surrounding lines."""
        if line_num < len(self.target_lines):
            match = re.match(r'^(\s*)', self.target_lines[line_num])
            if match:
                return match.group(1)

        # Estimate indentation from nearby lines
        for i in range(max(0, line_num - 5), min(len(self.target_lines), line_num + 5)):
            line = self.target_lines[i]
            if '=' in line and not line.strip().startswith('#'):
                match = re.match(r'^(\s*)', line)
                if match:
                    return match.group(1)

        return '        '  # Default indentation

    def apply_patches(self):
        """Apply all patches from patch_data to target_lines."""
        modifications_made = 0

        for section_path, patches in self.patch_data.items():
            print(f"Processing section: {' -> '.join(section_path)}")

            section_start, section_end, section_indent = self.find_section_boundaries(section_path)

            if section_start is None:
                # Section doesn't exist, need to add it
                print(f"  Adding new section: {section_path}")
                self.add_new_section(section_path, patches)
                modifications_made += len(patches)
                continue

            # Process each key-value pair in this section
            for key, value in patches.items():
                key_line = self.find_key_in_section(section_start, section_end, key)

                if key_line is not None:
                    # Key exists, update it
                    old_line = self.target_lines[key_line].rstrip()
                    indent = self.get_line_indentation(key_line)
                    new_line = f"{indent}{key} = {value}\n"

                    if old_line.strip() != new_line.strip():
                        print(f"  Updating {key}: {old_line.split('=')[1].strip()} -> {value}")
                        self.target_lines[key_line] = new_line
                        modifications_made += 1
                else:
                    # Key doesn't exist, add it
                    print(f"  Adding new key: {key} = {value}")
                    self.add_key_to_section(section_start, section_end, key, value, section_indent)
                    modifications_made += 1

        print(f"\nTotal modifications made: {modifications_made}")
        return modifications_made

    def add_new_section(self, section_path, patches):
        """Add a completely new section with its key-value pairs."""
        # Find the parent section
        if len(section_path) > 1:
            parent_path = section_path[:-1]
            parent_start, parent_end, parent_indent = self.find_section_boundaries(parent_path)

            if parent_start is not None:
                # Insert within the parent section, at the end but before the parent section ends
                # Default to insert just before the parent section ends
                insert_line = parent_end
                target_level = len(section_path)

                # Look for the best insertion point within the parent section
                last_same_level_section = None
                for i in range(parent_start + 1, parent_end):
                    line = self.target_lines[i]
                    section_match = re.match(r'^(\s*)(\[+)([^\]]+)(\]+)', line)
                    if section_match:
                        level = len(section_match.group(2))
                        if level == target_level:
                            # Track the last section at our target level
                            last_same_level_section = i
                        elif level < target_level:
                            # Found a section at a higher level (parent), insert before it
                            insert_line = i
                            break

                # If we found sections at the same level, insert after the last one
                if last_same_level_section is not None:
                    # Find the end of the last same-level section
                    for j in range(last_same_level_section + 1, parent_end):
                        line = self.target_lines[j]
                        section_match = re.match(r'^(\s*)(\[+)([^\]]+)(\]+)', line)
                        if section_match:
                            level = len(section_match.group(2))
                            if level <= target_level:
                                insert_line = j
                                break
                    else:
                        # No other section found, insert at end of parent section
                        # But look for comment blocks that belong to the next section
                        insert_line = parent_end

                        # Scan backwards from parent_end to find a good insertion point
                        # Look for comment blocks that seem to belong to the next section
                        for j in range(parent_end - 1, last_same_level_section, -1):
                            line = self.target_lines[j].strip()
                            # If we find a comment that looks like a section header, insert before it
                            if (line.startswith('#') and len(line) > 1 and
                                not line.startswith('# Add more') and
                                not line.startswith('# Just uncomment') and
                                not line.startswith('# Example:') and
                                ('---' in line or
                                 any(word in line.lower() for word in ['charts', 'configuration', 'behavior', 'settings', 'color palette']))):
                                # Found a section header comment, insert before the comment block
                                # Find the start of this comment block
                                comment_start = j
                                for k in range(j - 1, last_same_level_section, -1):
                                    prev_line = self.target_lines[k].strip()
                                    if prev_line and not prev_line.startswith('#'):
                                        break
                                    comment_start = k
                                insert_line = comment_start
                                break
                else:
                    # No sections at same level found, insert at end of parent but before comment blocks
                    insert_line = parent_end
                    # Look for comment blocks that belong to next section
                    for j in range(parent_start + 1, parent_end):
                        line = self.target_lines[j].strip()
                        if (line.startswith('#') and len(line) > 1 and
                            not line.startswith('# Add more') and
                            not line.startswith('# Just uncomment') and
                            not line.startswith('# Example:') and
                            ('---' in line or
                             any(word in line.lower() for word in ['charts', 'configuration', 'behavior', 'settings']))):
                            insert_line = j
                            break
            else:
                # Parent section doesn't exist, add at end
                insert_line = len(self.target_lines)
        else:
            # Top level section, add at end
            insert_line = len(self.target_lines)

        # Build section header with proper indentation matching the existing pattern
        indent_level = len(section_path)
        # Pattern: [Section] = 0 spaces, [[Subsection]] = 4 spaces, [[[Sub-subsection]]] = 8 spaces
        base_indent = '    ' * (indent_level - 1)  # 4 spaces per level above the first
        brackets = '[' * indent_level + ']' * indent_level
        section_header = f"{base_indent}{brackets[0:indent_level]}{section_path[-1]}{brackets[indent_level:]}\n"

        # Insert section and its content
        new_lines = ['\n', section_header]

        # Key indentation: add 4 more spaces for keys within the section
        key_indent = base_indent + '    '
        for key, value in patches.items():
            new_lines.append(f"{key_indent}{key} = {value}\n")

        # Insert the new lines
        for j, line in enumerate(new_lines):
            self.target_lines.insert(insert_line + j, line)

    def add_key_to_section(self, section_start, section_end, key, value, section_indent):
        """Add a new key-value pair to an existing section."""
        # Find the best place to insert (after last key but before any subsections or comments)
        insert_line = section_end
        last_key_line = None

        for i in range(section_start + 1, section_end):
            line = self.target_lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue

            # Found a subsection - insert before it
            if re.match(r'^\s*\[\[', line):
                insert_line = i
                break

            # Found a key-value pair - track it as potential insertion point
            if '=' in line and not stripped.startswith('#'):
                last_key_line = i + 1  # Insert after this key

        # If we found key-value pairs, insert after the last one
        if last_key_line is not None:
            insert_line = last_key_line

        # Determine proper indentation by looking at existing keys in the section
        key_indent = None
        for i in range(section_start + 1, section_end):
            line = self.target_lines[i]
            if '=' in line and not line.strip().startswith('#'):
                key_indent = re.match(r'^(\s*)', line).group(1)
                break

        # If no existing keys found, use section indent + 4 spaces
        if key_indent is None:
            key_indent = section_indent + '    '

        new_line = f"{key_indent}{key} = {value}\n"
        self.target_lines.insert(insert_line, new_line)

    def write_target_file(self):
        """Write the modified content back to the target file."""
        print(f"Writing changes to: {self.target_file}")

        # Write modified content
        with open(self.target_file, 'w', encoding='utf-8') as f:
            f.writelines(self.target_lines)

    def patch(self):
        """Main patching method."""
        try:
            self.parse_patch_file()
            self.read_target_file()
            modifications = self.apply_patches()

            if modifications > 0:
                self.write_target_file()
                print(f"\nPatching completed successfully! {modifications} modifications applied.")
            else:
                print("\nNo changes needed. Files are already in sync.")

        except Exception as e:
            print(f"Error during patching: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    print("neowx-material Configuration Patcher")
    print("=" * 40)
    print("This script applies configuration patches from skin.conf.patch to skin.conf")
    print("while preserving the original structure, comments, and indentation.\n")

    # Check if we're in the right directory (should be in skins/neowx-material)
    if not os.path.exists("skin.conf"):
        print("Error: This script should be run from the skins/neowx-material directory.")
        print("Current directory should contain 'skin.conf' file.")
        print("\nUsage:")
        print("  cd /path/to/neowx-material/skins/neowx-material")
        print("  python3 patch_conf.py")
        print("  # or")
        print("  ./patch_conf.py")
        sys.exit(1)

    # Check if patch file exists
    if not os.path.exists("skin.conf.patch"):
        print("Error: Patch file not found: skin.conf.patch")
        print("Please create a patch file with the configuration changes you want to apply.")
        sys.exit(1)

    # Check if target file exists
    if not os.path.exists("skin.conf"):
        print("Error: Target file not found: skin.conf")
        print("Please ensure the skin.conf file exists in the current directory.")
        sys.exit(1)

    patcher = ConfigPatcher()
    patcher.patch()


if __name__ == "__main__":
    main()
