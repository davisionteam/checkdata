import numpy as np

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def _order_points(pts):
    if len(pts) == 2:
        points = _order_points_2(pts)
    elif len(pts) == 4:
        points = _order_points_4(pts)
    else:
        raise ValueError('points must have the length of 2 or 4')
    return points

def _order_points_4(pts):
    assert len(pts) == 4, 'Length of points must be 4'
    tl = min(pts, key=lambda p: p[0] + p[1])
    br = max(pts, key=lambda p: p[0] + p[1])
    tr = max(pts, key=lambda p: p[0] - p[1])
    bl = min(pts, key=lambda p: p[0] - p[1])
    return [tl, tr, br, bl]


def _order_points_2(pts):
    assert len(pts) == 2, 'Length of points must be 2'
    a = [pts[0][0], pts[1][1]]
    b = [pts[1][0], pts[0][1]]
    return _order_points([pts[0], pts[1], a, b])


def flatten_coords(coords):
    coords = [int(val) for coord in coords for val in coord]
    return coords