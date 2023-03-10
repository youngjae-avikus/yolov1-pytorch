import torch
import os
from os.path import join as osp
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset
import albumentations as A

class VOCDataset(Dataset):
    def __init__(
        self, csv_file, img_dir, label_dir, S=7, B=2, C=20, transform=None
    ):
        self.annotations = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.label_dir = label_dir
        self.transform = transform
        self.S = S
        self.B = B
        self.C = C
        
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, index):
        label_path = osp(self.label_dir, self.annotations.iloc[index, 1])
        boxes = []
        with open(label_path) as f:
            for label in f.readlines():
                class_label, x, y, width, height = [
                    float(x) if float(x) != int(float(x)) else int(x)
                    for x in label.replace("\n", "").split()
                ]
                boxes.append([class_label, x, y, width, height])
                
        img_path = osp(self.img_dir, self.annotations.iloc[index, 0])
        image = Image.open(img_path)
        boxes = torch.tensor(boxes)
        
        if self.transform:
            image, boxes = self.transform(image, boxes)
            
        label_matrix = torch.zeros((self.S, self.S, self.C+5))
        
        for box in boxes:
            class_label, x, y, width, height = box.tolist()
            class_label = int(class_label)
            i, j = int(self.S * y), int(self.S * x) # i -> axis x, j -> axis y
            x_cell, y_cell = self.S * x - j, self.S * y - i
            
            """"
            We normalize the bounding box
            width and height by the image width and height so that they
            fall between 0 and 1. 
            """
            # width_cell, height_cell = (
            #     width * self.S,
            #     height * self.S
            # )
            width_cell, height_cell = (
                width,
                height 
            )
            
            # class_probability, objectness, bbox_coord
            if label_matrix[i, j, 20] == 0:
                label_matrix[i, j, 20] = 1
                label_matrix[i, j, class_label] = 1
                label_matrix[i, j, 21:25] = torch.tensor([x_cell, y_cell, width_cell, height_cell])
        
        return image, label_matrix
