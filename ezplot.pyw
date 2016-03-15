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

import pandas as pd
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

if sys.version_info >= (3, 0):
    unicode = str # for python 3

__appname__ = 'ezPlot'
__version__ = "1.0.0"
__author__  = 'RayN'

def SetPlotStyle(figsize=(4.8,3.6)):
    """ Set MPL plot paprameters """
    mpl.use('Qt4Agg')
    mpl.rcParams['font.sans-serif'] = ['SimHei'] # 指定默认字体
    mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题

    # mpl.rcParams['figure.figsize'] = figsize # [8, 6] # inch
    # mpl.rcParams['figure.dpi'] = 100 # dots per inch

    # mpl.rcParams['savefig.dpi'] = 300
    # mpl.rcParams['savefig.bbox'] = 'tight'
    # mpl.rcParams['savefig.pad_inches'] = 0.0

    # mpl.rcParams['font.family'] = 'serif'
    # mpl.rcParams['font.size'] = 12

    # mpl.rcParams['legend.fontsize'] = 12
    # mpl.rcParams['legend.fancybox'] = True
    #
    mpl.rcParams['lines.linewidth'] = 1.2
    mpl.rcParams['lines.markersize'] = 5
    #
    # mpl.rcParams['axes.grid'] = False

    # mpl.rcParams['text.usetex'] = False
    # color cycle for plot lines
    mpl.rcParams['axes.color_cycle'] = \
    ['#348ABD', '#A60628', '#7A68A6', '#467821',
     '#D55E00', '#CC79A7', '#56B4E9', '#009E73', '#F0E442', '#0072B2']


