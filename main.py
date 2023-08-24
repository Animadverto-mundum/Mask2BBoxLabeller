import tkinter as tk
from tkinter import Tk, Canvas, Frame, Checkbutton, Button
from PIL import ImageTk, Image
from tkinter.filedialog import askdirectory
from tkinter import ttk
import utils
import os
import sys

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

labels = None
image_root = None
image_list = None
image_ptr = 0
bbox_list = None
bbox_ptr = 0
label_list = None
original_img = None
crop_image = None
load_crop_image = None
area_image = None
load_area_image = None


def refresh(event=None):
    # repaint windows

    global image
    global crop_image
    global load_crop_image
    global area_image
    global load_area_image

    # pregress details on the title
    root.title("Mask2BBox | Image: %d/%d | Item: %d / %d | %s" % (image_ptr+1, len(image_list), bbox_ptr+1, len(bbox_list), image_list[image_ptr][0]))

    # resize the main canvas
    if event is not None and event != 0:
        canvas_width = event.width
        canvas_height = event.height
    else:
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
    
    canvas.config(
        width=canvas_width - area_canvas_width,
        height=canvas_height - checkboxes_height - bottom_height
    )
    
    # remove image and rectangles on the main canvas to repaint due to resizing
    canvas.delete("all")
    # resize image without distortion
    if original_img.size[0] > original_img.size[1]:
        width_factor = canvas.winfo_width() / original_img.size[0]
        height_factor = width_factor
    else:
        height_factor = canvas.winfo_height() / original_img.size[1]
        width_factor = height_factor

    if event is not None:
        image = original_img.resize((int(width_factor*original_img.size[0]), int(height_factor*original_img.size[1])))
        image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor='nw', image=image)

    # repaint bbox rectangles
    for i, (x1, y1, x2, y2) in enumerate(bbox_list):
        if i == bbox_ptr:
            # working on
            outline='white'
        elif any(label_list[i]):
            # visited
            outline='green'
        else:
            # todo
            outline='red'
        canvas.create_rectangle(x1 * width_factor, y1 * height_factor, x2 * width_factor, y2 * height_factor, outline=outline, width=1)
    
    # remove preview on area canvas to load new preview
    
    area_canvas.delete("all")
    if 0 <= bbox_ptr < len(bbox_list):
        area_l, area_u, area_r, area_d = bbox_list[bbox_ptr]
        area_factor = 2
        area_l, area_r = (area_l + area_r) // 2 - (area_r - area_l) * area_factor // 2, (area_l + area_r) // 2 + (area_r - area_l) * area_factor // 2
        area_u, area_d = (area_d + area_u) // 2 - (area_d - area_u) * area_factor // 2, (area_d + area_u) // 2 + (area_d - area_u) * area_factor // 2
        area_l, area_r, area_u, area_d = max(0, int(area_l)), min(original_img.size[0], int(area_r)), max(0, int(area_u)), min(original_img.size[1], int(area_d))
        area_image = original_img.crop((area_l, area_u, area_r, area_d)).resize((area_canvas.winfo_width(), area_canvas.winfo_height()))
        load_area_image = ImageTk.PhotoImage(area_image)
        area_canvas.create_image(0, 0, anchor='nw', image = load_area_image)


def prev_bbox():
    global bbox_ptr
    save_checker()
    bbox_ptr -= 1
    if bbox_ptr < 0: bbox_ptr = 0
    load_checker()
    refresh()

def next_bbox():
    global bbox_ptr
    save_checker()
    bbox_ptr += 1
    if bbox_ptr == len(bbox_list): bbox_ptr = len(bbox_list) - 1
    load_checker()
    refresh()

def prev_image():
    global image_ptr
    global bbox_ptr
    save_checker()
    bbox_ptr = 0
    annotation_center.add(image_list[image_ptr], bbox_list, label_list)
    image_ptr -= 1
    if image_ptr < 0: image_ptr = 0
    prepare_image()
    refresh(0)

