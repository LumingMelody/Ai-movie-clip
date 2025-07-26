from collections import defaultdict, deque

class DAGEngine:
    def __init__(self, dag):
        self.dag = dag
        self.graph = defaultdict(list)
        self.in_degree = defaultdict(int)
        self._build_graph()

    def _build_graph(self):
        for node, deps in self.dag.items():
            for dep in deps:
                self.graph[dep].append(node)
                self.in_degree[node] += 1
                self.in_degree[dep] = self.in_degree.get(dep, 0)

    def topological_sort(self):
        queue = deque([node for node in self.dag if self.in_degree[node] == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in self.graph[node]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.dag):
            raise ValueError("DAG 中存在环")
        return order

    def get_affected_nodes(self, modified_node):
        visited = set()
        result = []

        def dfs(node):
            for child in self.graph[node]:
                if child not in visited:
                    visited.add(child)
                    result.append(child)
                    dfs(child)

        dfs(modified_node)
        return result