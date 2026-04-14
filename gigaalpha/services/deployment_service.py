import logging
from typing import List, Dict
from pathlib import Path
from gigaalpha.utils.deploy import deploy_to_gh_pages

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parents[2]

class DeploymentService:
    def __init__(self, branch: str = "gh-pages"):
        self.branch = branch

    def deploy_reports(self, html_files: List[Path], alpha_name: str, gen_name: str) -> Dict[str, str]:
        """
        Orchestrate the deployment of HTML reports to GitHub Pages.
        """
        if not html_files:
            logger.info("[Deployment] No HTML files provided for deployment.")
            return {}

        commit_msg = f"deploy: automated reports update for {alpha_name}_{gen_name}"
        
        logger.info(f"[Deployment] Starting deployment of {len(html_files)} reports to branch: {self.branch}...")
        
        success, message, urls = deploy_to_gh_pages(
            repo_path=str(PROJECT_ROOT),
            branch=self.branch,
            file_paths=html_files,
            commit_message=commit_msg
        )

        if success:
            logger.info(f"[Deployment] Success: {message}")
            return urls
        else:
            logger.error(f"[Deployment] Failed: {message}")
            return {}
