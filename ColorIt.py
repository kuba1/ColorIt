#!/usr/bin/python2.7

#import clewn.vim as vim; vim.pdb()
import wx
import sqlite3
import os

class ImagePanel(wx.Panel):
    """ Describes a panel that contains an image being operated on """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(0,0), style=wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        
        #saves parent window for further reference
        self.parent = parent
        #this bitmap is a place to draw everything
        self.bitmap = None

        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnUp)
        self.Bind(wx.EVT_MOTION, self.OnDrag)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        #copy backgraund from parent window
        self.SetBackgroundStyle(parent.GetBackgroundStyle())

        #this is a color chosen by a user, initialised with black
        self.color = wx.Color(0, 0, 0, 255)

        #indicates whether pancil tool is active
        self.pencil = False

        self.forx = None
        self.fory = None

        self.Show(False)
        
    def SetPencil(self, active):
        self.pencil = active
        
    def OnDrag(self, e):
        if e.Dragging() and self.pencil:
            self.OnClick(e)

    def OnUp(self, e):
        self.forx = None
        self.fory = None

    def OnPaint(self, e):
        if self.bitmap:
            wx.BufferedPaintDC(self, self.bitmap)
        e.Skip()

    def OnClick(self, e):
        """ invoked when user clicks on an image """
        #if image is present
        if not self.bitmap:
            return

        mdc = wx.BufferedDC(wx.ClientDC(self), self.bitmap)

        x = e.GetX()
        y = e.GetY()

        if self.pencil:
            if self.forx and self.fory:
                pen = wx.Pen(wx.Color(0, 0, 0), 2)
                mdc.SetPen(pen)

                mdc.DrawLine(self.forx, self.fory, x, y)
        else:
            pixel = mdc.GetPixel(x,y)
            if pixel != wx.Color(0, 0, 0, 255):
                #use flood fill in clicked point
                brush = wx.Brush(self.color)
                mdc.SetBrush(brush)        
                mdc.SetBackground(brush)        
            
                #get pixel color in slicked spot so you know where to fill
                mdc.FloodFill(x, y, pixel)

        self.forx = x
        self.fory = y

    def SetImage(self, bitmap):
        """ set new image bitmap (mostly from main window) """
        self.bitmap = bitmap
        self.SetSize(bitmap.GetSize())
        self.Show(True)
        self.Refresh()

    def GetImage(self):
        """ return current image bitmap """
        return self.bitmap

    def SetColor(self, color):
        """ set the color with which to fill """
        self.color = color