def next_image():
    global image_ptr
    global bbox_ptr
    save_checker()
    bbox_ptr = 0
    annotation_center.add(image_list[image_ptr], bbox_list, label_list)
    image_ptr += 1
    if image_ptr == len(image_list): image_ptr = len(image_list) - 1
    prepare_image()
    refresh(0)

def load_checker():
    # load checkbox status from memory to GUI
    for i in range(len(checkboxes)):
        if 0 <= bbox_ptr < len(label_list):
            if label_list[bbox_ptr][i]:
                checks[i].set(True)
            else:
                checks[i].set(False)
    check2joint()

def save_checker():
    # save checkbox status from GUI to memory
    for i in range(len(checkboxes)):
        if 0 <= bbox_ptr < len(label_list):
            label_list[bbox_ptr][i] = int(checks[i].get())

def prepare_image():
    # load an image
    global original_img
    global bbox_list, label_list
    original_img = Image.open(image_list[image_ptr][0])
    bbox_list, label_list = annotation_center.query(image_list[image_ptr])
    load_checker()


query_win = Tk()
query_win.title('选择工作目录')
initial_width = 400
initial_height = 350
query_win.geometry(f"{initial_width}x{initial_height}+{(query_win.winfo_screenwidth()-initial_width)//2}+{(query_win.winfo_screenheight()-initial_height)//2}")

tk.Label(query_win, text='图像目录(命名如:1.jpg)').pack()
img_dir_text = tk.StringVar()
img_dir_textbox = tk.Entry(query_win, textvariable=img_dir_text)
img_dir_textbox.pack()
img_dir_button = tk.Button(query_win, text='选择目录', command=lambda: img_dir_text.set(askdirectory()))
img_dir_button.pack()

tk.Label(query_win, text='遮罩目录(命名如:1-mask.jpg)').pack()
mask_dir_text = tk.StringVar()
mask_dir_textbox = tk.Entry(query_win, textvariable=mask_dir_text)
mask_dir_textbox.pack()
mask_dir_button = tk.Button(query_win, text='选择目录', command=lambda: mask_dir_text.set(askdirectory()))
mask_dir_button.pack()

tk.Label(query_win, text='输出目录(将尝试载入/写入anno.csv) | 切换图片自动写入').pack()
output_dir_text = tk.StringVar()
output_dir_textbox = tk.Entry(query_win, textvariable=output_dir_text)
output_dir_textbox.pack()
output_dir_button = tk.Button(query_win, text='选择目录', command=lambda: output_dir_text.set(askdirectory()))
output_dir_button.pack()

def quit_query():
    global image_dir, mask_dir, output_dir, image_list
    image_dir = img_dir_text.get()
    mask_dir = mask_dir_text.get()
    output_dir = output_dir_text.get()
    image_list = utils.scan_from_2dir(image_dir, mask_dir, resize_check_var.get(), query_win)
    query_win.destroy()

resize_check_var = tk.BooleanVar()
resize_check = tk.Checkbutton(query_win, text='缩放图片', variable=resize_check_var)
resize_check.pack(pady=10)
output_dir_button = tk.Button(query_win, text='确认', command=quit_query)
output_dir_button.pack(pady=10)
query_win.protocol('WM_DELETE_WINDOW', lambda: (query_win.destroy(),sys.exit()))
query_win.mainloop()


# root windows
root = Tk()
root.title("Mask2BBox by @git-thinker")

# initial windows size
initial_width = 1920
initial_height = 1020
root.geometry(f"{initial_width}x{initial_height}")

label_text = iter(['病变类型:', '外观:', '分布:', '位置:', '荧光强度:'])
label = [
    [
        'G（小球）',
        'T（小管）',
        'PTC（管周毛细血管）',
        'A（动脉）',
        '错误分割',
    ],
    [
        '颗粒状',
        '线性',
        '团块状',
        '类线性',
    ],
    [
        '弥漫',
        '局灶',
        '球性',
        '节段',
        '阴性',
    ],
    [
        '毛细血管袢',
        '系膜区',
        '血管壁',
        '包曼囊壁',
        '肾小管基底膜',
        '上皮细胞胞浆',
        '管型（含蛋白管型）',
    ],
    [
        '1+',
        '2+',
        '3+',
        'trace',
        '0',
    ],
]


