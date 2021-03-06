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
from collections import OrderedDict, defaultdict
from matplotlib import style, colors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot

import gui_base as gui
from yaxis_selector import DataFrameTree

__appname__ = 'EzPlot'
__version__ = "3.0.1802"
__author__  = 'RayN'
__config__ = os.path.join(os.path.dirname(__file__), 'config.json')


'''
TODO:
    + hist & scatter plot : https://elitedatascience.com/python-seaborn-tutorial
'''


def GetPlotThemeSyles():
    return ['default', 'classic'] + sorted(
        style for style in plt.style.available if style != 'classic')
        

class EzPlot(QtWidgets.QMainWindow):
    
    # default config
    config = {
        'WindowSize' : (1200, 800),
        'SplitterState' : None,
        'DataFile' : os.path.dirname(__file__),
        'Style' : 'default',
        'FigWidth' : 5, 'FigHeight' : 4, 'FigAlpha' : 1.0,
        'FlagClear' : True, 'FlagGrid' : True, 'FlagLegend' : True,
        'FontSize' : 11,
    }
    
    def __init__(self, config:dict=None):
        super(EzPlot, self).__init__()
        if config:
            self.config.update(config)
        
        self.setStyleSheet('font-size: 10pt; font-family: microsoft yahei;') # overide font
        self.setWindowTitle(__appname__ +'  v'+__version__ + '  by ' + __author__)
        self.resize(*self.config['WindowSize'])
        self.center()
        
        self.dataframes = OrderedDict() # fn => df
        
        self.createMenu()
        self.createLoaderPanel()
        self.createFigurePanel()
        self.applyPlotStyle()

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
        self.config.update({
            # 'WindowSize'    : (self.frameGeometry().width(), self.frameGeometry().height()),
            'SplitterState' : str(self.main_frame.saveState().toHex(), encoding='ascii'),
            'DataFile'      : self.editor_datafile.getValue(),
            'Style'         : self.combo_style.getValue(),
            'FigWidth'      : self.editor_fig_width.getValue(), 
            'FigHeight'     : self.editor_fig_height.getValue(), 
            'FigAlpha'      : self.editor_fig_alpha.getValue(), 
            'FlagClear'     : self.chkbox_clear.isChecked(), 
            'FlagGrid'      : self.chkbox_grid.isChecked(), 
            'FlagLegend'    : self.chkbox_legend.isChecked(),
            'FontSize'      : self.editor_fontsz.getValue(),
        })
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
        wsize = self.frameSize()
        self.config['WindowSize'] = (wsize.width(), wsize.height())
    
    
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def createLoaderPanel(self):
        """create data file loader panel """
        self.panel_loader = QtWidgets.QWidget()
        self.editor_datafile = gui.File(label="Data", default=None,
                                        dlgDir=os.path.dirname(self.config['DataFile']),
                                        minWidth=120, callbackFunc=self.loadFile)
        self.editor_x_axis = gui.ComboBox(textList=[], label='X Axis', connectFunc=self.plot)


        self.editor_y_axis = DataFrameTree(parent=self,label='Y Axis')
        self.editor_y_axis.itemSelectionChanged.connect(self.plot)
        self.editor_y_axis.signal_column_renamed.connect(self.onColumnRenamed)
        self.editor_y_axis.signal_active_style_changed.connect(self.plot)
        self.editor_y_axis.signal_dataframe_deleted.connect(self.onDataFrameDeleted)
        self.editor_y_axis.signal_dataframe_reload.connect(self.onDataFrameReload)
        
        self.editor_ytitle = gui.Text(default=None, label='Y Title')     
        self.editor_xtitle = gui.Text(default=None, label='X Title')        
        self.editor_legend = gui.Text(default=None, label='Legend', 
                                      tooltip='multiple labels can be seperated by comma')
        self.editor_legend.editingFinished.connect(self.setCustomLegend)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.editor_datafile.labelText, 1, 0)
        grid.addWidget(self.editor_datafile.text, 1, 1)
        grid.addWidget(self.editor_datafile.button, 1, 2)

        grid.addWidget(self.editor_x_axis.labelText, 2, 0)
        grid.addWidget(self.editor_x_axis, 2, 1, 1, 2)

        grid.addWidget(self.editor_y_axis.labelText, 3, 0)
        grid.addWidget(self.editor_y_axis, 3, 1, 4, 2)
        
        grid.addWidget(self.editor_xtitle.labelText, 7, 0)
        grid.addWidget(self.editor_xtitle, 7, 1, 1, 2)
        grid.addWidget(self.editor_ytitle.labelText, 8, 0)
        grid.addWidget(self.editor_ytitle, 8, 1, 1, 2)
        
        grid.addWidget(self.editor_legend.labelText, 9, 0)
        grid.addWidget(self.editor_legend, 9, 1, 1, 2)

        self.panel_loader.setLayout(grid)
    
    
    def updateXAxisNames(self, colNames=None):
        """update the common x-axis names for editor_x_axis, keep currently selected if possible"""
        if colNames is None: # update to current df if given None
            ndf = len(self.dataframes)
            if ndf>1:
                commonNames = set.intersection(*[set(df.columns) for df in self.dataframes.values()])
            elif ndf==1:
                commonNames = [df.columns.tolist() for df in self.dataframes.values()][0]
            else: # <1
                commonNames = []
            self.updateXAxisNames(commonNames)
        else:  
            if colNames: # non-empty
                xSelected = self.editor_x_axis.getValue()
                if xSelected not in colNames:
                    xSelected = None
                self.editor_x_axis.resetItems(list(colNames), default=xSelected)
            else:
                self.editor_x_axis.resetItems([])
    
    
    @pyqtSlot(tuple) #  (fn, oldName, newName) 
    def onColumnRenamed(self, names:tuple):
        fn, oldName, newName = names
        df = self.dataframes[fn] 
        # rename df columns
        df.rename(columns={oldName:newName}, inplace=True)
        # update x-axis to current common names
        # commonNames = set.intersection(*[set(df.columns) for df in self.dataframes.values()])
        self.updateXAxisNames()
    
    @pyqtSlot(str) # fn
    def onDataFrameDeleted(self, fn:str):
        if fn in self.dataframes:
            del self.dataframes[fn]
            # update x-axis to current common names
            self.updateXAxisNames()
    
    @pyqtSlot(str) # fn
    def onDataFrameReload(self, fn:str):
        self.loadFile(fn)
    
    
    def loadFile(self, fn:str=None):
        """ load data into dataFrame """
        if fn is None:
            fn = os.path.abspath(self.editor_datafile.getValue())
        if os.path.isfile(fn):
            df = None
            tryFuncs = (pd.read_csv, pd.read_excel, pd.read_pickle, pd.read_table)
            tryFuncArgvs = [
                {'index_col': False }, # read_csv
                {}, # read_excel
                {}, # read_pickle
                {} # read_table
            ]
            for readfunc, argDict in zip(tryFuncs, tryFuncArgvs):
                try:
                    df = readfunc(fn, **argDict)
                    break 
                except:
                    pass
            
            if df is None or df.empty:
                self.statusBar().showMessage('Read data file failed! (supported formats: CSV, Pickle, Excel)', 8000)
            else:
                df.reset_index(level=None, inplace=True) # in case the header column does not math data column number
                df.columns = df.columns.str.strip() # strip column names
                # print(df)
                self.dataframes[fn] = df
                colNames = df.columns.tolist()
                # update y-axis dfTree
                self.editor_y_axis.addDataFrame(datafn=fn, columns=colNames)
                # update x-axis common columns
                self.updateXAxisNames()        
                self.statusBar().showMessage('Data loaded successfully.', 5000)
        else:
            self.statusBar().showMessage('File does not exist', 5000)

    
    def createFigurePanel(self):
        """ create matplotlib figure panel """
        self.panel_figure = QtWidgets.QWidget()
        
        # Create the mpl Figure and FigCanvas objects.
        style.use(self.config['Style'])
        figsize = (self.config['FigWidth'], self.config['FigHeight'])
        
        self.fig = Figure(figsize)
        self.fig.patch.set_alpha(0.0)
        self.canvas = FigureCanvas(figure=self.fig)
        self.canvas.setParent(self.panel_figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.axes = self.fig.add_subplot(111)
        
        # Create the navigation toolbar, tied to the canvas
        toolbar = NavigationToolbar(self.canvas, self.panel_figure)

        # figure control widgets
        self.botton_draw = gui.MakePushButton('Plot', minWidth=120, clickFunc=self.plot)
        
        self.chkbox_clear = gui.CheckBox(default=self.config['FlagClear'], label='Clear')
        self.chkbox_grid = gui.CheckBox(default=self.config['FlagGrid'], label='Grid')
        self.chkbox_legend = gui.CheckBox(default=self.config['FlagLegend'], label='Legend')
        
        self.editor_fig_width  = gui.Float(label="W", tooltip='figure width',
                                           low=1, high=64, step=0.01, digits=2, default=figsize[0])
        self.editor_fig_height = gui.Float(label="H", tooltip='figure height',
                                           low=1, high=64, step=0.01, digits=2, default=figsize[1])
        self.editor_fig_alpha  = gui.Float(label="Alpha", tooltip='figure background alpha', 
                                           low=0, high=1, step=0.1, digits=1, default=self.config['FigAlpha'])
        
        self.editor_fontsz = gui.Float(low=6, high=64, step=1.0, digits=1, default=self.config['FontSize'], label="FontSize")
        self.editor_fontsz.valueChanged.connect(self.plot)
        self.editor_skip = gui.Int(low=0, high=100, step=1, default=0, label='DataSkip', tooltip='plot every nth data row')
        self.editor_skip.valueChanged.connect(self.plot)
        
        styles = GetPlotThemeSyles()
        self.combo_style = gui.ComboBox(textList=styles, valueList=styles, label='Style',
                                        default=self.config['Style'],
                                        connectFunc=self.applyPlotStyle)
        
        hbox1 = gui.MakeHBoxLayout([
            gui.MakeHBoxLayout([self.combo_style.labelText, self.combo_style]),
            gui.MakeHBoxLayout([self.editor_fig_width.labelText, self.editor_fig_width]),
            gui.MakeHBoxLayout([self.editor_fig_height.labelText, self.editor_fig_height]),
            gui.MakeHBoxLayout([self.editor_fig_alpha.labelText, self.editor_fig_alpha])
        ])
        hbox2 = gui.MakeHBoxLayout([
            self.botton_draw, 
            gui.MakeHBoxLayout([self.chkbox_clear, self.chkbox_grid, self.chkbox_legend]),
            gui.MakeHBoxLayout([self.editor_fontsz.labelText, self.editor_fontsz]),
            gui.MakeHBoxLayout([self.editor_skip.labelText, self.editor_skip])
        ])
        vbox = gui.MakeVBoxLayout([self.canvas, toolbar, hbox1, hbox2])
        self.panel_figure.setLayout(vbox)

    
    def setEditorFigureSize(self, w, h):
        self.editor_fig_width.setValue(w)
        self.editor_fig_height.setValue(h)
        
    
    def applyPlotStyle(self):
        plt.rcdefaults()
        style.use(self.combo_style.getValue())
        self.fig.set_facecolor(plt.rcParams['figure.facecolor'])
        self.fig.set_edgecolor(plt.rcParams['figure.edgecolor'])
        self.axes.set_facecolor(plt.rcParams['axes.facecolor'])
        
        for axsp in self.axes.spines.values():
            axsp.set_edgecolor(plt.rcParams['axes.edgecolor'])
            axsp.set_linewidth(1.0)
            axsp.set_alpha(1.0)

        self.plot()
    
    
    def plot(self):
        """ Redraws the figure
        """
        def colNamesFormColNodes(colNodes, excludeName=None):
            if excludeName:
                return [col.column_name for col in colNodes if col.column_name!=excludeName]
            else:
                return [col.column_name for col in colNodes]
        
        xSelectedName = self.editor_x_axis.getValue() # selected x-axis column name
        if xSelectedName is None:
            return 
        
        ySelectedNodes = self.editor_y_axis.getSelectedColumns() # fn => [selected column nodes]
        ySelectedNames = {} # fn => [selected y-axis column names]
        for fn, nodes in ySelectedNodes.items():
            names = colNamesFormColNodes(nodes, excludeName=xSelectedName) 
            if names:
                ySelectedNames[fn] = names
                
        if self.dataframes and ySelectedNames:
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
            gridON = self.chkbox_grid.isChecked()
            rowSkip = self.editor_skip.getValue()
            
            for fn, ys in ySelectedNames.items():
                lineSet = set(self.axes.get_lines())
                df = self.dataframes[fn]
                if rowSkip>0:
                     df = df.iloc[::rowSkip, :]
                ax = df.plot(x=xSelectedName, 
                             y=ys,
                             ax=self.axes,
                             fontsize=fontSz,
                             grid=gridON,
                             legend=legnON)
                
                # apply individual user-custom styles (to newly plotted lines)
                newLines = set(ax.get_lines()) - lineSet # this avoid apply style to lines with same label
                for colNode in ySelectedNodes[fn]:
                    usersty = colNode.getStyle()
                    if usersty: # will be True if non-default
                        for line in newLines:
                            if line.get_label() == colNode.column_name:
                                usersty.apply(line)
                                break
        
            # axis grid
            if gridON:
                self.axes.grid(linestyle='--')
            
            # axis label
            ylabel = self.editor_ytitle.getValue()
            if ylabel: 
                self.axes.set_ylabel(ylabel)
            
            xlabel = self.editor_xtitle.getValue()
            if xlabel:
                self.axes.set_xlabel(xlabel)
                
            # axis alpha
            self.axes.patch.set_alpha(self.editor_fig_alpha.getValue())
            
            # axis label font size
            for item in [self.axes.title, self.axes.xaxis.label, self.axes.yaxis.label]:
                item.set_fontsize(fontSz)
            
            if legnON: # legend font & transparency
                self.axes.legend(borderpad=0.2, labelspacing=0.2, framealpha=0.8, fontsize=fontSz)
                legn = self.axes.get_legend()
                if legn is not None: 
                    self.setCustomLegend(canvasDraw=False)
                    legn.draggable(True)
        
            self.canvas.draw()
            
        else:
            self.statusBar().showMessage('Nothing to plot', 2000)

    def setCustomLegend(self, canvasDraw=True):
        ''' set legend from custom input text, seperated by comma'''
        legnStr = self.editor_legend.getValue()
        if legnStr:
            legn = self.axes.get_legend()
            if legn is not None:
                for lt, ls in zip(legn.get_texts(), legnStr.split(',')):
                    lt.set_text(ls)
                if canvasDraw:
                    self.canvas.draw_idle() # refresh


    # def savePlot(self):
    #     path = str(QtWidgets.QFileDialog.getSaveFileName(self, 'Save Image', '',
    #                                                "Image files (*.png *.eps *.pdf *.jpg *.tif *.tiff)"))
    #     if path:
    #         # self.canvas.print_figure(path, dpi=300, transparent=True)
    #         self.fig.savefig(path, dpi=300, bbox_inches='tight', transparent=True, pad_inches=0.2)
    #         self.statusBar().showMessage('Saved to %s' % path, 2000)

    
    def createMenu(self):
        """"""
        def addActions(target, actions):
            for action in actions:
                if action is None:
                    target.addSeparator()
                else:
                    target.addAction(action)
                
        fileMenu = self.menuBar().addMenu("&File")
        # action_save = self.createAction("&Save plot",
        #                                 slot=self.savePlot, shortcut="Ctrl+S", tip="Save the plot")
        action_quit = self.createAction("&Quit", slot=self.close,
                                        shortcut="Ctrl+Q", tip="Close the application")
        # addActions(fileMenu, (action_save, None, action_quit))
        addActions(fileMenu, (None, action_quit))

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
        config = { 'WindowSize' : (int(0.382*w), int(0.5*h)) }
        
    window = EzPlot(config)
    window.show()
    app.exec_()



if __name__ == "__main__":
    main()
