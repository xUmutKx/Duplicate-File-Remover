import os
import shutil
import re

# ANSI color codes for styling
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ASCII Art banner
def print_banner():
    banner = f"""
{Colors.OKCYAN}
  __  __           _        __  __       _ _          
 |  \/  | ___   __| | ___  |  \/  | __ _| | | ___ _ __ 
 | |\/| |/ _ \ / _` |/ _ \ | |\/| |/ _` | | |/ _ \ '__|
 | |  | | (_) | (_| |  __/ | |  | | (_| | | |  __/ |   
 |_|  |_|\___/ \__,_|\___| |_|  |_|\__,_|_|_|\___|_|   
                                                      
{Colors.ENDC}
"""
    print(banner)

# --- SETTINGS ---
music_dir = "/storage/emulated/0/Music/Audio"
destination_dir = "/storage/emulated/0/Music/Audio/duplicates_m4a"

os.makedirs(destination_dir, exist_ok=True)

valid_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']

def normalize_filename(name):
    # Remove ALL parentheses and their contents
    name = re.sub(r'\s*\([^)]*\)', '', name)

    # Remove common noise words (case insensitive)
    noise_words = [
        r'\bofficial\b', r'\bmusic\b', r'\bvideo\b', r'\baudio\b',
        r'\blyrics\b', r'\bhd\b', r'\bfeat\b', r'\bfeaturing\b',
        r'\bexplicit\b', r'\bversion\b', r'\bremix\b'
    ]
    pattern = re.compile('|'.join(noise_words), flags=re.IGNORECASE)
    name = pattern.sub('', name)

    # Remove quotes and trim spaces
    name = name.replace('＂', '').replace('"', '').strip()

    # Capitalize first letter of each word
    name = ' '.join(word.capitalize() for word in name.split())

    # Collapse multiple spaces to a single space
    name = re.sub(r'\s+', ' ', name)

    return name

def colored(text, color):
    return f"{color}{text}{Colors.ENDC}"

def main():
    print_banner()
    print(colored("Renaming files to normalized names...\n", Colors.OKBLUE))

    files = os.listdir(music_dir)
    for f in files:
        full_path = os.path.join(music_dir, f)
        if not os.path.isfile(full_path):
            continue
        name, ext = os.path.splitext(f)
        ext = ext.lower()
        if ext not in valid_extensions:
            continue

        new_base = normalize_filename(name)
        if not new_base:
            continue

        new_name = new_base + ext
        new_path = os.path.join(music_dir, new_name)

        # Improved rename logic:
        if os.path.exists(new_path):
            # Only try to find a new name if it's not the same file
            if os.path.abspath(full_path) != os.path.abspath(new_path):
                count = 1
                while True:
                    candidate = f"{new_base} ({count}){ext}"
                    candidate_path = os.path.join(music_dir, candidate)
                    if not os.path.exists(candidate_path):
                        new_name = candidate
                        new_path = candidate_path
                        break
                    count += 1
        elif new_path == full_path:
            continue  # Already named correctly, skip renaming

        if new_path != full_path:
            print(colored(f"Renaming:\n  {f}\n-> {new_name}\n", Colors.WARNING))
            os.rename(full_path, new_path)

    # Reload files after rename
    files = os.listdir(music_dir)
    music_files = []
    for f in files:
        full_path = os.path.join(music_dir, f)
        if os.path.isfile(full_path):
            name, ext = os.path.splitext(f)
            ext = ext.lower()
            if ext in valid_extensions and ext != '.lrc':
                music_files.append((name, ext, full_path))

    grouped_files = {}
    for name, ext, path in music_files:
        norm_name = normalize_filename(name)
        if norm_name not in grouped_files:
            grouped_files[norm_name] = []
        grouped_files[norm_name].append((name, ext, path))

    m4a_to_move = []
    originals = {}  # To track original files for each group

    for norm_name, group in grouped_files.items():
        # Find originals (non-m4a) to keep
        original_files = [p for n, e, p in group if e != '.m4a']
        if not original_files:
            continue
        originals[norm_name] = original_files
        # Collect m4a duplicates
        for n, e, p in group:
            if e == '.m4a':
                m4a_to_move.append((norm_name, p))

    if not m4a_to_move:
        print(colored("No duplicate .m4a files found.", Colors.OKGREEN))
        return

    print(colored("\nFound duplicate .m4a files to move:\n", Colors.HEADER))
    for norm_name, m4a_path in m4a_to_move:
        print(colored(f" - {os.path.basename(m4a_path)}", Colors.FAIL))
        # Show originals kept:
        for orig in originals.get(norm_name, []):
            print(colored(f"    ↳ Keeping original: {os.path.basename(orig)}", Colors.OKGREEN))
        print()

    confirm = input(colored(f"Move these .m4a files to:\n{destination_dir}\nConfirm? (yes/no): ", Colors.BOLD)).strip().lower()
    if confirm in ['yes', 'y']:
        moved_count = 0
        for _, path in m4a_to_move:
            try:
                filename = os.path.basename(path)
                dest_path = os.path.join(destination_dir, filename)
                shutil.move(path, dest_path)
                print(colored(f"Moved: {filename}", Colors.OKBLUE))
                moved_count += 1
            except Exception as e:
                print(colored(f"Error moving {path}: {e}", Colors.FAIL))
        print(colored(f"\nDone. {moved_count} files moved.", Colors.OKGREEN))
    else:
        print(colored("Operation cancelled.", Colors.WARNING))

if __name__ == "__main__":
    main()
