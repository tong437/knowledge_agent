import subprocess
from pathlib import Path
from typing import List, Optional


def _run_git(repo_path: Path, args: List[str]) -> subprocess.CompletedProcess:
	return subprocess.run(["git", "-C", str(repo_path), *args], capture_output=True, text=True)


def get_local_branches(repo_path: str) -> List[str]:
	"""Return a list of local branches for the repository at repo_path."""
	p = Path(repo_path)
	cp = _run_git(p, ["branch", "--list"])
	if cp.returncode != 0:
		raise RuntimeError(f"git branch failed: {cp.stderr}")
	branches = []
	for line in cp.stdout.splitlines():
		line = line.strip()
		if line.startswith("*"):
			line = line[1:].strip()
		branches.append(line)
	return branches


def get_local_latest_commit_hash(repo_path: str, branch: str = "HEAD") -> Optional[str]:
	"""Return the latest commit hash for the given local branch (or HEAD)."""
	p = Path(repo_path)
	cp = _run_git(p, ["rev-parse", branch])
	if cp.returncode != 0:
		return None
	return cp.stdout.strip()


def get_remote_branches_lsremote(repo_path: str) -> List[str]:
	"""Return remote branch names using `git ls-remote --heads`."""
	p = Path(repo_path)
	cp = subprocess.run(["git", "-C", str(p), "ls-remote", "--heads"], capture_output=True, text=True)
	if cp.returncode != 0:
		raise RuntimeError(f"git ls-remote failed: {cp.stderr}")
	branches = []
	for line in cp.stdout.splitlines():
		parts = line.split()  # sha \t refs/heads/branch
		if len(parts) >= 2:
			ref = parts[1]
			if ref.startswith("refs/heads/"):
				branches.append(ref.split("refs/heads/", 1)[1])
	return branches

