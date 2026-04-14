import subprocess
import os
import logging
from pathlib import Path
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class Git:
    """
    Standardize Git Helper for Python Projects.
    Designed for portability and ease of use in automated pipelines.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = str(Path(repo_path).absolute())
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            logger.warning(f"[Git] Path {self.repo_path} is not a git repository.")

    def run(self, *args: str) -> Tuple[Optional[subprocess.CompletedProcess], bool]:
        """Core executor for git commands."""
        command = ["git", *args]
        try:
            res = subprocess.run(
                command, 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                encoding='utf-8'
            )
            
            success = res.returncode == 0
            
            # Special handling for "nothing to commit" behavior
            if not success:
                out_composite = (res.stdout + res.stderr).lower()
                no_changes_msgs = [
                    "nothing to commit", 
                    "no changes added to commit", 
                    "working tree clean",
                    "up to date",
                    "no changes added"
                ]
                # If it's a commit and we see "no changes" or stderr is essentially empty
                if "commit" in args:
                    if any(msg in out_composite for msg in no_changes_msgs) or not res.stderr.strip():
                        return res, True
                
                if "push" in args and "up to date" in out_composite:
                    return res, True

                logger.error(f"[Git Error] '{' '.join(command)}' failed: {res.stderr.strip()}")
            
            return res, success
        except Exception as e:
            logger.error(f"[Git System Error] Failed to execute {' '.join(command)}: {e}")
            return None, False

    def get_current_branch(self) -> str:
        res, success = self.run("rev-parse", "--abbrev-ref", "HEAD")
        return res.stdout.strip() if success else ""

    def get_remote_url(self, remote: str = "origin") -> str:
        res, success = self.run("remote", "get-url", remote)
        return res.stdout.strip() if success else ""

    def checkout(self, branch: str, b: bool = False):
        args = ["checkout"]
        if b: args.append("-b")
        args.append(branch)
        return self.run(*args)

    def add(self, path: str = "."):
        return self.run("add", path)

    def commit(self, message: str):
        return self.run("commit", "-m", message)

    def push(self, remote: str = "origin", branch: str = None):
        if not branch:
            branch = self.get_current_branch()
        return self.run("push", remote, branch)

    def pull(self, remote: str = "origin", branch: str = None, rebase: bool = True):
        args = ["pull", remote]
        if branch: args.append(branch)
        if rebase: args.append("--rebase")
        return self.run(*args)

    def stash(self, action: str = "push"):
        """action: 'push' or 'pop'"""
        return self.run("stash", action)

    def show_ref(self, branch: str) -> bool:
        _, success = self.run("show-ref", "--verify", f"refs/heads/{branch}")
        return success