labels = [item for sublist in label for item in (sublist if isinstance(sublist, list) else [sublist])]

annotation_center = utils.AnnotationCenter(os.path.join(output_dir, 'anno.csv'), labels)



# set size for components
area_canvas_width = 450
area_canvas_height = 450
checkboxes_height = 200
bottom_height = 50

# main canvas
canvas = Canvas(root, bg="white")
canvas.pack(side="left", fill="both", expand=True)
canvas.bind("<Configure>", refresh)

middle = tk.Frame(root)
middle.pack(side='left')

tk.Label(middle, text='对象邻域').grid(row=0, column=0)



# area canvas for bbox preview

area_canvas = Canvas(middle, bg="lightgray", width=area_canvas_width, height=area_canvas_height)
area_canvas.grid(row=1, column=0)
area_canvas.bind("<Configure>", refresh)


def clearAllcheck():
    for check in checks:
        check.set(False)
    for joint in joints:
        joint.set(-1)

buttons_width = 16

# button for prev / next
button_frame = Frame(middle)
button_frame.grid(row=2, column=0, columnspan=2)

button0 = Button(button_frame, text="Clear(Q)", width=int(buttons_width/2), command=clearAllcheck)
button0.grid(row=0, column=0)

button1 = Button(button_frame, text="<- BBox(A)", width=int(buttons_width/2), command=prev_bbox)
button1.grid(row=1, column=0, pady=10)


button2 = Button(button_frame, text="BBox ->(D)", width=int(buttons_width/2), command=next_bbox)
button2.grid(row=1, column=1, padx=10)


button3 = Button(button_frame, text="<- Img(W)", width=int(buttons_width/2), command=prev_image)
button3.grid(row=2, column=0, pady=10)


button4 = Button(button_frame, text="Img(S) ->", width=int(buttons_width/2), command=next_image)
button4.grid(row=2, column=1, padx=10, pady=10)

def shortcut(event):
    char = event.char.lower()
    if char == 'w':
        prev_image()
    elif char == 's':
        next_image() 
    elif char == 'a':
        prev_bbox()
    elif char == 'd':
        next_bbox()
    elif char == 'q':
        clearAllcheck()       

root.bind('<Key>', shortcut)


# label checkboxes
checkbox_frame = Frame(root)
checkbox_frame.pack(anchor="n", fill="y", padx=10, pady=10)

checkboxes = []
checks = []
joints = []

def renew_checkbox():
    joint2check()

def joint2check():
    for check in checks:
        check.set(False)
    s = [i.get() for i in joints ]
    for joint in joints:
        if joint.get() != -1:
            checks[joint.get()].set(True)
    
def check2joint():
    label_map = []
    for i, l in enumerate(label):
        label_map.extend([i] * len(l))
    for joint in joints:
        joint.set(-1)
    
    for i, check in enumerate(checks):
        if check.get():
            joints[label_map[i]].set(i)

# unique id for each checkbox
i = 0
for l in label:
    joint = tk.IntVar(value=-1)
    tk.Label(checkbox_frame, text=next(label_text), pady=-3, font=("Times",10,"bold")).pack(anchor="w")
    for j in l:
        check = tk.BooleanVar()
        if j in label[0]:
            checkbox = tk.Radiobutton(checkbox_frame, text=j, variable=joint, value=i, command=renew_checkbox, pady=-2)
        else:
            checkbox = tk.Checkbutton(checkbox_frame, text=j, variable=check, command=check2joint, pady=-2)
        checkbox.pack(anchor="w")
        checks.append(check)
        checkboxes.append(checkbox)
        i += 1
    sep = ttk.Separator(checkbox_frame, orient='horizontal')
    sep.pack(fill='x')
    joints.append(joint)


# pre_loading image
prepare_image()

def root_distroy():
    next_image()
    root.destroy()

# save current bbox before exit
root.protocol('WM_DELETE_WINDOW', root_distroy)

# main loop
root.mainloop()