from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
import numpy as np
from PIL import Image , ImageTk
import pandas as pd
import pickle
from pathlib import Path


class Gui:
    def __init__(self):
        self.root = Tk()
        self.root.geometry("1000x800+150+10")
        self.root.title('Annotation Tool')
        self.root.resizable(False, False)
        self.bottomFrame = BottomFrame(self.root, self)
        self.topFrame = TopFrame(self.root, self)
        self.middleFrame = MiddleFrame(self.root, self)
        self.topFrame.pack(fill='x', padx=5, pady=5)
        self.middleFrame.pack(side=TOP, fill=BOTH)
        self.bottomFrame.pack(side=BOTTOM, fill='x')
        # bind keyboard events
        self.root.bind("<q>", self.save_and_exit)
        self.root.bind("<Left>", self.backward_image)
        self.root.bind("<Right>", self.forward_image)
        self.root.bind("<d>", self.delete_last_rect)
        self.root.bind("<s>", self.save_current_data)
        self.root.bind("<Visibility>", self.load_images_from_pickle)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        #self.middleFrame.get_images_for_annotation()
        self.root.mainloop()

    def set_top_label(self, msg):
        self.topFrame.set_label(msg)

    def get_working_folder(self):
        return self.topFrame.get_working_folder()

    def set_working_folder(self, folder):
        self.topFrame.set_working_folder(folder)

    def set_statusbar(self , msg , fcolor):
        self.bottomFrame.set_statusbar(msg,fcolor)

    def get_images_fo_annotation(self, toResize):
        self.middleFrame.get_images_for_annotation(toResize)

    def save_and_exit(self, n):
        self.bottomFrame.set_statusbar('Saving...', 'blue')
        self.middleFrame.save_current_data(n)
        self.root.destroy()
    def on_closing(self):
        self.save_and_exit(0)

    def backward_image(self, n):
        self.middleFrame.backward_image(n)

    def forward_image(self, n):
        self.middleFrame.forward_image(n)

    def delete_last_rect(self, n):
        self.middleFrame.delete_last_rect(n)

    def save_current_data(self, n):
        self.middleFrame.save_current_data(n)

    def load_images_from_pickle(self, n):
        self.root.unbind("<Visibility>")
        self.middleFrame.load_from_pickle()
        self.middleFrame.get_images_for_annotation(False)


class TopFrame(LabelFrame):
    def __init__(self, parent , gui):
        LabelFrame.__init__(self, parent)
        self.parent = parent
        self.gui = gui
        self.working_folder =''
        self.config(text='Working Image', height=50, width=50, bd='3')

        #button
        self.penFolderBtn = ttk.Button(self, text='Open Folder', command=self.select_working_folder)
        self.penFolderBtn.pack(side=LEFT, padx=5)

        # label
        self.image_lbl = Label(self, text='', width=200, anchor='w')
        self.image_lbl.pack(side=LEFT, padx=5)

    def select_working_folder(self):
        self.working_folder = filedialog.askdirectory()
        if self.working_folder == '':
            return
        self.gui.set_statusbar(self.working_folder, 'black')
        self.gui.get_images_fo_annotation(True)

    def set_label(self, msg):
        self.image_lbl['text'] = msg

    def get_working_folder(self):
        return self.working_folder

    def set_working_folder(self, folder):
        self.working_folder = folder
        self.gui.set_statusbar(folder, 'black')

class BottomFrame(Frame):
    def __init__(self, parent, gui):
        Frame.__init__(self, parent)
        self.parent = parent
        self.gui = gui

        # statusbar
        self.statusbar = Label(self, text='status', relief=SUNKEN, anchor='w')
        self.statusbar.pack(fill='x')
        
    def set_statusbar(self,msg,fcolor):
        self.statusbar.config(text = msg, fg= fcolor)