class MainFrame(wx.Frame):
    """ Main application window """
    def __init__(self):
        wx.Frame.__init__(self, None, title='ColorIt', size=(400,400))

        self.palette = []
        self.paletteIds = []
        self.selectedColor = None

        self.imagePanel = ImagePanel(self)

        self.hSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        #sqlite database containing all the displayed strings
        co = sqlite3.connect('language.db')
        cu = co.cursor()
        cu.execute('select * from data')
        self.db = cu.fetchall()
        cu.close()
        co.close()

        #palette database
        co = sqlite3.connect('palette.db')
        cu = co.cursor()
        cu.execute('select * from colors')
        colors = cu.fetchall()
        cu.close()
        co.close()
        
        i = 0
        for c in colors:
            self.palette.append((colors[i][1], colors[i][2], colors[i][3]))
            i = i + 1

        self.fileMenu = wx.Menu()
        self.mopen = wx.MenuItem(self.fileMenu, wx.ID_OPEN, self.db[0][0])
        self.mopen.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN))
        self.fileMenu.AppendItem(self.mopen)

        self.msave = wx.MenuItem(self.fileMenu, wx.ID_SAVE, self.db[1][0])
        self.msave.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FLOPPY))
        self.fileMenu.AppendItem(self.msave)

        self.mexit = wx.MenuItem(self.fileMenu, wx.ID_EXIT, self.db[2][0])
        self.mexit.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_QUIT))
        self.fileMenu.AppendItem(self.mexit)

        self.Bind(wx.EVT_MENU, self.OnExit, self.mexit)
        self.Bind(wx.EVT_MENU, self.OnOpen, self.mopen)
        self.Bind(wx.EVT_MENU, self.OnSave, self.msave)

        self.hSizer.AddStretchSpacer()
        self.hSizer.Add(self.imagePanel, 0, wx.CENTER)
        self.hSizer.AddStretchSpacer()
        
        self.optionsMenu = wx.Menu()
        self.mreload = self.optionsMenu.Append(wx.ID_ANY, self.db[3][0])
        self.mmono = self.optionsMenu.Append(wx.ID_ANY, "Mono")
        self.mabout = self.optionsMenu.Append(wx.ID_ANY, self.db[13][0])
        self.Bind(wx.EVT_MENU, self.OnReload, self.mreload)
        self.Bind(wx.EVT_MENU, self.OnMono, self.mmono)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.mabout)

        self.menuBar = wx.MenuBar()
        self.menuBar.Append(self.fileMenu, self.db[4][0])
        self.menuBar.Append(self.optionsMenu, self.db[5][0])

        self.SetMenuBar(self.menuBar)

        self.toolBar = self.CreateToolBar()
        self.SetInitialPalette()
        self.toolBar.Realize()
        
        self.statusBar = self.CreateStatusBar()
        
        self.SetSizer(self.hSizer)
    
    def OnPaint(self, e):
        """ makes sure to refresh the image panel """
        dc = wx.PaintDC(self)
        self.imagePanel.Refresh()

    def OnPencil(self, e):
        image = wx.Image('glyphicons_030_pencil.png', wx.BITMAP_TYPE_PNG)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 1)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 24)
        cursor = wx.CursorFromImage(image)
        self.SetCursor(cursor)
        wx.SetCursor(cursor)
        self.imagePanel.SetPencil(True)
        
    def OnOpen(self, e):
        """ invoked when "Open" menu option has been selected """
        wldcrd = 'ALL (*.*)|*.*|BMP (*.bmp)|*.bmp|JPG (*.jpg)|*.jpg|PNG (*.png)|*.png'
        wldcrd = wldcrd + '|PCX (*.pcx)|*.pcx|PNM (*.pnm)|*.pnm|TIFF (*.tiff)|*.tiff|ICO|*.ico|CUR|*.cur'
        dialog = wx.FileDialog(self, style=wx.FD_OPEN, wildcard=wldcrd)
        dialog.ShowModal()
        path = dialog.GetPath()
        if len(path) != 0:
            if wx.Image.CanRead(path):
                self.image = wx.Image(path)
                self.image.ConvertAlphaToMask()
                self.Scale(self.image)
                self.imagePanel.SetImage(self.image.ConvertToBitmap())
                self.hSizer.SetItemMinSize(1, self.image.GetSize())
                self.statusBar.SetStatusText(self.db[8][0] + path)
                self.Layout()
            else:
                w = wx.MessageDialog(self, self.db[9][0], self.db[7][0], wx.OK)
                w.ShowModal()
                self.statusBar.SetStatusText(self.db[10][0] + path)
        self.Refresh()

    def OnMono(self, e):
        wx.Quantize.Quantize(self.image, self.image, desiredNoColours=2)
        cols = self.GetColors(self.image)
        white = cols[0]
        self.image = self.image.ConvertToMono(white.Red(), white.Green(), white.Blue())
        self.imagePanel.SetImage(self.image.ConvertToBitmap())

    def OnSave(self, e):
        """ invoked when "Save" menu option has been selected """
        try:
            image = self.imagePanel.GetImage().ConvertToImage()
        except AttributeError:
            w = wx.MessageDialog(self, self.db[6][0], self.db[7][0], wx.OK)
            w.ShowModal()
            return
        except:
            w = wx.MessageDialog(self, self.db[11][0], self.db[7][0], wx.OK)
            w.ShowModal()
            return
        dialog = wx.FileDialog(self, style=wx.FD_SAVE)
        dialog.ShowModal()
        path = dialog.GetPath()
        ext = os.path.splitext(path)[1].lower()
        if ext == '.bmp':
            image.SaveFile(path, wx.BITMAP_TYPE_BMP)
        elif ext == '.jpg' or ext == '.jpeg':
            image.SaveFile(path, wx.BITMAP_TYPE_JPEG)
        elif ext == '.png':
            image.SaveFile(path, wx.BITMAP_TYPE_PNG)
        elif ext == '.pcx':
            image.SaveFile(path, wx.BITMAP_TYPE_PCX)
        elif ext == '.pnm':
            image.SaveFile(path, wx.BITMAP_TYPE_PNM)
        elif ext == '.tiff':
            image.SaveFile(path, wx.BITMAP_TYPE_XPM)
        elif ext == '.ico':
            image.SaveFile(path, wx.BITMAP_TYPE_ICO)
        elif ext == '.cur':
            image.SaveFile(path, wx.BITMAP_TYPE_CUR)
        else:
            image.SaveFile(path + '.bmp', wx.BITMAP_TYPE_BMP)

    def OnExit(self, e):
        """ invoked when "Exit" menu option has been selected """
        i = 0;
        co = sqlite3.connect('palette.db')
        cu = co.cursor()
        cu.execute('delete from colors')
        co.commit()
        for c in self.palette:
            cu.execute('insert into colors values (' +\
                    str(i) + ',' + str(c[0]) + ',' + str(c[1]) + ',' + str(c[2]) + ')')
            i = i + 1
        co.commit()
        cu.close()
        co.close()
        
        self.Destroy()
        exit()
       
    def OnAbout(self, e):
        """ invoked when "About" menu option has been selected """
        #dialog = wx.MessageDialog(self, "Author: JG", "Credits", wx.OK)
        info = wx.AboutDialogInfo()
        info.SetName('ColorIt')
        info.SetVersion('1.0')
        info.SetDescription('Simple coloring tool\n\nicons and cursors from:\n\nwww.glyphicons.com')
        info.SetCopyright('(c) Jakub Golebiewski\n\nLicence: GPL\n\nif you make any useful changes\n' +\
                'please send them to\nkubusg@gmail.com')
        info.AddDeveloper('Jakub Golebiewski\n\nkubusg@gmail.com')

        dialog = wx.AboutBox(info)

    def OnReload(self, e):
        """ invoked when "Reload" menu option has been selected """
        try:
            self.image
        except:
            return
        self.imagePanel.SetImage(self.image.ConvertToBitmap())
    
    def GetBitmap(self, color, x, y):
        """ returns empty bitmap of (x,y) size and background color specified by color """
        bitmap = wx.EmptyBitmap(x, y)
        dc = wx.MemoryDC(bitmap)
        dc.SetBackground(wx.Brush(color))
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)
        return bitmap

    def GetCursor(self, color):
        """ get cursor object with specified properties """
        image = wx.Image('glyphicons_234_brush.png', wx.BITMAP_TYPE_PNG)
        r, g, b = color.Get(False)
        image.SetRGBRect((0,10,10,13), r, g, b)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 1)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 22)
        cursor = wx.CursorFromImage(image)
        return cursor

    def SetInitialPalette(self):
        """ set 16 colors palette as displayed palette """
        col = self.toolBar.AddLabelTool(wx.ID_ANY, '',\
                wx.BitmapFromImage(wx.Image('glyphicons_327_sampler.png', wx.BITMAP_TYPE_PNG)))
        self.Bind(wx.EVT_TOOL, self.OnPalette, col)
        pls = self.toolBar.AddLabelTool(wx.ID_ANY, '',\
                wx.BitmapFromImage(wx.Image('glyphicons_190_circle_plus.png', wx.BITMAP_TYPE_PNG)))
        self.Bind(wx.EVT_TOOL, self.OnColorAdd, pls)
        mns = self.toolBar.AddLabelTool(wx.ID_ANY, '',\
                wx.BitmapFromImage(wx.Image('glyphicons_191_circle_minus.png', wx.BITMAP_TYPE_PNG)))
        self.Bind(wx.EVT_TOOL, self.OnColorRemove, mns)
        pen = self.toolBar.AddRadioLabelTool(wx.ID_ANY, '',\
                wx.BitmapFromImage(wx.Image('glyphicons_030_pencil.png', wx.BITMAP_TYPE_PNG)))
        self.Bind(wx.EVT_TOOL, self.OnPencil, pen)
        self.OnPencil(None)

        for c in self.palette:
            tool = self.toolBar.AddRadioLabelTool(wx.ID_ANY, '', self.GetBitmap(c, 35, 35))
            self.paletteIds.append(tool)
            self.Bind(wx.EVT_TOOL, self.OnColorChange, tool)

    def OnColorAdd(self, e):
        tool = self.toolBar.AddRadioLabelTool(wx.ID_ANY, '', self.GetBitmap(wx.Color(255, 255, 255), 35, 35))
        self.paletteIds.append(tool)
        self.palette.append((255, 255, 255))
        self.Bind(wx.EVT_TOOL, self.OnColorChange, tool)
        self.toolBar.Realize()

    def OnColorRemove(self, e):
        dlg = wx.MessageDialog(self, 'Na pewno usunac?', '???', wx.YES_NO)
        ret = dlg.ShowModal()
        if ret == wx.ID_YES:
            self.toolBar.RemoveTool(self.paletteIds[self.selectedColor].GetId())
            self.paletteIds.pop(self.selectedColor)
            self.palette.pop(self.selectedColor)
            num = len(self.palette) - 1
            if self.selectedColor > num:
                self.selectedColor = num
                self.toolBar.ToggleTool(self.paletteIds[num].GetId(), True)
                self.OnColorChange(self.paletteIds[num])
            else:
                self.toolBar.ToggleTool(self.paletteIds[self.selectedColor].GetId(), True)
                self.OnColorChange(self.paletteIds[self.selectedColor])
            self.toolBar.Realize()

    def OnPalette(self, e):
        dlg = wx.ColourDialog(self)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            col = dlg.GetColourData().GetColour()
            if col.Red() == 0 and col.Green() == 0 and col.Blue() == 0:
                col = wx.Color(1, 0, 0, 255)
            self.palette[self.selectedColor] = (col.Red(), col.Green(), col.Blue())
            tool = self.paletteIds[self.selectedColor]
            tool.SetNormalBitmap(self.GetBitmap(wx.Color(col.Red(), col.Green(), col.Blue()), 35, 35))
            #switch to force redraw
            self.toolBar.ToggleTool(self.paletteIds[self.selectedColor].GetId(), False)
            self.toolBar.ToggleTool(self.paletteIds[self.selectedColor].GetId(), True)
            self.toolBar.Realize()
            self.OnColorChange(self.paletteIds[self.selectedColor])

    def OnColorChange(self, e):
        """ invoked when user clicks a tool bar button to change selected color """
        num = 0
        #we need to search all the tool bar button's ids to find the clicked one
        for i in self.paletteIds:
            if i.GetId() == e.GetId():
                #when found, set its color as selected color
                r, g, b = self.palette[num]
                color = wx.Color(r, g, b, 255)
                self.imagePanel.SetPencil(False)
                self.imagePanel.SetColor(color)
                cursor = self.GetCursor(color)
                self.SetCursor(cursor)
                wx.SetCursor(cursor)
                self.selectedColor = num
            num = num + 1

    def GetColors(self, image):
        x, y = image.GetSize()
        color1 = wx.Color(image.GetRed(0,0), image.GetGreen(0,0), image.GetBlue(0,0))
        for i in range(0, x):
            for j in range(0, y):
                color2 = wx.Color(image.GetRed(i,j), image.GetGreen(i,j), image.GetBlue(i,j))
                if color1 != color2:
                    s1 = color1.Red() + color1.Green() + color1.Blue()
                    s2 = color2.Red() + color2.Green() + color2.Blue()
                    if s1 > s2:
                        return (color1, color2)
                    else:
                        return (color2, color1)

    def Scale(self, image):
        imSize = image.GetSize()
        imw = float(imSize[0])
        imh = float(imSize[1])
        frSize = self.GetClientSize()
        frw = float(frSize[0])
        frh = float(frSize[1])
        hScale = frw/imw
        vScale = frh/imh
        if vScale < hScale:
            image.Rescale(int(vScale*imw), int(frh), wx.IMAGE_QUALITY_HIGH)
        else:
            image.Rescale(int(frw), int(hScale*imh), wx.IMAGE_QUALITY_HIGH)

app = wx.App(False)
wnd = MainFrame()
wnd.Show(True)
wnd.Maximize(True)
app.MainLoop()
