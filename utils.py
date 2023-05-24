import os
from typing import *
import cv2
import numpy as np 
import csv
import collections
from tkinter import messagebox


def scan_dir(path: str) -> List[Tuple[str]]:
    """Scan all jpg image in a dir and return img-mask tuple

    Parameters
    ----------
    path : str
        image dir

    Returns
    -------
    List[Tuple[str]]
        [('1.jpg', '1-mask.jpg'])]
    """

    try:
        jpg_list = [os.path.join(path, i) for i in os.listdir(path) if any([i.endswith(j) for j in ('.jpg', 'png', '.bmp', 'jpeg')])]
    except:
        messagebox.showerror("", "No such path %s" % path)
    return [(jpg_list[i+1], jpg_list[i]) for i in range(0, len(jpg_list), 2)]

def mask2bbox(path: str) -> List[Tuple[int]]:
    """Load a mask image and return bbox

    Parameters
    ----------
    path : str
        path to mask image

    Returns
    -------
    List[Tuple[int]]
        [left, up, right, down]
    """

    # rgb 2 gray scale
    mask = cv2.imread(path, cv2.COLOR_BGR2GRAY)
    # gray scale to binary
    ret, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    if len(mask.shape) > 2:
        mask = mask.mean(-1).astype(np.int8)

    def mask_find_bboxs(mask):
        retval, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8) # connectivity参数的默认值为8
        stats = stats[stats[:,4].argsort()]
        return stats[:-1] # 排除最外层的连通图
    bboxs = mask_find_bboxs(mask)
    bboxs = [(b[0], b[1], b[0]+b[2], b[1]+b[3]) for b in bboxs]
    bboxs.sort()
    return bboxs

class AnnotationCenter:
    def __init__(self, write_path: str, labels: List[bool]) -> None:
        self.write_path = write_path
        self.labels = labels
        self.annotations = collections.defaultdict(lambda : (list(), list()))
        # try to load existing csv
        if os.path.isfile(self.write_path):
            try:
                with open(self.write_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for i, item in enumerate(reader):
                        if i == 0:
                            # if class names do not match
                            # give up
                            if [i.strip() for i in item] != ['image', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2'] + self.labels:
                                raise ValueError("CSV Error", "CSV Column name not compatiable")
                        else:
                            if not item: continue
                            image_name = item[0]
                            bbox = tuple([int(i) for i in item[1:5]])
                            labels = [int(i) for i in item[5:]]
                            self.annotations[image_name][0].append(bbox)
                            self.annotations[image_name][1].append(labels)
            except:
                messagebox.showerror("CSV Error", "CSV Exist but cannot be loaded, Overwriting...")

    def add(self, image_name_tuple: Tuple[str], bbox: List[Tuple[int]], labels_list: List[Tuple[bool]]):
        """Add bbox labels for an image

        Parameters
        ----------
        image_name_tuple : Tuple[str]
            image_path, mask_path
        bbox : List[Tuple[int]]
            list of bbox
        labels_list : List[Tuple[bool]]
            list of labels
        """
        image_name = image_name_tuple[0]
        image_name = os.path.split(image_name)[-1]
        self.annotations[image_name] = bbox[:], labels_list[:]
        self.save()
    
    def save(self):
        """save all labels
        """
        with open(self.write_path, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['image', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2'] + self.labels)
            f.write('\n')
            for i in sorted(self.annotations.keys()):
                for bbox, labels in zip(*self.annotations[i]):
                    writer.writerow([i] + [*bbox] + labels)
                    f.write('\n')

    def query(self, image_name_tuple: Tuple[str]):
        """query if labels of an image exist in memory, if not return empty template

        Parameters
        ----------
        image_name_tuple : Tuple[str]
            image_path, mask_path

        Returns
        -------
        List[Tuple[int]], List[List[bool]]
            bbox_list, label_list
        """
        image_name, mask_name = image_name_tuple
        image_name = os.path.split(image_name)[-1]
        if image_name in self.annotations:
            return self.annotations.get(image_name, (None, None))
        else:
            bbox_list = mask2bbox(mask_name)
            label_list = [[0 for _ in range(len(self.labels))] for _ in range(len(bbox_list))]
            return bbox_list, label_list