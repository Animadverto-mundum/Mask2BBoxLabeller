import tkinter as tk
from tkinter import Tk, Canvas, Frame, Checkbutton, Button
from PIL import ImageTk, Image
from tkinter.filedialog import askdirectory
from tkinter import messagebox
import utils
import os

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


def refresh(event=None):
    # repaint windows

    global image
    global crop_image
    global load_crop_image

    # pregress details on the title
    root.title("Mask2BBox by @git-thinker | Image: %d/%d | Item: %d / %d" % (image_ptr+1, len(image_list), bbox_ptr+1, len(bbox_list)))

    # resize the main canvas
    if event:
        canvas_width = event.width
        canvas_height = event.height
    else:
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
    canvas.config(
        width=canvas_width - small_canvas_width,
        height=canvas_height - checkboxes_height - bottom_height
    )
    
    # remove image and rectangles on the main canvas to repaint due to resizing
    canvas.delete("all")
    width_factor = canvas.winfo_width() / original_img.size[0]
    height_factor = canvas.winfo_height() / original_img.size[1]
    image = original_img.resize((canvas.winfo_width(), canvas.winfo_height()))
    image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor='nw', image=image)

    # repaint bbox rectangles
    for i, (x1, y1, x2, y2) in enumerate(bbox_list):
        if i < bbox_ptr:
            # visited
            outline='gray'
        elif i == bbox_ptr:
            # working on
            outline='red'
        else:
            # todo
            outline='black'
        canvas.create_rectangle(x1 * width_factor, y1 * height_factor, x2 * width_factor, y2 * height_factor, outline=outline, width=1)
    
    # remove preview on small canvas to load new preview
    small_canvas.delete("all")
    crop_image = original_img.crop(bbox_list[bbox_ptr]).resize((small_canvas.winfo_width(), small_canvas.winfo_height()))
    load_crop_image = ImageTk.PhotoImage(crop_image)
    small_canvas.create_image(0, 0, anchor='nw', image = load_crop_image)

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
    refresh()

def next_image():
    global image_ptr
    global bbox_ptr
    save_checker()
    bbox_ptr = 0
    annotation_center.add(image_list[image_ptr], bbox_list, label_list)
    image_ptr += 1
    if image_ptr == len(image_list): image_ptr = len(image_list) - 1
    prepare_image()
    refresh()

def load_checker():
    # load checkbox status from memory to GUI
    for i in range(len(checkboxes)):
        if label_list[bbox_ptr][i]:
            checkboxes[i].select()
        else:
            checkboxes[i].deselect()

def save_checker():
    # save checkbox status from GUI to memory
    for i in range(len(checkboxes)):
        label_list[bbox_ptr][i] = int(checks[i].get())

def prepare_image():
    # load an image
    global original_img
    global bbox_list, label_list
    original_img = Image.open(image_list[image_ptr][0])
    bbox_list, label_list = annotation_center.query(image_list[image_ptr])
    load_checker()



messagebox.showinfo("","Choose Your Image Folder in (ACSII).\nClass names shall be stored in class.csv\nOutput will be in anno.csv")
imaeg_dir = askdirectory()

try:
    with open(os.path.join(imaeg_dir, 'class.csv'), 'r', encoding='utf-8') as f:
        labels = [i.strip() for i in f.readline().strip().split(',')]
        labels.sort()
except:
    messagebox.showerror("Missing class setting", "class.csv not found")

annotation_center = utils.AnnotationCenter(os.path.join(imaeg_dir, 'anno.csv'), labels)
image_list = utils.scan_dir(imaeg_dir)

# root windows
root = Tk()
root.title("Mask2BBox by @git-thinker")

# initial windows size
initial_width = 800
initial_height = 600
root.geometry(f"{initial_width}x{initial_height}")

# set size for components
small_canvas_width = 200
small_canvas_height = 200
checkboxes_height = 200
bottom_height = 50

# main canvas
canvas = Canvas(root, bg="white")
canvas.pack(side="left", fill="both", expand=True)
canvas.bind("<Configure>", refresh)


# small canvas for bbox preview
small_canvas = Canvas(root, bg="lightgray", width=small_canvas_width, height=small_canvas_height)
small_canvas.pack(side="top", anchor="ne")
small_canvas.bind("<Configure>", refresh)

# label checkboxes
checkbox_frame = Frame(root)
checkbox_frame.pack(side="right", fill="y", padx=10, pady=10)

checkboxes = []
checks = []

for i in labels:
    check = tk.BooleanVar()
    checkbox = Checkbutton(checkbox_frame, text=i, variable=check)
    checkbox.pack(anchor="w")
    checks.append(check)
    checkboxes.append(checkbox)


# button for prev / next
button_frame = Frame(root)
button_frame.pack(side="right", anchor="se", padx=10, pady=10)

buttons_width = 16

button1 = Button(button_frame, text="<- BBox", width=int(buttons_width/2), command=prev_bbox)
button1.grid(row=0, column=0)

button2 = Button(button_frame, text="BBox ->", width=int(buttons_width/2), command=next_bbox)
button2.grid(row=0, column=1, padx=10)

button3 = Button(button_frame, text="<- Img", width=int(buttons_width/2), command=prev_image)
button3.grid(row=1, column=0, pady=10)

button4 = Button(button_frame, text="Img ->", width=int(buttons_width/2), command=next_image)
button4.grid(row=1, column=1, padx=10, pady=10)

# pre_loading image
prepare_image()

# main loop
root.mainloop()