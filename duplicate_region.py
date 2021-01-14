import copy
import json
from argparse import ArgumentParser
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Union
import cv2
from shapely import geometry
import numpy as np
from PIL import Image


def compute_intersection_ratio(polyA, polyB):
    ratio = 0.
    polyA = geometry.Polygon(polyA)
    polyB = geometry.Polygon(polyB)
    if polyA.intersects(polyB):
        ratio = polyA.intersection(polyB).area / polyB.area
    return ratio


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = np.array(pts).sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def find_shape(label_name: str, shapes: List[Dict]) -> Union[Dict, List[Dict]]:
    results: List[Dict] = []
    for shape in shapes:
        if shape['label'] == label_name:
            results.append(shape)

    return results


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('ref_json', type=str, help='Reference json file which will be duplicated for each image')
    parser.add_argument('region_path', type=str, default=None, help='Path to the file containing region configurations')
    parser.add_argument('json_dir', type=str,
                        help='Directory where the frames are located in')
    parser.add_argument('--ext', default='jpg', help='Image extension')
    args = parser.parse_args()

    region_path = Path(args.region_path)
    if region_path.suffix == '.yaml':
        import yaml
        region_config = yaml.safe_load(open(region_path, 'rt'))
    elif region_path.suffix == '.json':
        import json
        region_config = json.load(open(region_path, 'rt'))
    else:
        print('Unsupport file type. Should be .yaml or .json')
        exit(-1)

    assert 'names' in region_config.keys()

    json_ref = json.load(open(args.ref_json, 'rt'))

    if 'ignore' in region_config.keys():
        json_ref['shapes'] = [shape for shape in json_ref['shapes'] if shape['label'] not in region_config['ignore']]

    json_dir = Path(args.json_dir)
    for json_path in json_dir.glob(f'*.json'):
        print(f'Processing {json_path}')
        json_new = json.load(open(json_path, 'rt'))

        src: Optional[List[Tuple[float]]] = None
        dst: Optional[List[Tuple[float]]] = None

        region_news = [shape for shape in json_new['shapes'] if shape['label'] in region_config['names']]
        json_new['shapes'] = copy.deepcopy(region_news)
        for region_new in region_news:
            found = False
            for region_ref in json_ref['shapes']:
                if region_ref['label'] != region_new['label']:
                    continue
                found = True
                region_src = order_points(region_ref['points'])
                region_dst = order_points(region_new['points'])

                src_array = np.array(region_src, np.float32).reshape(-1, 2)
                dst_array = np.array(region_dst, np.float32).reshape(-1, 2)
                M: np.ndarray = cv2.getPerspectiveTransform(src_array, dst_array)

                for shape in json_ref['shapes']:
                    if shape['label'] == region_new['label']:
                        continue

                    shape_points = order_points(shape['points'])
                    ratio = compute_intersection_ratio(region_src, shape_points)
                    if ratio >= 0.6:
                        src_array = np.array(shape_points, dtype=np.float32).reshape(-1, 2)
                        dst_array = cv2.perspectiveTransform(np.array([src_array]), M).squeeze(0)
                        dst = dst_array.tolist()

                        dst_shape = copy.deepcopy(shape)
                        dst_shape['points'] = dst

                        json_new['shapes'].append(dst_shape)
        image_path = json_path.with_suffix(f'.{args.ext}')
        json_new['imagePath'] = image_path.name
        json_new['imageWidth'], json_new['imageHeight'] = Image.open(image_path).size
        json_new['imageData'] = None
        json.dump(json_new, open(json_path, 'wt', encoding='utf8'), ensure_ascii=False, indent=4)
