import copy
import json
from argparse import ArgumentParser
from pathlib import Path

from PIL import Image


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('ref_json', type=str, help='Reference json file which will be duplicated for each image')
    parser.add_argument('frame_dir', type=str, help='Directory where the frames are located in')
    parser.add_argument('--ext', default='jpg', help='Image extension')
    parser.add_argument('--ignore', '-i', nargs='*', default=[], help='Labels to be ignored')
    args = parser.parse_args()

    json_dict_template = json.load(open(args.ref_json, 'rt'))
    json_dict_template['shapes'] = [shape for shape in json_dict_template['shapes'] if shape['label'] not in args.ignore]

    frames = Path(args.frame_dir).glob(f'*.{args.ext}')
    for frame_path in frames:
        print('-' * 30)
        print(f'Processing frame {frame_path}')
        json_dict = copy.deepcopy(json_dict_template)
        json_dict['imagePath'] = frame_path.name
        json_dict['imageWidth'], json_dict['imageHeight'] = Image.open(frame_path).size
        json_dict['imageData'] = None
        json.dump(json_dict, open(frame_path.with_suffix('.json'), 'wt', encoding='utf8'), ensure_ascii=False, indent=4)
