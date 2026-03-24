import json
from github import Github
from github.GithubException import UnknownObjectException

class GitHubStorage:
    def __init__(self, token, repo_name):
        """
        Initialize GitHub Storage.
        :param token: GitHub Personal Access Token
        :param repo_name: Repository name in format "username/repo"
        """
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)

    def read_file(self, path):
        """
        Read a file from the repository.
        :param path: Path to the file in the repository
        :return: File content as string, or None if file doesn't exist
        """
        try:
            content_file = self.repo.get_contents(path)
            return content_file.decoded_content.decode('utf-8')
        except UnknownObjectException:
            return None

    def write_file(self, path, content, commit_message):
        """
        Write or update a file in the repository.
        :param path: Path to the file in the repository
        :param content: Content to write
        :param commit_message: Commit message
        """
        try:
            # Try to get the file to see if it exists
            content_file = self.repo.get_contents(path)
            self.repo.update_file(
                path=path,
                message=commit_message,
                content=content,
                sha=content_file.sha
            )
            print(f"✅ Updated {path} in GitHub.")
        except UnknownObjectException:
            # File doesn't exist, create it
            self.repo.create_file(
                path=path,
                message=commit_message,
                content=content
            )
            print(f"✅ Created {path} in GitHub.")

    def read_json(self, path):
        """
        Read a JSON file from the repository.
        :param path: Path to the JSON file
        :return: Parsed JSON object, or None if file doesn't exist
        """
        content = self.read_file(path)
        if content:
            return json.loads(content)
        return None

    def write_json(self, path, data, commit_message):
        """
        Write a JSON object to the repository.
        :param path: Path to the JSON file
        :param data: Data to write (dict or list)
        :param commit_message: Commit message
        """
        content = json.dumps(data, ensure_ascii=False, indent=2)
        self.write_file(path, content, commit_message)

    def list_files(self, path):
        """
        List files in a directory.
        :param path: Directory path
        :return: List of file paths
        """
        try:
            contents = self.repo.get_contents(path)
            return [content.path for content in contents if content.type == "file"]
        except UnknownObjectException:
            return []
