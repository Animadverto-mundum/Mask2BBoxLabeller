import os
os.environ['OPENCV_IO_MAX_IMAGE_PIXELS']='200000000000'
import shutil
import csv
import os.path as osp
import collections
import tkinter as tk
import tqdm
from tkinter import messagebox
from tkinter.filedialog import askdirectory, askopenfilename
import cv2


def do():
    img_dir = img_dir_text.get()
    mask_dir = mask_dir_text.get()
    output_img_dir = output_img_dir_text.get()
    output_mask_dir = output_mask_dir_text.get()
    csv_path = csv_path_text.get()
    
    flag = False
    if not osp.isdir(img_dir):
        messagebox.showerror("", "不存在图像路径 %s。" %  img_dir)
        raise ValueError("不存在图像路径 %s。" %  img_dir)
    if not osp.isdir(mask_dir):
        messagebox.showerror("", "不存在遮罩路径 %s。" %  mask_dir)
        raise ValueError("不存在遮罩路径 %s。" %  mask_dir)
    if not osp.isfile(csv_path):
        messagebox.showerror("", "不存在文件 %s。" %  csv_path)
        raise ValueError("不存在文件 %s。" %  csv_path)
    if osp.isdir(output_img_dir) and len(os.listdir(output_img_dir)):
        messagebox.showerror("", "输出图像目录 %s 不为空。" %  output_img_dir)
        flag = True
    if osp.isdir(output_mask_dir) and len(os.listdir(output_mask_dir)):
        messagebox.showerror("", "输出遮罩目录 %s 不为空。" %  output_mask_dir)
        flag = True
    if flag:
        ok = messagebox.askokcancel("", "部分输出目录不为空，是否继续？")
        if not ok:
            messagebox.showerror("", "已终止操作")
            return
    if not osp.isdir(output_img_dir):
        os.makedirs(output_img_dir)
    if not osp.isdir(output_mask_dir):
        os.makedirs(output_mask_dir)
    
    annotation_dict = collections.defaultdict(list)

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, item in enumerate(reader):
            if i == 0 or not item:
                continue
            labels = [int(i) for i in item[5:]]
            annotation_dict[item[0].strip()].append(any(labels))
    
    messagebox.showinfo("", "%d张已标记。将进行拷贝，程序可能假死，请耐心等待" % (sum([all(i) for i in annotation_dict.values()])))
    
    all_img_name = set()
    all_mask_name = {}
    for i, j, k in tqdm.tqdm(os.walk(img_dir)):
        for f in k:
            if any(f.lower().endswith(ext_name) for ext_name in ('.jpg', 'png', '.bmp', 'jpeg')):
                if f.split('.')[-2].endswith("_mask") or f.split('.')[-2].endswith("-mask"):
                    continue
                all_img_name.add('.'.join(f.split('.')[:-1]))

    for i, j, k in tqdm.tqdm(os.walk(mask_dir)):
        for f in k:
            if any(f.lower().endswith(ext_name) for ext_name in ('.jpg', 'png', '.bmp', 'jpeg')):
                if not (f.split('.')[-2].endswith("_mask") or f.split('.')[-2].endswith("-mask")):
                    continue
                all_mask_name['.'.join(f.replace("_mask", "").replace("-mask", "").split('.')[:-1])] = osp.join(i, f)

    for i, j, k in tqdm.tqdm(os.walk(mask_dir)):
        for f in k:
            if any(f.lower().endswith(ext_name) for ext_name in ('.jpg', 'png', '.bmp', 'jpeg')):
                if not (f.split('.')[-2].endswith("_mask") or f.split('.')[-2].endswith("-mask")):
                    continue
                base_img_name = f.replace("_mask", "").replace("-mask", "")
                if not (all(annotation_dict[base_img_name]) and len(annotation_dict[base_img_name])):
                    # if corressponding not in all img name
                    if '.'.join(base_img_name.split('.')[:-1]) not in all_img_name:
                        continue
                    # if not all bbox is annotated
                    if not len(annotation_dict[base_img_name]):
                        # if this one has not been logged into csv
                        # we need to determine whether the mask is empty
                        img = cv2.imread(osp.join(i, f))
                        if img.sum() < 10:
                            # if the mask is empty
                            # remove mask from all_mask_name
                            del all_mask_name['.'.join(f.replace("_mask", "").replace("-mask", "").split('.')[:-1])]
                            # and skip copying
                            continue
                    folder = osp.relpath(i, mask_dir)
                    to_dir = osp.join(output_mask_dir, folder)
                    if not osp.isdir(to_dir):
                        os.makedirs(to_dir)
                    shutil.copy(osp.join(i, f), osp.join(to_dir, f))
    
    for i, j, k in tqdm.tqdm(os.walk(img_dir)):
        for f in k:
            if any(f.lower().endswith(ext_name) for ext_name in ('.jpg', 'png', '.bmp', 'jpeg')):
                if f.split('.')[-2].endswith("_mask") or f.split('.')[-2].endswith("-mask"):
                    continue
                base_img_name = f
                if not (all(annotation_dict[base_img_name]) and len(annotation_dict[base_img_name])):
                    # if not all bbox is annotated
                    if '.'.join(base_img_name.split('.')[:-1]) in all_mask_name:
                        # if there does exist a mask
                        # those black mask has been removed
                        folder = osp.relpath(i, img_dir)
                        to_dir = osp.join(output_img_dir, folder)
                        if not osp.isdir(to_dir):
                            os.makedirs(to_dir)
                        shutil.copy(osp.join(i, f), osp.join(to_dir, f))
    
    messagebox.showinfo("", f"已过滤所有已标记样本，图像目录为{output_img_dir}，遮罩目录为{output_mask_dir}")

