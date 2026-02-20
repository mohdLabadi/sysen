# Depth-First Search (DFS)

Depth-first search explores a graph or tree by going as deep as possible along each branch before backtracking. It is useful for path finding, cycle detection, and topological ordering.

## How it works

DFS uses a stack (or recursion, which uses the call stack). From a start node, visit a neighbor, then recursively visit one of its neighbors until no unvisited neighbors remain; then backtrack and try the next branch.

## Example

A recursive implementation on an adjacency-list graph:

```python
def dfs(graph, node, visited=None):
    if visited is None:
        visited = set()
    visited.add(node)
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
    return visited
```

Iterative version using an explicit stack:

```python
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                stack.append(neighbor)
    return visited
```

## When to use

- **Path finding** between two nodes.
- **Cycle detection** in directed or undirected graphs.
- **Topological sort** (e.g. with DFS and a finish-time stack).
- **Connected components** by running DFS from each unvisited node.

## Complexity

- Time: O(V + E) for a graph with V vertices and E edges when using an adjacency list.
- Space: O(V) for the visited set and, in the recursive version, the call stack.
