import json
from argparse import ArgumentParser
from pathlib import Path

import yaml


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('modify_config', type=str, help='YAML file defines configuration dictionary')
    parser.add_argument('input_dir', type=str, help='Directory where the json files are located in')
    args = parser.parse_args()

    modify_config = yaml.safe_load(open(args.modify_config, 'rt'))
    json_paths = Path(args.input_dir).glob(f'*.json')
    for json_path in json_paths:
        print('-' * 30)
        print(f'Processing {json_path}')
        json_dict = json.load(open(json_path, 'rt'))
        for shape in json_dict['shapes']:
            shape['label'] = modify_config['rename'].get(shape['label'], shape['label'])
        json.dump(json_dict, open(json_path, 'wt', encoding='utf8'), ensure_ascii=False, indent=4)
