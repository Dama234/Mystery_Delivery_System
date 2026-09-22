"""
Visualizer Module for FastBox Mystery Delivery System
Provides ASCII-based spatial mapping and delivery route visualization.
"""

from typing import Dict, List, Tuple, Any


def render_ascii_map(
    warehouses: Dict[str, Tuple[float, float]],
    agents: Dict[str, Tuple[float, float]],
    packages: List[Dict[str, Any]],
    width: int = 60,
    height: int = 22,
) -> str:
    """
    Renders a 2D ASCII spatial map showing warehouses, agents, and package destinations.
    
    Markers:
      [W#] : Warehouse
      <A#> : Agent starting location
      P#   : Package destination
    """
    # Collect all points to determine bounding box
    all_points = list(warehouses.values()) + list(agents.values()) + [tuple(p["destination"]) for p in packages]
    if not all_points:
        return "No coordinate data to visualize."

    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    # Add small margin
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)

    # Create grid of characters
    grid = [[" " for _ in range(width)] for _ in range(height)]

    def to_grid(x: float, y: float) -> Tuple[int, int]:
        # y is inverted for terminal output (0 at top)
        col = int(((x - min_x) / span_x) * (width - 1))
        row = int(((max_y - y) / span_y) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        return col, row

    def place_text(text: str, col: int, row: int):
        start = max(0, min(col, width - len(text)))
        for i, ch in enumerate(text):
            if start + i < width:
                grid[row][start + i] = ch

    # 1. Place package destinations
    for p in packages:
        c, r = to_grid(p["destination"][0], p["destination"][1])
        place_text(p["id"], c, r)

    # 2. Place warehouses
    for wid, loc in warehouses.items():
        c, r = to_grid(loc[0], loc[1])
        place_text(f"[{wid}]", c, r)

    # 3. Place agents
    for aid, loc in agents.items():
        c, r = to_grid(loc[0], loc[1])
        place_text(f"<{aid}>", c, r)

    lines = []
    lines.append("+" + "-" * width + "+")
    lines.append(f"| FastBox 2D ASCII Territory Map ({width}x{height})".ljust(width + 1) + "|")
    lines.append(f"| Bounds: X=[{min_x:.0f}, {max_x:.0f}], Y=[{min_y:.0f}, {max_y:.0f}]".ljust(width + 1) + "|")
    lines.append("+" + "-" * width + "+")
    for r in range(height):
        lines.append("|" + "".join(grid[r]) + "|")
    lines.append("+" + "-" * width + "+")
    lines.append("Legend: <A#> = Agent Start | [W#] = Warehouse | P# = Package Destination")
    return "\n".join(lines)


def render_route_summary(
    agent_id: str,
    start_pos: Tuple[float, float],
    routes: List[Dict[str, Any]],
) -> str:
    """
    Renders an ASCII text-based path sequence for a specific agent's deliveries.
    """
    if not routes:
        return f"Agent {agent_id}: No deliveries assigned (Idle at {start_pos})."

    output = [f"=== Agent {agent_id} Delivery Route Flow ==="]
    curr = f"Start <{agent_id}> ({start_pos[0]:.1f}, {start_pos[1]:.1f})"

    for i, leg in enumerate(routes, 1):
        pkg_id = leg["package_id"]
        w_id = leg["warehouse_id"]
        w_pos = leg["warehouse_pos"]
        d_pos = leg["destination_pos"]
        leg_dist = leg["leg_distance"]

        step = (
            f"  Step {i}: {curr}\n"
            f"          |-- travel to {w_id} ({w_pos[0]:.1f}, {w_pos[1]:.1f}) [dist: {leg['dist_to_wh']:.2f}]\n"
            f"          |-- pick up package {pkg_id}\n"
            f"          |-- deliver to destination ({d_pos[0]:.1f}, {d_pos[1]:.1f}) [dist: {leg['dist_to_dest']:.2f}]\n"
            f"          => Leg Subtotal: {leg_dist:.2f}"
        )
        output.append(step)
        curr = f"Destination of {pkg_id} ({d_pos[0]:.1f}, {d_pos[1]:.1f})"

    return "\n".join(output)
