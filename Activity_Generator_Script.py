import os
import sys
import subprocess
import random
import shutil
from datetime import datetime, timedelta

REPO_NAME = "Activity_Generator"

def run_cmd(cmd, env=None, capture_output=True):
    result = subprocess.run(
        cmd,
        shell=True,
        env=env,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None
    )
    return result

def print_install_instructions():
    print("\n******INSTALLATION INSTRUCTIONS******\n")
    print("Git Installation:")
    print("  For Windows: Download from https://git-scm.com/download/win")
    print("  For Mac:     Run 'brew install git' in terminal")
    print("  For Linux:   Run 'sudo apt install git' (Debian/Ubuntu) or 'sudo dnf install git' (Fedora)")
    print("  For Termux:  Run 'pkg install git'")

    print("\nGitHub CLI (gh) Installation:")
    print("  For Windows: Run 'winget install --id GitHub.cli' in PowerShell")
    print("  For Mac:     Run 'brew install gh' in terminal")
    print("  For Linux:   Run 'sudo apt install gh' or follow official docs")
    print("  For Termux:  Run 'pkg install gh'")
    print("-" * 65)

def check_dependencies():
    missing = False
    print("Checking dependencies...")

    if run_cmd("git --version").returncode != 0:
        print("❌ Git is not installed or not found in PATH")
        missing = True
    else:
        print("✅ Git is installed")

    if run_cmd("gh --version").returncode != 0:
        print("❌ GitHub CLI (gh) is not installed or not found in PATH")
        missing = True
    else:
        print("✅ GitHub CLI (gh) is installed.")
        
        if os.environ.get("GH_TOKEN"):
            print("✅ GH_TOKEN detected in environment. Using exported token for authentication.")
        else:
            auth_check = run_cmd("gh auth status")
            if auth_check.returncode != 0:
                print("❌ GitHub CLI is installed, but you are not logged in")
                print("Please run 'gh auth login' in your terminal (or export GH_TOKEN), and run this script again")
                sys.exit(1)
            else:
                print("✅ GitHub CLI is authenticated.")

    if missing:
        print_install_instructions()
        print("Please install the missing tools manually and run this script again.")
        sys.exit(1)

def show_welcome():
    print("=" * 60)
    print("        GITHUB ACTIVITY GENERATOR AUTOMATION          ")
    print("=" * 60)
    print("\nIMPORTANT REQUIREMENT:")
    print("To ensure your generated commits show up on your profile heatmap,")
    print("you must enable private contributions on GitHub")
    print("\n1. Go to your GitHub profile page")
    print("2. Click 'Contribution settings' ")
    print("3. Check 'Include private contributions'")
    print("=" * 60)
    print()
    input("Press ENTER to confirm this is enabled and continue...")

# Revert back to original state
# GitHub Repo deletion
def revert_changes():
    print(f"\n--- Reverting '{REPO_NAME}' ---")

    confirm = input("Are you sure you want to delete the local file and remote repo? This cannot be undone. (y/n): ").strip().lower()
    if confirm != 'y':
        print("Revert operation cancelled.")
        return

    user_result = run_cmd("gh api user -q .login")
    if user_result.returncode == 0:
        username = user_result.stdout.decode('utf-8').strip()
        print(f"Deleting remote repository '{username}/{REPO_NAME}' on GitHub...")

        del_result = run_cmd(f"gh repo delete {username}/{REPO_NAME} --yes", capture_output=False)

        if del_result.returncode == 0:
            print("✅ Remote repository deleted.")
        else:
            print("\n⚠️ GitHub CLI failed to delete the repository.")
            print("💡 Reminder: Your token or login session MUST have the 'delete_repo' permission scope.")
            print("   - If using a Token: Ensure the 'delete_repo' box is checked.")
            print("   - If logged in via CLI: Run 'gh auth refresh -h github.com -s delete_repo'")
            print("You can manually delete the repo from your GitHub under repo settings too to make changes visible")
    else:
        print("⚠️ Could not authenticate with GitHub to delete remote repo.")

    # Delete Local Folder
    if os.path.exists(REPO_NAME):
        print("\nDeleting local repository folder...")
        def remove_readonly(func, path, excinfo):
            os.chmod(path, 0o777)
            func(path)
        shutil.rmtree(REPO_NAME, onexc=remove_readonly)
        print("✅ Local folder deleted.")
    else:
        print("No local folder found to delete.")

    print("\nRevert complete. Your profile heatmap will update shortly.")