class AppForm(QMainWindow):
    def __init__(self, parent=None):
        super(AppForm, self).__init__(parent)
        self.setWindowTitle(__appname__ +'  ver.'+__version__)
        self.resize(900, 600)
        self.center()

        self.create_menu()
        self.create_loader()
        self.create_figure_mpl(figSize=(5,4), figDPI=120)

        self.main_frame = QSplitter(Qt.Horizontal)
        self.main_frame.addWidget(self.panel_loader)
        self.main_frame.addWidget(self.panel_fig)
        self.setCentralWidget(self.main_frame)

        self.main_frame.setStretchFactor(0, 1)
        self.main_frame.setStretchFactor(1, 4)

        status = self.statusBar()
        status.setSizeGripEnabled(True)
        status.showMessage("Ready", 5000)


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # =====================================================================
    def create_loader(self):
        ''' create data file loader panel '''
        self.panel_loader = QWidget()
        # init dataFrame
        self.dataFrame = None

        fnLabel = QLabel("  &Data:")
        self.datFnLineEdit = QLineEdit()
        self.datFnLineEdit.setMinimumWidth(100)
        self.connect(self.datFnLineEdit, SIGNAL('editingFinished()'), self.file_load)
        fnLabel.setBuddy(self.datFnLineEdit)

        self.botton_open = QPushButton("&Open")
        self.connect(self.botton_open, SIGNAL('clicked()'), self.file_open)

        xLabel = QLabel("&X Axis:")
        self.xSelComboBox = QComboBox()
        self.xSelComboBox.setEditable(False)
        self.connect(self.xSelComboBox, SIGNAL('currentIndexChanged(int)'), self.update_plot_data)
        xLabel.setBuddy(self.xSelComboBox)

        # self.xSelComboBox.addItems([])

        yLabel = QLabel("&Y Axis:")
        self.ySelList = QListWidget()
        self.ySelList.setSelectionMode(QAbstractItemView.ExtendedSelection) # multiple selection
        self.connect(self.ySelList, SIGNAL('itemSelectionChanged()'), self.update_plot_data)
        yLabel.setBuddy(self.ySelList)
        # self.ySelList.addItems([])

        lgdLabel = QLabel("Legend:")
        self.lgdLineEdit= QLineEdit()
        self.connect(self.lgdLineEdit, SIGNAL('editingFinished()'), self.set_legend)
        lgdLabel.setBuddy(self.lgdLineEdit)
        self.lgdLineEdit.setToolTip('Use comma(,) to seperate legend text')

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(fnLabel, 1, 0)
        grid.addWidget(self.datFnLineEdit, 1, 1)
        grid.addWidget(self.botton_open, 1, 2)

        grid.addWidget(xLabel, 2, 0)
        grid.addWidget(self.xSelComboBox, 2, 1, 1, 2)

        grid.addWidget(yLabel, 3, 0)
        grid.addWidget(self.ySelList, 3, 1, 4, 2)

        grid.addWidget(lgdLabel, 7, 0)
        grid.addWidget(self.lgdLineEdit, 7, 1, 1, 2)

        self.panel_loader.setLayout(grid)


    def file_open(self):
        try: # use current date path as default open dir
            curDir = os.path.split(unicode(self.datFnLineEdit.text()))[0]
        except:
            curDir = ''

        datPath = QFileDialog.getOpenFileName(
            self, 'Select File', curDir, "Data files (*.csv *.pkl)")

        if datPath=="": # canceled
            return
        else:
            self.datFnLineEdit.setText(datPath)
            self.file_load()


    def file_load(self):
        # load data into dataFrame
        datPath = unicode(self.datFnLineEdit.text())
        if os.path.exists(datPath):
            fType = datPath.split('.')[-1]
            if fType=='csv':
                func_read = pd.read_csv
            elif fType=='pkl':
                func_read = pd.read_pickle
            else:
                self.statusBar().showMessage('File type not supported (support: .csv, .pkl)', 5000)
                return

            try:
                df = func_read(datPath)
            except Exception as e:
                with open(r'./err_read.log','w') as f: f.write(e)
                self.statusBar().showMessage('Read data file failed, see log for details.', 8000)
                return

            self.dataFrame = None
            colNames = df.columns.tolist()

            self.ySelList.clearSelection()
            self.ySelList.clear()
            self.ySelList.addItems(colNames)

            self.xSelComboBox.clear()
            self.xSelComboBox.addItems(colNames)
            self.xSelComboBox.setCurrentIndex(0)

            # self.ySelList.setCurrentItem(colNames[0])

            self.dataFrame = df
            self.statusBar().showMessage('Data loaded successfully.', 5000)
        else:
            self.statusBar().showMessage('File does not exist', 5000)
            return

    # =====================================================================
    def create_figure_mpl(self, figSize=(5,4), figDPI=100):
        ''' create matplotlib figure panel '''
        SetPlotStyle()
        self.panel_fig = QWidget()

        # Create the mpl Figure and FigCanvas objects.
        self.fig = Figure(figSize, dpi=figDPI)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.panel_fig)

        self.axes = self.fig.add_subplot(111)

        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.panel_fig)

        # figure control widgets
        self.botton_draw = QPushButton("&Plot")
        self.connect(self.botton_draw, SIGNAL('clicked()'), self.update_plot_data)

        self.chkbox_clear = QCheckBox("&Clear")
        self.chkbox_clear.setChecked(True)

        self.chkbox_grid = QCheckBox("&Grid")
        self.chkbox_grid.setChecked(True)
        # self.connect(self.chkbox_grid, SIGNAL('stateChanged(int)'), self.plot_mpl)

        self.chkbox_legend = QCheckBox("&Legend")
        self.chkbox_legend.setChecked(True)
        # self.connect(self.chkbox_legend, SIGNAL('stateChanged(int)'), self.plot_mpl)

        self.slider_fontsz = QSlider(Qt.Horizontal)
        self.slider_fontsz.setRange(5, 50)
        self.slider_fontsz.setValue(10)
        self.slider_fontsz.setTickInterval(5)
        self.slider_fontsz.setTickPosition(QSlider.TicksBothSides)
        self.slider_fontsz.setTracking(True)
        self.connect(self.slider_fontsz, SIGNAL('valueChanged(int)'), self.plot_mpl)
        sliderLabel = QLabel('&Font Size:')
        sliderLabel.setBuddy(self.slider_fontsz)

        hbox = QHBoxLayout()
        for w in [self.botton_draw, self.chkbox_clear, self.chkbox_grid, self.chkbox_legend,
                  sliderLabel, self.slider_fontsz]:
            hbox.addWidget(w)
            # hbox.setAlignment(w, Qt.AlignVCenter)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)

        self.panel_fig.setLayout(vbox)


    def update_plot_data(self):
        self.xColName = unicode(self.xSelComboBox.currentText())
        self.yColNames = [ unicode(item.text())
                         for item in self.ySelList.selectedItems() ]

        if self.xColName in self.yColNames:
            self.yColNames.remove(self.xColName)

        if len(self.yColNames)>0:
            self.plot_mpl()


    def plot_mpl(self):
        """ Redraws the figure
        """
        if self.dataFrame is None or len(self.yColNames)==0:
            self.statusBar().showMessage('Nothing to plot', 2000)
            return

        if self.chkbox_clear.isChecked(): # clear the axes and redraw the plot anew
            self.axes.clear()

        fontSz = self.slider_fontsz.value()
        legnON = self.chkbox_legend.isChecked()
        ax = self.dataFrame.plot(x=self.xColName, y=self.yColNames,
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
            if legn is not None: legn.draggable(True)

        self.canvas.draw()


    def set_legend(self):
        ''' set legend from custom input text, seperated by comma'''
        legnStr = unicode(self.lgdLineEdit.text())
        if len(legnStr)>0:
            legn = self.axes.get_legend()
            if legn is not None:
                for lt, ls in zip(legn.get_texts(), legnStr.split(',')):
                    lt.set_text(ls)
                self.canvas.draw() # refresh
                self.statusBar().showMessage('Legend updated', 2000)


    def save_plot(self):
        path = unicode(QFileDialog.getSaveFileName(self, 'Save Image', '',
                                                   "Image files (*.png *.pdf *.jpg *.tif *.tiff)"))
        if path:
            # self.canvas.print_figure(path, dpi=300, transparent=True)
            self.fig.savefig(path, dpi=300, bbox_inches='tight', transparent=True, pad_inches=0.2)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    # =====================================================================
    def create_menu(self):
        fileMenu = self.menuBar().addMenu("&File")
        action_save = self.create_action("&Save plot",
            slot=self.save_plot, shortcut="Ctrl+S", tip="Save the plot")
        action_quit = self.create_action("&Quit", slot=self.close,
            shortcut="Ctrl+Q", tip="Close the application")
        self.add_actions(fileMenu, (action_save, None, action_quit))

        helpMenu = self.menuBar().addMenu("&Help")
        action_about = self.create_action("&About",
            slot=self.on_about,  shortcut='F1', tip='About the demo')
        self.add_actions(helpMenu, (action_about,))


    def create_action(self, text, slot=None, shortcut=None, icon=None,
                                    tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon("./%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def on_about(self):
        msg = """ A very simple data plot tool based on PyQT. """
        QMessageBox.about(self, "About the demo", msg.strip())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(__appname__)

    curFd = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QIcon(os.path.join(curFd, 'icons', 'logo.png')))

    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
