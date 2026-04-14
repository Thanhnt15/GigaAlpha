import os
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from gigaalpha.helpers.git import Git

logger = logging.getLogger(__name__)

def get_gh_pages_base_url(git: Git) -> str:
    """
    Compute the GitHub Pages base URL from the remote origin URL.
    """
    remote_url = git.get_remote_url("origin")
    if not remote_url:
        return ""

    clean_url = remote_url.replace(".git", "")

    if "github.com" in clean_url:
        if clean_url.startswith("git@"):
            parts = clean_url.split(":")[-1].split("/")
        else:
            parts = clean_url.split("/")[-2:]
        
        if len(parts) >= 2:
            return f"https://{parts[0]}.github.io/{parts[1]}/"
    
    return ""

def deploy_to_gh_pages(repo_path: str, branch: str, file_paths: List[Path], commit_message: str) -> Tuple[bool, str, Dict[str, str]]:
    """
    Refactored deployment logic using the new Stateful Git Helper.
    """
    git = Git(repo_path)
    original_branch = git.get_current_branch()
    base_url = get_gh_pages_base_url(git)
    deployed_urls = {}

    try:
        # 1. Protection
        git.stash("push")

        # 2. Branch management
        if not git.show_ref(branch):
            logger.info(f"[Deploy] Initializing new branch: {branch}")
            git.checkout(branch, b=True)
        else:
            git.checkout(branch)

        # 3. Add files
        success_count = 0
        repo_abs_path = Path(repo_path).absolute()
        
        for fpath in file_paths:
            abs_fpath = fpath if fpath.is_absolute() else repo_abs_path / fpath
            if abs_fpath.exists():
                rel_path = abs_fpath.relative_to(repo_abs_path)
                git.add(str(rel_path))
                
                if base_url:
                    deployed_urls[abs_fpath.name] = f"{base_url}{str(rel_path).replace(os.sep, '/')}"
                success_count += 1

        if success_count == 0:
            return False, "No files found to deploy", {}

        # 4. Commit and Push
        git.commit(commit_message)
        _, success = git.push("origin", branch)
        
        if not success:
            return False, "Push to GitHub failed. Check your permissions.", {}

        return True, "Deployment successful", deployed_urls

    except Exception as e:
        logger.error(f"[Deploy Error] {e}")
        return False, str(e), {}
    finally:
        # 5. Restore original state
        if original_branch:
            git.checkout(original_branch)
            git.stash("pop")
