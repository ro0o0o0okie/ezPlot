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

from matplotlib import style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets, QtGui

import gui_base as bui


__appname__ = 'EzPlot'
__version__ = "2.0.0"
__author__  = 'RayN'


__config__ = 'config.json'


def GetPlotSyles():
    return ['default', 'classic'] + sorted(
        style for style in plt.style.available if style != 'classic')


# def SetPlotStyle():
#     """ Set MPL plot paprameters """
#     style.use('bmh')
#     # style.use('seaborn-paper')
#     # style.use('fivethirtyeight')
#     # cn_font_prop = fontm.FontProperties(fname=settings.FILE_FIGURE_FONT, size=9) # fix legend CN issue
#     # mpl.use('Qt5Agg')
#     # mpl.rcParams['font.family'] = 'serif'
#     # mpl.rcParams['font.sans-serif'] = ['SimHei'] # 指定默认字体
#     # mpl.rcParams['font.serif'] = ['Times'] # 指定默认字体
#     # mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
# 
#     # mpl.rcParams['figure.figsize'] = figsize # [8, 6] # inch
#     # mpl.rcParams['figure.dpi'] = 100 # dots per inch
# 
#     # mpl.rcParams['savefig.dpi'] = 300
#     # mpl.rcParams['savefig.bbox'] = 'tight'
#     # mpl.rcParams['savefig.pad_inches'] = 0.0
# 
#     # mpl.rcParams['font.family'] = 'serif'
#     # mpl.rcParams['font.size'] = 12
# 
#     # mpl.rcParams['legend.fontsize'] = 12
#     # mpl.rcParams['legend.fancybox'] = True
#     #
#     # mpl.rcParams['lines.linewidth'] = 1.2
#     # mpl.rcParams['lines.markersize'] = 5
#     #
#     # mpl.rcParams['axes.grid'] = False
# 
#     # mpl.rcParams['text.usetex'] = False
#     # color cycle for plot lines
#     # mpl.rcParams['axes.color_cycle'] = \
#     # ['#348ABD', '#A60628', '#7A68A6', '#467821',
#     #  '#D55E00', '#CC79A7', '#56B4E9', '#009E73', '#F0E442', '#0072B2']

        


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

        self.createMenu()
        self.createLoader()
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
            'FigWidth'      : self.edit_fig_width.getValue(), 
            'FigHeight'     : self.edit_fig_height.getValue(), 
            'FlagClear'     : self.chkbox_clear.isChecked(), 
            'FlagGrid'      : self.chkbox_grid.isChecked(), 
            'FlagLegend'    : self.chkbox_legend.isChecked(),
            'FontSize'      : self.edit_fontsz.getValue(),
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
        self.setFigureSizeEditor(fsize[0], fsize[1])
    
    
    def resizeEvent(self, event):
        # update fig size text when resized
        fsize = self.fig.get_size_inches()
        self.setFigureSizeEditor(fsize[0], fsize[1])
    
    
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def createLoader(self):
        ''' create data file loader panel '''
        self.panel_loader = QtWidgets.QWidget()
        # init dataFrame
        self.dataframe = None
        self.datafile = bui.File(label="Data", default=self.config['DataFile'], minWidth=120, callbackFunc=self.onLoadFile)
        self.editor_x_axis = bui.ComboBox(textList=[], label='X Axis', connectFunc=self.updatePlotData)
        self.editor_y_axis = bui.List(items=[], multiple=True, label="Y Axis", connectFunc=self.updatePlotData)
        self.editor_legend = bui.Text(default=None, label='Legend',
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


    def onLoadFile(self):
        # load data into dataFrame
        datPath = self.datafile.getValue()
        if os.path.isfile(datPath):
            df = None
            for readfunc in (pd.read_csv, pd.read_excel, pd.read_pickle, pd.read_table):
                try:
                    df = readfunc(datPath)
                    break 
                except:
                    pass
                
            if df is None or df.empty:
                self.statusBar().showMessage('Read data file failed! (supported formats: CSV, Pickle, Excel)', 8000)
            else:
                # df.reset_index(level=None, inplace=True)
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
        self.botton_draw = QtWidgets.QPushButton("&Plot")
        self.botton_draw.clicked.connect(self.updatePlotData)
        
        self.chkbox_clear = QtWidgets.QCheckBox("&Clear")
        self.chkbox_clear.setChecked(self.config['FlagClear'])

        self.chkbox_grid = QtWidgets.QCheckBox("&Grid")
        self.chkbox_grid.setChecked(self.config['FlagGrid'])

        self.chkbox_legend = QtWidgets.QCheckBox("&Legend")
        self.chkbox_legend.setChecked(self.config['FlagLegend'])
        
        self.edit_fig_width = bui.Float(low=1, high=64, step=0.01, digits=2, default=figsize[0], label="FigWidth")
        self.edit_fig_height = bui.Float(low=1, high=64, step=0.01, digits=2, default=figsize[1], label="FigHeight")
        self.edit_fontsz = bui.Float(low=6, high=64, step=1.0, digits=1, default=self.config['FontSize'], label="FontSize")
        self.edit_fontsz.valueChanged.connect(self.plot)
        
        styles = GetPlotSyles()
        self.combo_style = bui.ComboBox(textList=styles, valueList=styles, label='Style', 
                                        default=self.config['Style'],
                                        connectFunc=self.onStyleChanged)
        
        hbox1 = bui.MakeHBoxLayout([
            bui.MakeHBoxLayout([self.combo_style.labelText, self.combo_style]),
            bui.MakeHBoxLayout([self.edit_fig_width.labelText, self.edit_fig_width]),
            bui.MakeHBoxLayout([self.edit_fig_height.labelText, self.edit_fig_height])
        ])
        hbox2 = bui.MakeHBoxLayout([
            self.botton_draw, 
            bui.MakeHBoxLayout([self.chkbox_clear, self.chkbox_grid, self.chkbox_legend]),
            bui.MakeHBoxLayout([self.edit_fontsz.labelText, self.edit_fontsz])
        ])
        vbox = bui.MakeVBoxLayout([self.canvas, toolbar, hbox1, hbox2])
        self.panel_figure.setLayout(vbox)
    

    def updatePlotData(self):
        self.selected_x_col = self.editor_x_axis.getValue()
        self.selected_y_cols = self.editor_y_axis.getValue() 
        try: # draw x v.s x is not allowed
            self.selected_y_cols.remove(self.selected_x_col)
        except ValueError:
            pass
        self.plot()

    
    def setFigureSizeEditor(self, w, h):
        self.edit_fig_width.setValue(w)
        self.edit_fig_height.setValue(h)
        
    
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
            
            customFigW = self.edit_fig_width.getValue()
            customFigH = self.edit_fig_height.getValue()            
            currentFigSize = self.fig.get_size_inches()
            if customFigW==0 or customFigH==0: # fig size not given, init to current fig size
                self.setFigureSizeEditor(currentFigSize[0], currentFigSize[1])
            elif currentFigSize[0]!=customFigW or currentFigSize[1]!=customFigH: # set to custom fig size
                self.fig.set_size_inches(self.edit_fig_width.getValue(), self.edit_fig_height.getValue(), forward=True)
            
            fontSz = self.edit_fontsz.value()
            legnON = self.chkbox_legend.isChecked()
            
            ax = self.dataframe.plot(x=self.selected_x_col, y=self.selected_y_cols,
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

    # =====================================================================
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



def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)

    curFd = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(os.path.join(curFd, 'icons', 'logo.png')))
    
    resolution = app.desktop().screenGeometry()
    w, h = resolution.width(), resolution.height()
    
    try:
        config = json.load(open(__config__))
    except Exception as e:
        warnings.warn('load config file failed, use default config. \n%r'%e)
        config = {
            'WindowSize' : (int(0.382*w), int(0.5*h))
        }
    window = EzPlot(config)
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
