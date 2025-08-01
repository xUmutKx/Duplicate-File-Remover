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

def colored(text, color):
    return f"{color}{text}{Colors.ENDC}"

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

def rename_files(music_dir, valid_extensions):
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

        # Skip renaming if target exists and is different file
        if os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(full_path):
            print(colored(f"Skipping rename (target exists): {f}", Colors.WARNING))
            continue

        if new_path != full_path:
            print(colored(f"Renaming:\n  {f}\n-> {new_name}\n", Colors.WARNING))
            os.rename(full_path, new_path)

def detect_and_handle_duplicates(music_dir, destination_dir, valid_extensions):
    os.makedirs(destination_dir, exist_ok=True)

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

    files_to_handle = []
    originals = {}

    for norm_name, group in grouped_files.items():
        group_sorted = sorted(group, key=lambda x: x[1])  # sort by extension alphabetically
        original = group_sorted[0][2]  # keep this file
        originals[norm_name] = original
        duplicates = [p for _, _, p in group_sorted[1:]]
        files_to_handle.extend([(norm_name, p) for p in duplicates])

    if not files_to_handle:
        print(colored("No duplicates found.", Colors.OKGREEN))
        return

    print(colored("\nFound duplicates to handle (keeping one original per group):\n", Colors.HEADER))
    for norm_name, path in files_to_handle:
        print(colored(f" - {os.path.basename(path)}", Colors.FAIL))
        print(colored(f"    ↳ Keeping original: {os.path.basename(originals[norm_name])}", Colors.OKGREEN))
        print()

    # Ask whether to move or delete duplicates
    while True:
        action = input(colored("What do you want to do with duplicates?\n"
                              "1) Move duplicates to folder\n"
                              "2) Delete duplicates\n"
                              "Enter choice (1 or 2): ", Colors.BOLD)).strip()
        if action in ['1', '2']:
            break
        print(colored("Invalid choice. Please enter 1 or 2.", Colors.WARNING))

    if action == '1':
        confirm = input(colored(f"Move these duplicates to:\n{destination_dir}\nConfirm? (yes/no): ", Colors.BOLD)).strip().lower()
        if confirm in ['yes', 'y']:
            moved_count = 0
            for _, path in files_to_handle:
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
    else:  # Delete
        confirm = input(colored(f"Are you sure you want to DELETE these duplicates? This action cannot be undone.\nConfirm? (yes/no): ", Colors.BOLD)).strip().lower()
        if confirm in ['yes', 'y']:
            deleted_count = 0
            for _, path in files_to_handle:
                try:
                    os.remove(path)
                    print(colored(f"Deleted: {os.path.basename(path)}", Colors.FAIL))
                    deleted_count += 1
                except Exception as e:
                    print(colored(f"Error deleting {path}: {e}", Colors.WARNING))
            print(colored(f"\nDone. {deleted_count} files deleted.", Colors.OKGREEN))
        else:
            print(colored("Deletion cancelled.", Colors.WARNING))

def main():
    print_banner()

    default_music_dir = "/storage/emulated/0/Music/Audio"
    valid_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']

    print("Select an action:")
    print("1) Rename files only")
    print("2) Detect & handle duplicates only (move or delete)")
    print("3) Rename + Detect & handle duplicates")
    print("4) Exit")

    choice = input(colored("Enter choice (1-4): ", Colors.BOLD)).strip()
    if choice not in ['1', '2', '3']:
        print("Exiting.")
        return

    music_dir = input(colored(f"Enter music folder path (default: {default_music_dir}): ", Colors.OKCYAN)).strip()
    if not music_dir:
        music_dir = default_music_dir

    if not os.path.isdir(music_dir):
        print(colored(f"Error: Directory '{music_dir}' does not exist.", Colors.FAIL))
        return

    destination_dir = None
    if choice in ['2', '3']:
        destination_dir = input(colored(
            f"Enter duplicates folder path (default: will create 'duplicates_moved' inside {music_dir}): ", Colors.OKCYAN)).strip()
        if not destination_dir:
            destination_dir = os.path.join(music_dir, "duplicates_moved")

    if choice == '1':
        rename_files(music_dir, valid_extensions)
    elif choice == '2':
        detect_and_handle_duplicates(music_dir, destination_dir, valid_extensions)
    elif choice == '3':
        rename_files(music_dir, valid_extensions)
        detect_and_handle_duplicates(music_dir, destination_dir, valid_extensions)

if __name__ == "__main__":
    main()