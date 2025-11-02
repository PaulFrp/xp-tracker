from flask import Blueprint, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import random
import os

running_bp = Blueprint('running', __name__, template_folder='../templates/running')

@running_bp.route('/running', methods=['GET'])
def running_index():
    return render_template('running.html')  # Page with form for distance, elevation, lat/lon

@running_bp.route('/running/route', methods=['POST'])
def generate_route():
    data = request.json

    # Validate inputs
    distance_km = float(data.get('distance') or 5)
    elevation_gain = float(data.get('elevation') or 50)
    lat_str = data.get('lat')
    lon_str = data.get('lon')

    if not lat_str or not lon_str:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        return jsonify({"error": "Latitude and longitude must be numbers"}), 400

    # Load OSM graph around user (increase radius for better start node)
    G = ox.graph_from_point((lat, lon), dist=3000, network_type='walk')

    # Find nearest node to user location
    start_node = ox.nearest_nodes(G, lon, lat)

    # Generate a circular loop route
    route_nodes = generate_circular_loop(G, start_node, distance_km)

    # Convert node IDs to coordinates for Leaflet
    route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route_nodes]

    # Create response
    response = {
        "route": route_coords,
        "distance": distance_km
    }

    print("Generated route JSON:", response)  # Debugging
    return jsonify(response)


def generate_circular_loop(G, start_node, target_distance_km, num_points=16):
    """
    Generates a multi-point loop to approximate a circle around the start node.
    """
    target_m = target_distance_km * 1000
    nodes_list = [start_node]

    # Get all nodes within the target distance
    lengths = nx.single_source_dijkstra_path_length(G, start_node, cutoff=target_m)
    if not lengths:
        return [start_node]

    all_nodes = list(lengths.keys())

    # Pick 'num_points' nodes around the start node at roughly equal fractions of distance
    for i in range(1, num_points + 1):
        fraction = i / num_points
        # Allowed distance range (±10%) around fraction of target
        min_dist = 0.9 * fraction * target_m
        max_dist = 1.1 * fraction * target_m

        candidates = [n for n, d in lengths.items() if min_dist <= d <= max_dist]
        if candidates:
            node = random.choice(candidates)
        else:
            node = random.choice(all_nodes)
        nodes_list.append(node)

    # Close the loop
    nodes_list.append(start_node)

    # Build full route by connecting consecutive points
    full_path = []
    for i in range(len(nodes_list) - 1):
        path_segment = nx.shortest_path(G, nodes_list[i], nodes_list[i+1], weight='length')
        if i > 0:
            # avoid repeating the start of the segment
            path_segment = path_segment[1:]
        full_path.extend(path_segment)

    return full_path
