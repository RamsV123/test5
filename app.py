from flask import Flask, request, render_template_string
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# ---------------------------------
# Bellman-Ford Algorithm
# ---------------------------------
def bellman_ford(vertices, edges, source):

    distance = {v: float('inf') for v in vertices}
    parent = {v: None for v in vertices}

    distance[source] = 0

    steps = []

    for iteration in range(len(vertices) - 1):

        updated = False

        for u, v, w in edges:

            if distance[u] != float('inf') and distance[u] + w < distance[v]:

                old_distance = distance[v]

                distance[v] = distance[u] + w
                parent[v] = u

                steps.append({
                    "iteration": iteration + 1,
                    "edge": f"{u} → {v}",
                    "old": old_distance,
                    "new": distance[v]
                })

                updated = True

        if not updated:
            break

    negative_cycle = False

    for u, v, w in edges:
        if distance[u] != float('inf') and distance[u] + w < distance[v]:
            negative_cycle = True
            break

    return distance, parent, steps, negative_cycle


# ---------------------------------
# Path Reconstruction
# ---------------------------------
def get_path(parent, destination):

    path = []

    while destination is not None:
        path.append(destination)
        destination = parent[destination]

    path.reverse()

    return path


# ---------------------------------
# Graph Generation
# ---------------------------------
def generate_graph(vertices, edges, shortest_edges):

    G = nx.DiGraph()

    for v in vertices:
        G.add_node(v)

    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    plt.figure(figsize=(8, 6))

    pos = nx.spring_layout(G, seed=42)

    edge_colors = []

    for u, v in G.edges():

        if (u, v) in shortest_edges:
            edge_colors.append("red")
        else:
            edge_colors.append("black")

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=2500,
        node_color="lightblue",
        edge_color=edge_colors,
        width=3,
        arrows=True
    )

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=nx.get_edge_attributes(G, "weight")
    )

    buffer = io.BytesIO()

    plt.savefig(buffer, format="png", bbox_inches="tight")

    buffer.seek(0)

    graph_url = base64.b64encode(
        buffer.getvalue()
    ).decode()

    plt.close()

    return graph_url


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Bellman Ford Visualization</title>

    <style>
        body{
            font-family:Arial;
            margin:30px;
        }

        table{
            border-collapse:collapse;
        }

        th,td{
            border:1px solid black;
            padding:8px;
        }

        input{
            padding:5px;
        }
    </style>

</head>
<body>

<h1>Bellman-Ford Algorithm Visualization</h1>

<form method="POST">

<label>Vertices (comma separated)</label><br>
<input type="text" name="vertices"
placeholder="A,B,C,D,E" required>
<br><br>

<label>Source Vertex</label><br>
<input type="text" name="source" required>
<br><br>

<h3>Edges (Maximum 10)</h3>

<table>

<tr>
<th>From</th>
<th>To</th>
<th>Weight</th>
</tr>

{% for i in range(10) %}
<tr>
<td><input type="text" name="u{{i}}"></td>
<td><input type="text" name="v{{i}}"></td>
<td><input type="number" name="w{{i}}"></td>
</tr>
{% endfor %}

</table>

<br>

<input type="submit" value="Run Bellman-Ford">

</form>

{% if result %}

<hr>

<h2>Shortest Distances</h2>

<table>

<tr>
<th>Vertex</th>
<th>Distance</th>
</tr>

{% for v,d in result.items() %}
<tr>
<td>{{v}}</td>
<td>{{d}}</td>
</tr>
{% endfor %}

</table>

<h2>Shortest Paths</h2>

{% for node,path in paths.items() %}
<p>
<b>{{node}}</b> :
{{ " → ".join(path) }}
(Cost = {{ result[node] }})
</p>
{% endfor %}

<h2>Relaxation Steps</h2>

<table>

<tr>
<th>Iteration</th>
<th>Edge</th>
<th>Old Distance</th>
<th>New Distance</th>
</tr>

{% for step in steps %}
<tr>
<td>{{step.iteration}}</td>
<td>{{step.edge}}</td>
<td>{{step.old}}</td>
<td>{{step.new}}</td>
</tr>
{% endfor %}

</table>

{% if negative_cycle %}
<h2 style="color:red">
Negative Cycle Detected
</h2>
{% endif %}

<h2>Graph Visualization</h2>

<img src="data:image/png;base64,{{graph_url}}"
width="700">

{% endif %}

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():

    result = None
    paths = {}
    steps = []
    graph_url = None
    negative_cycle = False

    if request.method == "POST":

        vertices = [
            v.strip()
            for v in request.form["vertices"].split(",")
        ]

        source = request.form["source"].strip()

        if source not in vertices:
            return "Source vertex must exist in vertex list."

        edges = []

        for i in range(10):

            u = request.form.get(f"u{i}")
            v = request.form.get(f"v{i}")
            w = request.form.get(f"w{i}")

            if u and v and w:

                edges.append(
                    (
                        u.strip(),
                        v.strip(),
                        int(w)
                    )
                )

        result, parent, steps, negative_cycle = bellman_ford(
            vertices,
            edges,
            source
        )

        shortest_edges = set()

        for vertex in vertices:

            if vertex != source and result[vertex] != float("inf"):

                path = get_path(parent, vertex)

                paths[vertex] = path

                for i in range(len(path)-1):
                    shortest_edges.add(
                        (path[i], path[i+1])
                    )

        graph_url = generate_graph(
            vertices,
            edges,
            shortest_edges
        )

    return render_template_string(
        HTML,
        result=result,
        paths=paths,
        steps=steps,
        graph_url=graph_url,
        negative_cycle=negative_cycle
    )


if __name__ == "__main__":
    app.run(debug=True)