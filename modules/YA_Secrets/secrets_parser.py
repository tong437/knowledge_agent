import os
import subprocess
import yaml
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("secrets_parser")


def load_secrets(path: str = "env.yaml", sops_config: str = ".sops.yaml") -> dict:
    """
    解密 sops 文件并返回 secrets 字典
    """

    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"待解密文件 '{path}' 不存在")

        if not os.path.exists(sops_config):
            raise FileNotFoundError(f"SOPS 配置文件 '{sops_config}' 不存在")

        result = subprocess.run(
            ["sops", "--config", sops_config, "-d", path],
            capture_output=True,
            text=True,
            check=True,
        )
        decrypted_yaml = result.stdout

        data = yaml.safe_load(decrypted_yaml)

        if not isinstance(data, dict):
            raise ValueError("YAML 内容格式不正确")

        secrets = data.get("secrets", {})
        if not isinstance(secrets, dict):
            raise ValueError("YAML 中未找到有效的 secrets 字段")

        return secrets

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"解密失败: {e.stderr}") from e


def get_secret(secret_name: str, path: str = "env.yaml"):
    """
    获取某个 secret 的值
    """
    try:
        secrets = load_secrets(path)
        if secret_name not in secrets:
            raise KeyError(f"Secret '{secret_name}' 不存在")
        return secrets[secret_name]
    except Exception as e:
        logger.error(f"获取 secret '{secret_name}' 失败: {e}")
        return None


if __name__ == "__main__":
    try:
        api_key = get_secret("api_key")
        logger.info(f"API KEY = {api_key}")
    except KeyError:
        logger.warning("api_key 不存在")
