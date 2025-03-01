import torch
import os
import pandas as pd
import yaml
import scipy.io as sio
import json

from dataloaders import make_data_loader
from deeplab3.config.defaults import get_cfg_defaults

def get_all_models(directory):
    # traverse root directory, and list directories as dirs and files as files
    model_configs = []
    for root, dirs, files in os.walk(directory):
        path = root.split(os.sep)
        for file in files:
            if file == "parameters.txt.yaml" or file == "parameters.yaml":
                model_configs.append(os.path.join(root, file))
    return model_configs

def flatten_cfg(cfg_dict, prefix=None):
    flattened = {}
    for key, value in cfg_dict.items():
        if prefix is None:
            prefixed_key = key
        else:
            prefixed_key = "{}.{}".format(prefix, key)

        if not isinstance(value, dict):
            flattened[prefixed_key] = value
        else:
            flattened.update(flatten_cfg(value, prefixed_key))
    return flattened

# Throws FileNotFoundException
def match_cfg_versions(cfg_filepath):
    cfg = get_cfg_defaults()
    with open(cfg_filepath, 'r') as f:
        model_cfg = yaml.load(f)
        model_cfg = flatten_cfg(model_cfg)
    for key, value in model_cfg.items():
        if not key.startswith("CHECKPOINT"):
            try:
                if key == "TRAIN.EVAL_INTERVAL":
                    value = float(value)
                if key == "DATASET.USE_DEPTH":
                    key = "DATASET.MODE"
                    if value:
                        value = "RGBD"
                    else:
                        value = "RGB"
                if key == "DATASET.CHANNELS":
                    key = "MODEL.INPUT_CHANNELS"
                if key == "DATASET.DARKEN" and isinstance(value, bool):
                    key = "DATASET.DARKEN.DARKEN"

                cfg.merge_from_list([key, value])
            except ValueError as e:
                print(e)
            except AssertionError as e:
                print(e)

    if cfg.DATASET.ROOT.startswith("datasets"):
        cfg.merge_from_list(['DATASET.ROOT', "../" + cfg.DATASET.ROOT])
    if cfg.DATASET.NAME == "sunrgbd":
        cfg.DATASET.ROOT = "../datasets/SUNRGBD/"
    elif cfg.DATASET.NAME == "scenenet":
        cfg.DATASET.ROOT = "../datasets/scenenet/"

    return cfg