root = tk.Tk()
root.title('选择清理目录')
initial_width = 500
initial_height = 550
root.geometry(f"{initial_width}x{initial_height}+{(root.winfo_screenwidth()-initial_width)//2}+{(root.winfo_screenheight()-initial_height)//2}")

tk.Label(root, text='图像目录(命名如:1.jpg)').pack()
img_dir_text = tk.StringVar()
img_dir_textbox = tk.Entry(root, textvariable=img_dir_text)
img_dir_textbox.pack()
img_dir_button = tk.Button(root, text='选择目录', command=lambda: img_dir_text.set(askdirectory()))
img_dir_button.pack()

tk.Label(root, text='遮罩目录(命名如:1-mask.jpg)').pack()
mask_dir_text = tk.StringVar()
mask_dir_textbox = tk.Entry(root, textvariable=mask_dir_text)
mask_dir_textbox.pack()
mask_dir_button = tk.Button(root, text='选择目录', command=lambda: mask_dir_text.set(askdirectory()))
mask_dir_button.pack()

tk.Label(root, text='anno.csv路径').pack()
csv_path_text = tk.StringVar()
csv_path_textbox = tk.Entry(root, textvariable=csv_path_text)
csv_path_textbox.pack()
csv_path_button = tk.Button(root, text='选择文件', command=lambda: csv_path_text.set(askopenfilename(filetypes=[("Default", "anno.csv"), ("Any CSV", "*.csv")])))
csv_path_button.pack()

tk.Label(root, text='输出图像目录 默认新建img文件夹').pack()
output_img_dir_text = tk.StringVar()
output_img_dir_textbox = tk.Entry(root, textvariable=output_img_dir_text)
output_img_dir_textbox.pack()
output_img_dir_button = tk.Button(root, text='选择目录', command=lambda: output_img_dir_text.set(osp.join(askdirectory(), "img")))
output_img_dir_button.pack()

tk.Label(root, text='输出遮罩目录 默认新建msk文件夹').pack()
output_mask_dir_text = tk.StringVar()
output_mask_dir_textbox = tk.Entry(root, textvariable=output_mask_dir_text)
output_mask_dir_textbox.pack()
output_mask_dir_button = tk.Button(root, text='选择目录', command=lambda: output_mask_dir_text.set(osp.join(askdirectory(), "msk")))
output_mask_dir_button.pack()

do_button = tk.Button(root, text='确认', command=do)
do_button.pack(pady=10)

root.mainloop()


