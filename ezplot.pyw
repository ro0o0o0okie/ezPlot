# -*- coding: utf-8 -*-
"""
******************************
* Filename: ezplot.pyw
* Author: RayN
* Created on 9/26/2015
******************************
"""
import os
import sys
import json
import warnings
import pandas as pd
import matplotlib as plt
import qdarkstyle

from matplotlib import style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets, QtGui

import gui_base as gui


__appname__ = 'EzPlot'
__version__ = "2.0.0"
__author__  = 'RayN'
__config__ = os.path.join(os.path.dirname(__file__), 'config.json')


def GetPlotSyles():
    return ['default', 'classic'] + sorted(
        style for style in plt.style.available if style != 'classic')
        

class EzPlot(QtWidgets.QMainWindow):
    def __init__(self, config:dict=None):
        super(EzPlot, self).__init__()
        self.config = {
            'WindowSize' : (1200, 800),
            'SplitterState' : None,
            'DataFile' : None,
            'Style' : 'default',
            'FigWidth' : 5, 'FigHeight' : 4, 
            'FlagClear' : True, 'FlagGrid' : True, 'FlagLegend' : True,
            'FontSize' : 11,
        }
        if config:
            self.config.update(config)
        
        self.setStyleSheet('font-size: 10pt; font-family: microsoft yahei;') # overide font
        self.setWindowTitle(__appname__ +'  v'+__version__ + '  by ' + __author__)
        self.resize(*self.config['WindowSize'])
        self.center()
        
        self.dataframe = None # init dataFrame
        
        self.createMenu()
        self.createLoaderPanel()
        self.createFigurePanel()

        self.main_frame = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_frame.addWidget(self.panel_loader)
        self.main_frame.addWidget(self.panel_figure)
        self.setCentralWidget(self.main_frame)
        
        stateStr = self.config['SplitterState']
        if stateStr is not None:
            state = QtCore.QByteArray().fromHex(bytes(stateStr, encoding='ascii'))
            self.main_frame.restoreState(state)
        else:
            self.main_frame.setStretchFactor(0, 1)
            self.main_frame.setStretchFactor(1, 3)
        
        status = self.statusBar()
        status.setSizeGripEnabled(True)
        status.showMessage("Ready", 5000)
    
    
    def saveConfig(self, fn):
        self.config = {
            'WindowSize'    : (self.frameGeometry().width(), self.frameGeometry().height()),
            'SplitterState' : str(self.main_frame.saveState().toHex(), encoding='ascii'),
            'DataFile'      : self.datafile.getValue(),
            'Style'         : self.combo_style.getValue(),
            'FigWidth'      : self.editor_fig_width.getValue(), 
            'FigHeight'     : self.editor_fig_height.getValue(), 
            'FlagClear'     : self.chkbox_clear.isChecked(), 
            'FlagGrid'      : self.chkbox_grid.isChecked(), 
            'FlagLegend'    : self.chkbox_legend.isChecked(),
            'FontSize'      : self.editor_fontsz.getValue(),
        }
        json.dump(self.config, open(fn,'w'), indent=4)
        
    
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 
                    'Message', 
                    "Are you sure you want to exit?", 
                    QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No )
    
        if reply == QtWidgets.QMessageBox.Yes:
            self.saveConfig(__config__)
            event.accept()
        else:
            event.ignore()
            
            
    def showEvent(self, event):
        # update fig size text when show
        fsize = self.fig.get_size_inches()
        self.setEditorFigureSize(fsize[0], fsize[1])
    
    
    def resizeEvent(self, event):
        # update fig size text when resized
        fsize = self.fig.get_size_inches()
        self.setEditorFigureSize(fsize[0], fsize[1])
    
    
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def createLoaderPanel(self):
        ''' create data file loader panel '''
        self.panel_loader = QtWidgets.QWidget()
        self.datafile = gui.File(label="Data", default=None, 
                                 dlgDir=os.path.dirname(self.config['DataFile']), 
                                 minWidth=120, callbackFunc=self.loadFile)
        self.editor_x_axis = gui.ComboBox(textList=[], label='X Axis', connectFunc=self.updatePlot)
        self.editor_y_axis = gui.List(items=[], multiple=True, label="Y Axis", editable=True, 
                                      connectFunc=self.updatePlot, editCallbackFunc=self.onColumnLabelChanged)
        self.editor_legend = gui.Text(default=None, label='Legend',
                                      tooltip='multiple labels can be seperated by comma')
        self.editor_legend.editingFinished.connect(self.setCustomLegend)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.datafile.labelText, 1, 0)
        grid.addWidget(self.datafile.text, 1, 1)
        grid.addWidget(self.datafile.button, 1, 2)

        grid.addWidget(self.editor_x_axis.labelText, 2, 0)
        grid.addWidget(self.editor_x_axis, 2, 1, 1, 2)

        grid.addWidget(self.editor_y_axis.labelText, 3, 0)
        grid.addWidget(self.editor_y_axis, 3, 1, 4, 2)

        grid.addWidget(self.editor_legend.labelText, 7, 0)
        grid.addWidget(self.editor_legend, 7, 1, 1, 2)

        self.panel_loader.setLayout(grid)
    
    
    def onColumnLabelChanged(self, newItemText:str, oldItemText:str):
        if self.dataframe is not None:
            # rename df columns
            self.dataframe.rename(columns={oldItemText: newItemText}, inplace=True)
            # update x axis combo items
            xidx = self.editor_x_axis.currentIndex()
            colNames = self.dataframe.columns.tolist()
            self.editor_x_axis.resetItems(textList=colNames, default=colNames[xidx])
    

    def loadFile(self):
        """ load data into dataFrame """
        fn = self.datafile.getValue()
        if os.path.isfile(fn):
            df = None
            for readfunc in (pd.read_csv, pd.read_excel, pd.read_pickle, pd.read_table):
                try:
                    df = readfunc(fn)
                    break 
                except:
                    pass
                
            if df is None or df.empty:
                self.statusBar().showMessage('Read data file failed! (supported formats: CSV, Pickle, Excel)', 8000)
            else:
                df.reset_index(level=None, inplace=True)
                self.dataframe = df
                colNames = df.columns.tolist()
                self.editor_y_axis.resetItems(colNames)
                self.editor_x_axis.resetItems(colNames, default=colNames[0])
                self.statusBar().showMessage('Data loaded successfully.', 5000)
        else:
            self.statusBar().showMessage('File does not exist', 5000)

    
    def createFigurePanel(self):
        ''' create matplotlib figure panel '''
        self.panel_figure = QtWidgets.QWidget()
        
        # Create the mpl Figure and FigCanvas objects.
        style.use(self.config['Style'])
        figsize = (self.config['FigWidth'], self.config['FigHeight'])
        
        self.fig = Figure(figsize)
        self.canvas = FigureCanvas(figure=self.fig)
        self.canvas.setParent(self.panel_figure)
        self.axes = self.fig.add_subplot(111)
        # Create the navigation toolbar, tied to the canvas
        toolbar = NavigationToolbar(self.canvas, self.panel_figure)

        # figure control widgets
        self.botton_draw = gui.MakePushButton('Plot', minWidth=120, clickFunc=self.updatePlot)
        self.chkbox_clear = gui.CheckBox(default=self.config['FlagClear'], label='Clear')
        self.chkbox_grid = gui.CheckBox(default=self.config['FlagGrid'], label='Grid')
        self.chkbox_legend = gui.CheckBox(default=self.config['FlagLegend'], label='Legend')
        self.editor_fig_width = gui.Float(low=1, high=64, step=0.01, digits=2, default=figsize[0], label="FigWidth")
        self.editor_fig_height = gui.Float(low=1, high=64, step=0.01, digits=2, default=figsize[1], label="FigHeight")
        self.editor_fontsz = gui.Float(low=6, high=64, step=1.0, digits=1, default=self.config['FontSize'], label="FontSize")
        self.editor_fontsz.valueChanged.connect(self.plot)
        self.editor_skip = gui.Int(low=0, high=100, step=1, default=0, label='DataSkip', 
                                   tooltip='plot every nth data row')
        
        styles = GetPlotSyles()
        self.combo_style = gui.ComboBox(textList=styles, valueList=styles, label='Style',
                                        default=self.config['Style'],
                                        connectFunc=self.onStyleChanged)
        
        hbox1 = gui.MakeHBoxLayout([
            gui.MakeHBoxLayout([self.combo_style.labelText, self.combo_style]),
            gui.MakeHBoxLayout([self.editor_fig_width.labelText, self.editor_fig_width]),
            gui.MakeHBoxLayout([self.editor_fig_height.labelText, self.editor_fig_height])
        ])
        hbox2 = gui.MakeHBoxLayout([
            self.botton_draw, 
            gui.MakeHBoxLayout([self.chkbox_clear, self.chkbox_grid, self.chkbox_legend]),
            gui.MakeHBoxLayout([self.editor_fontsz.labelText, self.editor_fontsz]),
            gui.MakeHBoxLayout([self.editor_skip.labelText, self.editor_skip])
        ])
        vbox = gui.MakeVBoxLayout([self.canvas, toolbar, hbox1, hbox2])
        self.panel_figure.setLayout(vbox)
    

    def updatePlot(self):
        self.selected_x_col = self.editor_x_axis.getValue()
        self.selected_y_cols = self.editor_y_axis.getValue() 
        try: # draw x v.s x is not allowed
            self.selected_y_cols.remove(self.selected_x_col)
        except ValueError:
            pass
        self.plot()

    
    def setEditorFigureSize(self, w, h):
        self.editor_fig_width.setValue(w)
        self.editor_fig_height.setValue(h)
        
    
    def onStyleChanged(self):
        style.use('default')
        style.use(self.combo_style.getValue())
        self.fig.patch.set_facecolor(plt.rcParams['figure.facecolor'])
        self.fig.set_edgecolor(plt.rcParams['figure.facecolor'])
        self.fig.set_edgecolor(plt.rcParams['figure.edgecolor'])
        self.axes.set_facecolor(plt.rcParams['axes.facecolor'])
        self.plot()
        
    
    def plot(self):
        """ Redraws the figure
        """
        if self.dataframe is None or len(self.selected_y_cols)==0:
            self.statusBar().showMessage('Nothing to plot', 2000)
        else:
            if self.chkbox_clear.isChecked(): # clear the axes and redraw the plot anew
                self.axes.clear()
            
            customFigW = self.editor_fig_width.getValue()
            customFigH = self.editor_fig_height.getValue()            
            currentFigSize = self.fig.get_size_inches()
            if customFigW==0 or customFigH==0: # fig size not given, init to current fig size
                self.setEditorFigureSize(currentFigSize[0], currentFigSize[1])
            elif currentFigSize[0]!=customFigW or currentFigSize[1]!=customFigH: # set to custom fig size
                self.fig.set_size_inches(self.editor_fig_width.getValue(), self.editor_fig_height.getValue(), forward=True)
            
            fontSz = self.editor_fontsz.getValue()
            legnON = self.chkbox_legend.getValue()
            skip = self.editor_skip.getValue()
            
            df = self.dataframe if skip==0 else self.dataframe.iloc[::skip, :]
            ax = df.plot(x=self.selected_x_col, 
                         y=self.selected_y_cols,
                         ax=self.axes,
                         fontsize=fontSz,
                         grid=self.chkbox_grid.isChecked(),
                         legend=legnON)
    
            # ax.patch.set_alpha(0)
    
            # axis label font size
            for item in [ax.title, ax.xaxis.label, ax.yaxis.label]:
                item.set_fontsize(fontSz)
    
            if legnON: # legend font & transparency
                ax.legend(borderpad=0.2, labelspacing=0.2, framealpha=0.8, fontsize=fontSz)
                legn = ax.get_legend()
                if legn is not None: 
                    self.setCustomLegend()
                    legn.draggable(True)

        self.canvas.draw()


    def setCustomLegend(self):
        ''' set legend from custom input text, seperated by comma'''
        legnStr = self.editor_legend.getValue()
        if legnStr:
            legn = self.axes.get_legend()
            if legn is not None:
                for lt, ls in zip(legn.get_texts(), legnStr.split(',')):
                    lt.set_text(ls)
                self.canvas.draw_idle() # refresh


    def savePlot(self):
        path = str(QtWidgets.QFileDialog.getSaveFileName(self, 'Save Image', '',
                                                   "Image files (*.png *.eps *.pdf *.jpg *.tif *.tiff)"))
        if path:
            # self.canvas.print_figure(path, dpi=300, transparent=True)
            self.fig.savefig(path, dpi=300, bbox_inches='tight', transparent=True, pad_inches=0.2)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    
    def createMenu(self):
        """"""
        def addActions(target, actions):
            for action in actions:
                if action is None:
                    target.addSeparator()
                else:
                    target.addAction(action)
                
        fileMenu = self.menuBar().addMenu("&File")
        action_save = self.createAction("&Save plot",
                                        slot=self.savePlot, shortcut="Ctrl+S", tip="Save the plot")
        action_quit = self.createAction("&Quit", slot=self.close,
                                        shortcut="Ctrl+Q", tip="Close the application")
        addActions(fileMenu, (action_save, None, action_quit))

        helpMenu = self.menuBar().addMenu("&Help")
        action_about = self.createAction("&About",
                                         slot=self.dialogAbout, shortcut='F1', tip='About the demo')
        addActions(helpMenu, (action_about,))


    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        action = QtWidgets.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon("./%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            # self.connect(action, SIGNAL(signal), slot)
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action


    def dialogAbout(self):
        msg = """ A very simple data plot tool based on PyQT & matplotlib.\nAuthor: RayN"""
        QtWidgets.QMessageBox.about(self, "About the app", msg.strip())



def SetDarkUI(app):
    """ ref: https://gist.github.com/lschmierer/443b8e21ad93e2a2d7eb """
    app.setStyle("Fusion")
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    
    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)

    curFd = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(os.path.join(curFd, 'icons', 'logo.png')))
    
    try:
        config = json.load(open(__config__))
        if 'Style' in config and config['Style']=='dark_background':
            # SetDarkUI(app) # if figure use dark theme, we make gui dark too ;)
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    except Exception as e:
        warnings.warn('load config file failed, use default config. \n%r'%e)
        resolution = app.desktop().screenGeometry()
        w, h = resolution.width(), resolution.height()
        config = { 'WindowSize' : (int(0.382*w), int(0.45*h)) }
        
    window = EzPlot(config)
    window.show()
    app.exec_()



if __name__ == "__main__":
    main()
