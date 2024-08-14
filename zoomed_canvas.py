# fork of https://github.com/foobar167/junkyard/blob/master/zoom_advanced2.py
import tkinter as tk
# import customtkinter as ctk
import platform
from tkinter import ttk
from PIL import Image, ImageTk

OS = platform.system()


# class AutoScrollbar(ttk.Scrollbar):
#     ''' A scrollbar that hides itself if it's not needed.
#         Works only if you use the grid geometry manager '''
#
#     def set(self, lo, hi):
#         if float(lo) <= 0.0 and float(hi) >= 1.0:
#             self.grid_remove()
#         else:
#             self.grid()
#             ttk.Scrollbar.set(self, lo, hi)
#
#     def pack(self, **kw):
#         raise tk.TclError('Cannot use pack with this widget')
#
#     def place(self, **kw):
#         raise tk.TclError('Cannot use place with this widget')

class MimicWheelEvent:
    def __init__(self, x=1, y=1, delta=-120, num=5):
        self.x = x
        self.y = y
        self.delta = delta
        self.num = num


class ZoomAdvanced(ttk.Frame):
    ''' Advanced zoom of the image '''

    def __init__(self, master, path):
        ''' Initialize the main Frame '''
        ttk.Frame.__init__(self, master=master)
        # self.master.title('Zoom with mouse wheel')
        # self.master.geometry('800x600')
        # Vertical and horizontal scrollbars for canvas
        # self.vbar = AutoScrollbar(self.master, orient='vertical')
        # self.hbar = AutoScrollbar(self.master, orient='horizontal')
        # self.vbar.grid(row=0, column=1, sticky='ns')
        # self.hbar.grid(row=1, column=0, sticky='we')
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self.master, highlightthickness=0, )
        # self.canvas = ctk.CTkCanvas(master=self.master, highlightthickness=0, )
        # xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        # self.vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        # self.hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>', self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>', self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>', self.wheel)  # only with Linux, wheel scroll up
        self.image = Image.open(path)  # open image
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)

        self._center_view()
        self.show_image()

    def _center_view(self):

        self.canvas.xview(tk.SCROLL, 1, tk.UNITS)
        hor_step = self.canvas.canvasx(0)
        if hor_step == 0:  # or <=
            return

        self.canvas.xview(tk.SCROLL, -1, tk.UNITS)

        x1 = self.canvas.canvasx(self.canvas.winfo_width())

        hor_center = int(self.width // 2 - 1 / 2 * x1)
        num_hor_steps = int(hor_center // hor_step)

        if num_hor_steps:
            for _ in range(num_hor_steps):
                self.canvas.xview(tk.SCROLL, 1, tk.UNITS)

        self.canvas.xview(tk.SCROLL, 1, tk.UNITS)

        mouse_zoom_in = MimicWheelEvent(int(self.canvas.winfo_width() // 2))
        mouse_zoom_out = MimicWheelEvent(int(self.canvas.winfo_width() // 2), 1, delta=120, num=4)

        x0 = self.canvas.canvasx(0)

        for _ in range(5):
            self.wheel(mouse_zoom_in)

            a0 = self.canvas.coords(self.container)[0]

            if a0 >= x0:
                self.wheel(mouse_zoom_out)
                break

    def scroll_y(self, *args):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            pass  # Ok! Inside the image
        else:
            return  # zoom only inside image area
        scale = 1.0
        if OS == 'Darwin':
            if event.delta < 0:  # scroll down
                i = min(self.width, self.height)
                if int(i * self.imscale) < 30:
                    return  # image is less than 30 pixels
                self.imscale /= self.delta
                scale /= self.delta
            if event.delta > 0:  # scroll up
                i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
                if i < self.imscale:
                    return  # 1 pixel is bigger than the visible area
                self.imscale *= self.delta
                scale *= self.delta
        else:
            # Respond to Linux (event.num) or Windows (event.delta) wheel event
            if event.num == 5 or event.delta == -120:  # scroll down
                i = min(self.width, self.height)
                if int(i * self.imscale) < 30:
                    return  # image is less than 30 pixels
                self.imscale /= self.delta
                scale /= self.delta
            if event.num == 4 or event.delta == 120:  # scroll up
                i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
                if i < self.imscale:
                    return  # 1 pixel is bigger than the visible area
                self.imscale *= self.delta
                scale *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
        ''' Show image on the canvas '''
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        # Vertical part of the image is in the visible area
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        # Convert scroll rgion to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale),
                                     int(x2 / self.imscale), int(y2 / self.imscale)))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


if __name__ == "__main__":
    path = r'/home/tomasz/PycharmProjects/sekretarz/1/foto/62662726.png'  # place path to your image here
    root = tk.Tk()
    app = ZoomAdvanced(root, path=path)
    root.mainloop()
