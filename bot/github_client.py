import base64
import logging
from typing import Optional, List, Tuple, Dict, Any
from github import Github, GithubException, Auth
from bot.config import GITHUB_PAT, GITHUB_REPO, GITHUB_BRANCH, GITHUB_USERNAME

logger = logging.getLogger("ALC_Support.GitHub")


class ALCGitHubClient:
    def __init__(self):
        if GITHUB_PAT:
            auth = Auth.Token(GITHUB_PAT)
            self.gh = Github(auth=auth)
        else:
            self.gh = Github()
        self.repo_name = GITHUB_REPO
        self.branch = GITHUB_BRANCH

    def _get_repo(self):
        return self.gh.get_repo(self.repo_name)

    def list_files(self) -> List[str]:
        """Lists editable website files from the GitHub repository."""
        try:
            repo = self._get_repo()
            tree = repo.get_git_tree(self.branch, recursive=True)
            editable_exts = (".html", ".css", ".js", ".json", ".xml", ".txt", ".md")
            files = [
                element.path for element in tree.tree
                if element.type == "blob"
                and any(element.path.lower().endswith(ext) for ext in editable_exts)
                and not element.path.startswith("bot/")
                and not element.path.startswith(".github/")
            ]
            return sorted(files)
        except Exception as e:
            logger.error(f"Error listing repo files from GitHub: {e}")
            return []

    def read_file(self, path: str) -> Optional[str]:
        """Fetches the content of a file from GitHub."""
        try:
            repo = self._get_repo()
            content_file = repo.get_contents(path, ref=self.branch)
            if isinstance(content_file, list):
                return None
            return content_file.decoded_content.decode("utf-8")
        except Exception as e:
            logger.error(f"Error reading file '{path}' from GitHub: {e}")
            return None

    def commit_file_change(self, path: str, new_content: str, commit_message: str) -> Tuple[bool, str, Optional[str]]:
        """
        Commits a file update directly to GitHub on behalf of alckellogg.
        Returns: (success, message_or_error, commit_html_url)
        """
        try:
            repo = self._get_repo()
            try:
                content_file = repo.get_contents(path, ref=self.branch)
                if isinstance(content_file, list):
                    return False, "Target path is a directory, not a file.", None
                sha = content_file.sha
                res = repo.update_file(
                    path=path,
                    message=f"feat(website): {commit_message} [via ALC Support Bot]",
                    content=new_content,
                    sha=sha,
                    branch=self.branch,
                )
                commit_url = res["commit"].html_url
                return True, f"Successfully committed changes to `{path}`.", commit_url
            except GithubException as ge:
                if ge.status == 404:
                    # Create new file
                    res = repo.create_file(
                        path=path,
                        message=f"feat(website): create {path} [via ALC Support Bot]",
                        content=new_content,
                        branch=self.branch,
                    )
                    commit_url = res["commit"].html_url
                    return True, f"Successfully created `{path}`.", commit_url
                else:
                    raise ge
        except Exception as e:
            logger.error(f"Failed to commit file '{path}' to GitHub: {e}")
            return False, f"GitHub error: {str(e)}", None

    def upload_image_asset(self, path: str, image_bytes: bytes, commit_message: str) -> Tuple[bool, str, Optional[str]]:
        """Uploads a binary image file to the GitHub repo."""
        try:
            repo = self._get_repo()
            try:
                content_file = repo.get_contents(path, ref=self.branch)
                sha = content_file.sha
                res = repo.update_file(
                    path=path,
                    message=f"asset: {commit_message} [via ALC Support Bot]",
                    content=image_bytes,
                    sha=sha,
                    branch=self.branch,
                )
            except GithubException:
                res = repo.create_file(
                    path=path,
                    message=f"asset: upload {path} [via ALC Support Bot]",
                    content=image_bytes,
                    branch=self.branch,
                )
            return True, f"Image asset uploaded to `{path}`.", res["commit"].html_url
        except Exception as e:
            logger.error(f"Failed to upload asset '{path}': {e}")
            return False, f"Asset upload error: {str(e)}", None

    def get_latest_workflow_run(self) -> Optional[Dict[str, Any]]:
        """Fetches the latest GitHub Actions CI/CD deployment workflow run."""
        try:
            repo = self._get_repo()
            runs = repo.get_workflow_runs()
            if runs.totalCount > 0:
                latest = runs[0]
                return {
                    "id": latest.id,
                    "name": latest.name,
                    "status": latest.status,
                    "conclusion": latest.conclusion,
                    "html_url": latest.html_url,
                    "head_commit": latest.head_commit.message if latest.head_commit else "",
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching workflow runs: {e}")
            return None
