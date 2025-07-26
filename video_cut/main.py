import cli.cli
import sys

from video_cut.config import DAG, NODES


def load_dag_and_nodes():
    """加载DAG和节点配置"""

    return DAG, NODES

# if __name__ == "__main__":
#     cli.cli.cli()

if __name__ == "__main__":
    sys.argv = ["main.py", "generate", "--input-file", "examples/generate.json"]
    cli.cli.cli()