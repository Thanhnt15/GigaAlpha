import logging, os
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
        Orchestrate the deployment of HTML reports to GH Pages.
        """
        if not html_files:
            return {}

        logger.info(f"[Deployment] Starting deployment of {len(html_files)} reports to branch: {self.branch}...")
        
        commit_message = f"Deploy reports for {alpha_name}_{gen_name}"
        success, message, urls = deploy_to_gh_pages(
            repo_path=str(PROJECT_ROOT),
            branch=self.branch,
            file_paths=html_files,
            commit_message=commit_message,
            token=os.getenv("GITHUB_TOKEN")
        )

        if success:
            logger.info(f"[Deployment] Success: {message}")
            return urls
        else:
            logger.error(f"[Deployment] Failed: {message}")
            return {}
