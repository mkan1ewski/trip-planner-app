from services.google_maps import get_route_matrix
from models import Edge, Graph, TravelMode

async def get_route_graph(origins: list, destinations: list, travel_mode: TravelMode) -> dict:
    match travel_mode:
        case TravelMode.DRIVE:
            drive_matrix = await get_route_matrix(origins=origins, destinations=destinations, travel_mode=TravelMode.DRIVE)
            return build_graph_from_matrix(
                matrix=drive_matrix,
                travel_mode=TravelMode.DRIVE,
            )
        case TravelMode.WALK:
            walk_matrix = await get_route_matrix(origins=origins, destinations=destinations, travel_mode=TravelMode.WALK)
            return build_graph_from_matrix(
                matrix=walk_matrix,
                travel_mode=TravelMode.WALK,
            )
        case TravelMode.TRANSIT:
            walk_matrix = await get_route_matrix(origins=origins, destinations=destinations, travel_mode=TravelMode.WALK)
            walk_graph = build_graph_from_matrix(
                matrix=walk_matrix,
                travel_mode=TravelMode.WALK
            )
            transit_matrix = await get_route_matrix(origins=origins, destinations=destinations, travel_mode=TravelMode.TRANSIT)
            transit_graph = build_graph_from_matrix(
                matrix=transit_matrix,
                travel_mode=TravelMode.TRANSIT
            )
            return merge_graphs_fastest([
                transit_graph,
                walk_graph,
            ])

def parse_duration_to_seconds(duration: str) -> int:
    return int(duration.replace("s", ""))


def build_graph_from_matrix(
    matrix: list[dict],
    travel_mode: TravelMode,
) -> Graph:
    """
    Builds a graph from the Google Maps route matrix response.
    """
    graph = Graph()

    for row in matrix:
        if row.get("condition") != "ROUTE_EXISTS" or \
            row["originIndex"] == row["destinationIndex"]:
            continue

        edge = Edge(
            origin_index=row["originIndex"],
            destination_index=row["destinationIndex"],
            duration_seconds=parse_duration_to_seconds(
                row["duration"]
            ),
            distance_meters=row.get("distanceMeters", 0),
            travel_mode=travel_mode,
        )

        graph.add_edge(edge)
    return graph


def merge_graphs_fastest(graphs: list[Graph]) -> Graph:
    """
    Connects multiple graphs into one.

    For each origin -> destination relation,
    the fastest travel option is selected.
    """

    final_graph = Graph()

    for graph in graphs:
        for origin, destinations in graph.graph.items():

            for destination, edge in destinations.items():

                existing_edge = final_graph.get_edge(
                    origin,
                    destination,
                )

                if existing_edge is None:
                    final_graph.add_edge(edge)
                    continue

                if (
                    edge.duration_seconds
                    < existing_edge.duration_seconds
                ):
                    final_graph.add_edge(edge)

    return final_graph