class MiddleFrame(Frame):
    def __init__(self, parent, gui):
        Frame.__init__(self, parent)
        self.parent = parent
        self.gui = gui
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.data = pd.DataFrame(columns=['directory','file','rectangles'])
        self.img = None
        self.photo = None
        self.img_id = -1

        self.files = []
        self.rects = []
        self.rects_ids = []
        self.curr_image = -1

        # canvas
        self.main_canvas = Canvas(self, width=1000, height=600)
        self.main_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        #mouse events
        self.main_canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.main_canvas.bind("<B1-Motion>", self.on_move_press)
        self.main_canvas.bind("<ButtonRelease-1>", self.on_button_release)
        #canvas events
        self.main_canvas.bind("<Configure>", self.resize_image)

    def get_images_for_annotation(self, toResize):
        folderName = self.gui.get_working_folder()
        if folderName == '':
            return

        folder = os.listdir(self.gui.get_working_folder())

        if folder == '':
            return
        self.files =[]
        for file in folder:
            if file.split('.')[-1].lower() in ['png','jpg','jpeg','gif'] :
                self.files.append(file)

        if len(self.files) == 0:
            self.gui.set_statusbar( 'No images found in ' + self.gui.get_working_folder(), 'red')
        else:
            self.curr_image = 0
            self.load_files_to_annotate(0, toResize)

    def load_files_to_annotate(self, idx, toResize):

        self.main_canvas.delete(ALL)
        self.rects = []
        self.rects_ids = []
        file_name = f'{self.gui.get_working_folder()}/{self.files[idx]}'
        self.img = Image.open(file_name)
        if toResize:
            self.img = self.img.resize((self.main_canvas.winfo_width(), self.main_canvas.winfo_height()), Image.ANTIALIAS)
        self.photo = ImageTk.PhotoImage(self.img, Image.ANTIALIAS)
        self.img_id = self.main_canvas.create_image(0, 0, anchor=NW, image=self.photo)

        self.gui.set_top_label(self.files[idx])
        self.gui.set_statusbar(self.gui.get_working_folder(), 'black')
        self.curr_image = idx

        self.create_rects_from_pickle()

    def resize_image(self, event):
        new_width = event.width
        new_height = event.height
        if self.img:
            self.img = self.img.resize((new_width, new_height), Image.ANTIALIAS)
            self.photo = ImageTk.PhotoImage(self.img)
            self.main_canvas.itemconfig(self.img_id, image=self.photo)

    def backward_image(self, n):
      if self.curr_image <= 0:
          self.gui.set_statusbar( 'No previous image found!', 'red')
      else:
          self.save_current_data(0)
         # self.check_annotation_to_save()
          self.load_files_to_annotate(self.curr_image - 1, True)

    def forward_image(self, n):
        self.save_current_data(0)
        #self.check_annotation_to_save()

        if self.curr_image >= 0 and self.curr_image + 1 < len(self.files) - 1:
            self.load_files_to_annotate(self.curr_image + 1 , True)
        else:
            self.gui.set_statusbar('No more images found!', 'red')

    def check_annotation_to_save(self):
       if len(self.rects_ids) > 0:
            answer = messagebox.askyesno(title='Save Annotation', message='Do you want to save your annotation?')
            if answer:
                self.save_current_data(0)

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = event.x
        self.start_y = event.y

        # create rectangle if not yet exist
        # if not self.rect:
        self.rect = self.main_canvas.create_rectangle(event.x, event.y, 1, 1, outline = 'red',width = 2, fill="")


    def on_move_press(self, event):
        curX, curY = (event.x, event.y)

        # expand rectangle as you drag the mouse
        self.main_canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        self.main_canvas.itemconfig(self.rect, outline = 'blue')
        rect_size = list(self.main_canvas.bbox(self.rect))
        self.rects.append(rect_size)
        self.rects_ids.append(self.rect)


    def delete_last_rect(self, n):
        if len(self.rects) == 0:
            return
        self.rects.pop()
        rect = self.rects_ids.pop()
        if rect > 0:
            self.main_canvas.delete(rect)


    def save_current_data(self, n):
        folderName = self.gui.get_working_folder()
        if folderName == '' :
            return
        file = self.files[self.curr_image]
        #file = f'{folderName}/{self.files[self.curr_image]}'
        if len(self.rects) == 0:
            i = self.data[(self.data['file'] == self.files[self.curr_image]) & (self.data['directory'] == folderName)].index
            if len(i) > 0:
                self.data.drop(i[0], axis=0, inplace=True)
                self.data.reset_index(drop=True)
                pd.to_pickle(self.data, 'results.pkl')
            return

        row = {'directory': folderName, 'file': file, 'rectangles': self.rects}

        #check if file in data
        i = self.data[(self.data['file'] == file) & (self.data['directory'] == folderName)].index
        if len(i) >0:
            self.data['rectangles'][i[0]] = self.rects
        else:
             self.data = self.data.append(row, ignore_index= True)
        #self.gui.set_statusbar("Saving annotations...", 'blue')
        pd.to_pickle(self.data,'results.pkl')
        #self.gui.set_statusbar("Annotations saved", 'black')
        self.rects = []
        self.rects_ids = []

    def load_from_pickle(self):
        if os.path.exists('results.pkl'):
            self.data = pd.read_pickle('results.pkl')
            if self.data.shape[0] == 0:
                return
            #assuming all files are from the same working folder
            folder = self.data['directory'][0]
            self.gui.set_working_folder(folder)

    def create_rects_from_pickle(self):
        folderName = self.gui.get_working_folder()
        if folderName == '':
            return
        file = self.files[self.curr_image]

        #find file in data
        rects = self.data[(self.data['file'] == file) & (self.data['directory'] == folderName)]['rectangles'].to_list()

        if len(rects) > 0 :
            rects = rects[0]
            for rect in rects:
                self.rect = self.main_canvas.create_rectangle(rect[0], rect[1] , rect[2] , rect[3], outline ='blue')
                self.rects_ids.append(self.rect)
                rect_size = list(self.main_canvas.bbox(self.rect))
                self.rects.append(rect_size)


if __name__ == '__main__':
    app = Gui()