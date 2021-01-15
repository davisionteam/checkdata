import copy
import json
from argparse import ArgumentParser
from json.decoder import JSONDecoder
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Union
import cv2
from shapely import geometry
import numpy as np
from PIL import Image


def order_points(points):
    if len(points) == 4:
        rect = np.zeros((4, 2), dtype="float32")
        s = np.array(points).sum(axis=1)
        rect[0] = points[np.argmin(s)]
        rect[2] = points[np.argmax(s)]
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]
        rect[3] = points[np.argmax(diff)]
    else:
        rect = points
    return rect


class Shape():
    def __init__(self, shape):
        self.label = shape['label']
        self.points = shape['points']
        self.type = shape['shape_type']
        self.group_id = shape['group_id']
        self.flags = shape['flags']

    def __repr__(self) -> str:
        return f'Shape({self.label}, {self.points})'

    def is_child(self, parent: 'Shape'):
        ratio = 0.
        polyA = geometry.Polygon(parent.points)
        if len(self.points) == 4:
            polyB = geometry.Polygon(self.points)
            if polyA.intersects(polyB):
                ratio = polyA.intersection(polyB).area / polyB.area
        elif len(self.points) == 2:
            line = geometry.LineString(self.points)
            if line.intersection(polyA).within(polyA):
                ratio = 1.0
        return ratio >= 0.6


    def astype(self, othertype):
        assert othertype in ['line', 'polygon', 'rectangle']
        if len(self.points) == 2 and self.type == 'rectangle' and othertype == 'polygon':
            p1, p2 = self.points
            x1 = min(p1[0], p2[0])
            y1 = min(p1[1], p2[1])
            x2 = max(p1[0], p2[0])
            y2 = max(p1[1], p2[1])
            self.points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            self.type = othertype
        else:
            raise ValueError()

    def find_transform(self, other: 'Shape'):
        assert len(self.points) == 4 and len(other.points) == 4

        region_src = order_points(self.points)
        region_dst = order_points(other.points)

        src_array = np.array(region_src, np.float32).reshape(-1, 2)
        dst_array = np.array(region_dst, np.float32).reshape(-1, 2)
        M: np.ndarray = cv2.getPerspectiveTransform(src_array, dst_array)
        return M

    def map(self, transform: np.ndarray):
        src_points = order_points(self.points)
        src_array = np.array(src_points, dtype=np.float32).reshape(-1, 2)
        dst_array = cv2.perspectiveTransform(np.array([src_array]), transform).squeeze(0)
        dst = dst_array.tolist()
        return Shape({
            'label': self.label,
            'points': dst,
            'shape_type': self.type,
            'flags': self.flags,
            'group_id': self.group_id
        })


class Annotation():
    def __init__(self, image_path, image_height, image_width, shapes):
        self.image_path = image_path
        self.image_width = image_width
        self.image_height = image_height
        self.shapes = list(map(Shape, shapes))

    def __iter__(self):
        for shape in self.shapes:
            yield shape

    def __len__(self):
        return len(self.shapes)

    def keep_labels(self, labels: List[str]):
        self.shapes = [shape for shape in self.shapes if shape.label in labels]

    def remove_labels(self, labels: List[str]):
        self.shapes = [shape for shape in self.shapes if shape.label not in labels]

    @classmethod
    def parse_from_labelme(cls, json_path):
        json_dict = json.load(open(json_path, 'rt'))
        return cls(json_dict['imagePath'],
                   json_dict['imageHeight'],
                   json_dict['imageWidth'],
                   json_dict['shapes'])

    def __repr__(self) -> str:
        shapes = self.shapes[:5]
        repr = f'Annotation({self.image_path}, {self.image_width}x{self.image_height}, {len(self.shapes)}):\n'
        for shape in shapes:
            repr += f'\t{shape.__repr__()}\n'
        if len(shapes) > 5:
            repr += '...\n'
        return repr


    def find(self, labels: List[str], first: bool = False):
        results: List[Shape] = []
        for shape in self.shapes:
            if shape.label in labels:
                results.append(shape)

        if len(results) == 0 and first:
            return None
        elif first:
            return results[0]
        else:
            return results

    def find_childs(self, ref_shape):
        childs: List[Shape] = [shape for shape in self.shapes if shape.is_child(ref_shape) and shape != ref_shape]
        return childs

    def add_shapes(self, shapes: List[Shape]):
        self.shapes.extend(shapes)

    def remove_shapes(self, shapes: List[Shape]):
        self.shapes = [shape for shape in self.shapes if shape not in shapes]

    def to_json(self, path: Path):
        # print(json.dumps(anno_new.__dict__, default=serializer))
        json.dump(self, open(path, 'wt', encoding='utf8'), ensure_ascii=False, indent=4, default=labelme_serializer)


def labelme_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, Annotation):
        d = {
            'version': '4.5.6',
            'flags': {},
            'shapes': obj.shapes,
            'imageData': None,
            'imagePath': obj.image_path,
            'imageHeight': obj.image_height,
            'imageWidth': obj.image_width,
        }
        return d

    if isinstance(obj, Shape):
        d = {
            'label': obj.label,
            'points': obj.points,
            "group_id": obj.group_id,
            "shape_type": obj.type,
            "flags": obj.flags,
        }
        return d

    return obj.__dict__


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

    back_anno_ref: Annotation = Annotation.parse_from_labelme(args.ref_json)
    if region_config.get('ignore', None) is not None:
        back_anno_ref.remove_labels(region_config['ignore'])

    json_dir = Path(args.json_dir)
    for json_path in json_dir.glob(f'*.json'):
        print(f'Processing {json_path}')
        anno_ref: Annotation = copy.deepcopy(back_anno_ref)
        anno_new: Annotation = Annotation.parse_from_labelme(json_path)

        region_news = anno_new.find(region_config['names'])
        if len(region_news) == 0:
            print('Empty region annotations!')
            continue

        anno_new.keep_labels(region_config['names'])

        for region_new in region_news:
            region_ref: Shape = anno_ref.find([region_new.label], first=True)
            if region_ref is None:
                print(f'Not found corresponding region name = {region_new.label} annotation in reference. Skip')
                continue

            transform = region_ref.find_transform(region_new)
            region_ref_childs = anno_ref.find_childs(region_ref)
            region_new_childs = [child.map(transform) for child in region_ref_childs]
            anno_new.add_shapes(region_new_childs)
            # remove to avoid duplication
            anno_ref.remove_shapes(region_ref_childs)

        if 'depend' in region_config.keys():
            dependence = region_config['depend']
            for depend_region_name, depend_labels in dependence.items():
                region_ref = anno_ref.find(depend_region_name, first=True)
                if region_ref is None:
                    print(f'Unknow depend region name in reference, name = {depend_region_name}. Skip!')
                    continue
                region_new = anno_new.find(depend_region_name, first=True)
                if region_new is None:
                    print(f'Unknow depend region name in new, name = {depend_region_name}. Skip!')
                    continue
                transform = region_ref.find_transform(region_new)
                shapes = anno_ref.find(depend_labels)
                mapped_shapes = [shape.map(transform) for shape in shapes]
                anno_new.add_shapes(mapped_shapes)
                anno_ref.remove_shapes(shapes)

        anno_new.to_json(json_path)