#Commits generation
def generate_commits(start_date, end_date, density, git_name, git_email):
    if not os.path.exists(REPO_NAME):
        os.makedirs(REPO_NAME)
    os.chdir(REPO_NAME)

    if not os.path.isdir(".git"):
        run_cmd("git init")
        run_cmd("git branch -M main")
        print("\nConfiguring local Git identity for these commits...")
        run_cmd(f'git config user.name "{git_name}"')
        run_cmd(f'git config user.email "{git_email}"')

    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

    delta = timedelta(days=1)
    commit_count = 0

    print(f"\nGenerating commits from {current_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}...")

    while current_date <= end_date:
        if density == 'partial' and random.random() < 0.40:
            current_date += delta
            continue

        daily_commits = random.randint(1, 5) if density == 'full' else random.randint(1, 3)

        for _ in range(daily_commits):
            commit_time = current_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            date_str = commit_time.strftime("%Y-%m-%dT%H:%M:%S")

            with open("activity.txt", "a") as f:
                f.write(f"Commit generated on {date_str}\n")

            run_cmd("git add activity.txt")

            env = os.environ.copy()
            env['GIT_AUTHOR_DATE'] = date_str
            env['GIT_COMMITTER_DATE'] = date_str

            commit_msg = f"Private activity update - {commit_time.strftime('%Y%m%d%H%M')}"
            run_cmd(f'git commit -m "{commit_msg}"', env=env)

            commit_count += 1

        current_date += delta

    print(f"✅ Success! {commit_count} backdated commits generated locally")

#Push actions
def push_to_github():
    print("\nDeploying to GitHub autonomously...")

    user_result = run_cmd("gh api user -q .login")
    if user_result.returncode != 0:
        print("❌ Failed to get GitHub username. Ensure your token is valid or you are logged in")
        sys.exit(1)

    username = user_result.stdout.decode('utf-8').strip()

    print(f"1. Creating private repository '{REPO_NAME}' on GitHub...")
    if run_cmd(f"gh repo view {username}/{REPO_NAME}").returncode != 0:
        run_cmd(f"gh repo create {REPO_NAME} --private")

    print("2. Configuring local Git credentials...")
    subprocess.run("git remote remove origin", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    remote_url = f"https://github.com/{username}/{REPO_NAME}.git"
    run_cmd(f"git remote add origin {remote_url}")

    run_cmd('git config credential.helper ""')
    run_cmd('git config --add credential.helper "!gh auth git-credential"')

    print("3. Pushing commits to GitHub...")
    push_result = run_cmd("git push -u origin main", capture_output=False)

    if push_result.returncode == 0:
        print("\n✅ Successfully pushed to GitHub!")
        print("You can now check your GitHub profile heatmap. It may take a minute to refresh")
    else:
        print("\n❌ Error pushing to GitHub. Check the output above for details")

# Main Menu
def main():
    check_dependencies()
    show_welcome()

    print("\nWhat would you like to do?")
    print("1. Generate new profile activity")
    print("2. Revert/Undo previous activity")
    print("3. Exit")

    action = input("Enter choice (1-3): ").strip()

    if action == '3':
        sys.exit(0)
    elif action == '2':
        revert_changes()
        sys.exit(0)
    elif action == '1':
        print("\n--- Identity Configuration ---")
        print("Enter the details of the account getting the commits")
        git_name = input("GitHub Username: ").strip()
        git_email = input("GitHub Email address: ").strip()

        print("\n--- Configure Timeline ---")
        print("1. Past 1 month")
        print("2. Past 2 months")
        print("3. Past 3 months")
        print("4. Past 6 months")
        print("5. Past 12 months")
        print("6. Custom Start Date (dd/mm/yyyy)")

        choice = input("Enter choice (1-6): ").strip()
        end_date = datetime.now()

        if choice in ['1', '2', '3', '4', '5']:
            months = { '1': 30, '2': 60, '3': 90, '4': 180, '5': 365 }[choice]
            start_date = end_date - timedelta(days=months)
        elif choice == '6':
            date_str = input("Enter start date (dd/mm/yyyy 00:00): ").strip()
            try:
                start_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            except ValueError:
                print("Invalid date format. Please use dd/mm/yyyy 00:00")
                sys.exit(1)
        else:
            print("Invalid choice.")
            sys.exit(1)

        print("\n--- Frequency of Commits ---")
        print("1. Full (Commits every day, looks inorganic)")
        print("2. Partial (Skips days randomly, looks organic)")
        density_choice = input("Enter choice (1-2): ").strip()
        density = 'full' if density_choice == '1' else 'partial'

        generate_commits(start_date, end_date, density, git_name, git_email)
        push_to_github()

if __name__ == "__main__":
    main()
