from ..utils.logger import get_logger
from typing import Any, Dict, List, Optional

import time

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

logger = get_logger("gitea_client")


class GiteaClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

        if httpx is None:
            logger.error("httpx library is not installed (required for GiteaClient)")
            raise RuntimeError("httpx is required for GiteaClient")

        self._client = httpx.Client(base_url=self.base_url, timeout=20.0)
        if token:
            self._client.headers.update({"Authorization": f"token {token}"})

    def _request_with_retry(self, method: str, path: str, params: Optional[Dict] = None, max_retries: int = 3, backoff: float = 1.0):
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = self._client.request(method, path, params=params)
                resp.raise_for_status()
                return resp
            except Exception as e:
                last_exc = e
                logger.warning("Gitea request failed (attempt %d/%d): %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(backoff * attempt)
        logger.error("Gitea request failed after %d attempts: %s", max_retries, last_exc)
        raise last_exc

    def list_user_repos(self, user_id: str, per_page: int = 50, max_pages: int = 20) -> List[Dict[str, Any]]:
        """Return aggregated list of repositories for a user/org with pagination and retries.

        This will request pages until an empty page is returned or `max_pages` is reached.
        """
        path = f"/api/v1/users/{user_id}/repos"
        page = 1
        results: List[Dict[str, Any]] = []
        while page <= max_pages:
            params = {"page": page, "limit": per_page}
            resp = self._request_with_retry("GET", path, params=params)
            data = resp.json()
            if not data:
                break
            results.extend(data)
            if len(data) < per_page:
                break
            page += 1
        return results

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        path = f"/api/v1/repos/{owner}/{repo}"
        resp = self._request_with_retry("GET", path)
        return resp.json()

    def list_repo_branches(self, owner: str, repo: str, per_page: int = 50, max_pages: int = 10) -> List[Dict[str, Any]]:
        path = f"/api/v1/repos/{owner}/{repo}/branches"
        page = 1
        branches: List[Dict[str, Any]] = []
        while page <= max_pages:
            params = {"page": page, "limit": per_page}
            resp = self._request_with_retry("GET", path, params=params)
            data = resp.json()
            if not data:
                break
            branches.extend(data)
            if len(data) < per_page:
                break
            page += 1
        return branches

    def get_branch_latest_commit(self, owner: str, repo: str, branch: str) -> Optional[str]:
        """Return the latest commit SHA for a given branch (or None).

        Uses the branches endpoint which contains commit ref information.
        """
        path = f"/api/v1/repos/{owner}/{repo}/branches/{branch}"
        try:
            resp = self._request_with_retry("GET", path)
            data = resp.json()
            commit = data.get("commit")
            if commit:
                return commit.get("id") or commit.get("sha")
        except Exception:
            logger.exception("Failed to get latest commit for %s/%s@%s", owner, repo, branch)
        return None

    def get_commit(self, owner: str, repo: str, sha: str) -> Optional[Dict[str, Any]]:
        path = f"/api/v1/repos/{owner}/{repo}/git/commits/{sha}"
        try:
            resp = self._request_with_retry("GET", path)
            return resp.json()
        except Exception:
            logger.exception("Failed to fetch commit %s for %s/%s", sha, owner, repo)
            return None

