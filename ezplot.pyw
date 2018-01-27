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
import matplotlib as mpl
# mpl.use('Qt5Agg')
print(mpl.get_backend())


from matplotlib import style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5 import QtCore, QtWidgets, QtGui


__appname__ = 'EzPlot'
__version__ = "2.0.0"
__author__  = 'RayN'


def SetPlotStyle(figsize=(4.8,3.6)):
    """ Set MPL plot paprameters """
    # style.use('seaborn-paper')
    # style.use('fivethirtyeight')
    # cn_font_prop = fontm.FontProperties(fname=settings.FILE_FIGURE_FONT, size=9) # fix legend CN issue
    # mpl.use('Qt5Agg')
    # mpl.rcParams['font.family'] = 'serif'
    # mpl.rcParams['font.sans-serif'] = ['SimHei'] # 指定默认字体
    # mpl.rcParams['font.serif'] = ['Times', 'SimHei'] # 指定默认字体
    # mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题

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
    # mpl.rcParams['axes.color_cycle'] = \
    # ['#348ABD', '#A60628', '#7A68A6', '#467821',
    #  '#D55E00', '#CC79A7', '#56B4E9', '#009E73', '#F0E442', '#0072B2']


class Float(QtWidgets.QDoubleSpinBox):
    def __init__(self, low, high, step, digits=3, default=None,
                 prefix=None, suffix=None, readonly=False, minWidth=50, label="Float", tooltip=None):
        super(Float, self).__init__()
        self.labelText = QtWidgets.QLabel(label+':')
        self.default = default if default is not None else low # use 'low' as default if not given
        self.setRange(low, high)
        self.setSingleStep(step)
        self.setDecimals(digits)
        self.setDefault()
        if prefix is not None : self.setPrefix(prefix)
        if suffix is not None : self.setSuffix(suffix)
        if readonly : self.enable(False) # self.setReadOnly(True)
        if tooltip  : self.setToolTip(tooltip)
        self.setMinimumWidth(minWidth)
        self.setFocusPolicy(QtCore.Qt.StrongFocus) # diable wheel focus

    def wheelEvent(self, event):
        """ overide default wheel envent to prevent accidently changing value by scrolling.
        """
        pass

    def setDefault(self):
        """ reset to default value. """
        self.setValue(self.default)

    def getValue(self):
        return float(self.value())

    def getLimit(self):
        """ widget min & max limit """
        return self.minimum(), self.maximum()

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)
        


class AppForm(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AppForm, self).__init__(parent)
        self.setStyleSheet('font-size: 10pt; font-family: microsoft yahei;') # overide font
        self.setWindowTitle(__appname__ +'  v'+__version__ + '  by ' + __author__)
        self.resize(1200, 800)
        self.center()

        self.create_menu()
        self.create_loader()
        self.create_figure_mpl(figSize=(5,4), figDPI=120)

        self.main_frame = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_frame.addWidget(self.panel_loader)
        self.main_frame.addWidget(self.panel_fig)
        self.setCentralWidget(self.main_frame)

        self.main_frame.setStretchFactor(0, 1)
        self.main_frame.setStretchFactor(1, 4)

        # zp = ZoomPan() # setup mouse zoom & pan
        # for ax in [self.axes]:
        #     zp.zoom_factory(ax, base_scale = 1.01)
        #     zp.pan_factory(ax)
        
        status = self.statusBar()
        status.setSizeGripEnabled(True)
        status.showMessage("Ready", 5000)

    
    
    def resizeEvent(self, event):
        # update fig size text when resized
        fsize = self.fig.get_size_inches()
        self.set_figure_size_editor(fsize[0],fsize[1])
    
    
    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # =====================================================================
    def create_loader(self):
        ''' create data file loader panel '''
        self.panel_loader = QtWidgets.QWidget()
        # init dataFrame
        self.dataFrame = None

        fnLabel = QtWidgets.QLabel("  &Data:")
        self.datFnLineEdit = QtWidgets.QLineEdit()
        self.datFnLineEdit.setMinimumWidth(100)
        # self.connect(self.datFnLineEdit, SIGNAL('editingFinished()'), self.file_load)
        self.datFnLineEdit.editingFinished.connect(self.file_load)
        fnLabel.setBuddy(self.datFnLineEdit)

        self.botton_open = QtWidgets.QPushButton("&Open")
        # self.connect(self.botton_open, SIGNAL('clicked()'), self.file_open)
        self.botton_open.clicked.connect(self.file_open)

        xLabel = QtWidgets.QLabel("&X Axis:")
        self.xSelComboBox = QtWidgets.QComboBox()
        self.xSelComboBox.setEditable(False)
        # self.connect(self.xSelComboBox, SIGNAL('currentIndexChanged(int)'), self.update_plot_data)
        self.xSelComboBox.currentIndexChanged.connect(self.update_plot_data)
        xLabel.setBuddy(self.xSelComboBox)

        # self.xSelComboBox.addItems([])

        yLabel = QtWidgets.QLabel("&Y Axis:")
        self.ySelList = QtWidgets.QListWidget()
        self.ySelList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection) # multiple selection
        # self.connect(self.ySelList, SIGNAL('itemSelectionChanged()'), self.update_plot_data)
        self.ySelList.itemSelectionChanged.connect(self.update_plot_data)
        yLabel.setBuddy(self.ySelList)
        # self.ySelList.addItems([])

        lgdLabel = QtWidgets.QLabel("Legend:")
        self.lgdLineEdit= QtWidgets.QLineEdit()
        # self.connect(self.lgdLineEdit, SIGNAL('editingFinished()'), self.set_legend)
        self.lgdLineEdit.editingFinished.connect(self.set_legend)
        lgdLabel.setBuddy(self.lgdLineEdit)
        self.lgdLineEdit.setToolTip('Use comma(,) to seperate legend text')

        grid = QtWidgets.QGridLayout()
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
            curDir = os.path.split(str(self.datFnLineEdit.text()))[0]
        except:
            curDir = ''

        datPath = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select File', curDir, "Data files (*.csv *.pkl)")

        if datPath: # canceled
            self.datFnLineEdit.setText(str(datPath[0]))
            self.file_load()


    def file_load(self):
        # load data into dataFrame
        datPath = str(self.datFnLineEdit.text())
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
        self.panel_fig = QtWidgets.QWidget()

        # Create the mpl Figure and FigCanvas objects.
        self.fig = Figure(figSize, dpi=figDPI)
        self.canvas = FigureCanvas(figure=self.fig)
        self.canvas.setParent(self.panel_fig)

        self.axes = self.fig.add_subplot(111)

        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.panel_fig)

        # figure control widgets
        self.botton_draw = QtWidgets.QPushButton("&Plot")
        # self.connect(self.botton_draw, SIGNAL('clicked()'), self.update_plot_data)
        self.botton_draw.clicked.connect(self.update_plot_data)
        
        self.chkbox_clear = QtWidgets.QCheckBox("&Clear")
        self.chkbox_clear.setChecked(True)

        self.chkbox_grid = QtWidgets.QCheckBox("&Grid")
        self.chkbox_grid.setChecked(True)
        # self.connect(self.chkbox_grid, SIGNAL('stateChanged(int)'), self.plot_mpl)

        self.chkbox_legend = QtWidgets.QCheckBox("&Legend")
        self.chkbox_legend.setChecked(True)
        # self.connect(self.chkbox_legend, SIGNAL('stateChanged(int)'), self.plot_mpl)

        self.slider_fontsz = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_fontsz.setRange(6, 36)
        self.slider_fontsz.setValue(10)
        self.slider_fontsz.setTickInterval(2)
        self.slider_fontsz.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider_fontsz.setTracking(True)
        self.slider_fontsz.valueChanged.connect(self.plot_mpl)
        updateToolTip = lambda s : self.slider_fontsz.setToolTip(str(s))
        self.slider_fontsz.valueChanged.connect(updateToolTip)
        sliderFontszLabel = QtWidgets.QLabel('&FontSize:')
        sliderFontszLabel.setBuddy(self.slider_fontsz)
        
        self.edit_fig_width = Float(low=0, high=16, step=0.01, digits=3, default=0, label="FigWidth")
        self.edit_fig_height = Float(low=0, high=16, step=0.01, digits=3, default=0, label="FigHeight")
        
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        for w in [sliderFontszLabel, self.slider_fontsz, 
                  self.edit_fig_width.labelText, self.edit_fig_width, 
                  self.edit_fig_height.labelText, self.edit_fig_height ]:
            hbox1.addWidget(w)
        for w in [self.botton_draw, self.chkbox_clear, self.chkbox_grid, self.chkbox_legend]:
            hbox2.addWidget(w)
            # hbox.setAlignment(w, Qt.AlignVCenter)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.panel_fig.setLayout(vbox)
    
    
    
    # def update_figure_mpl(self, figSize=(5,4), figDPI=100):
    #     ''' create matplotlib figure panel '''
    #     # Create the mpl Figure and FigCanvas objects.
    #     # self.fig.clear()
    #     self.fig = Figure(figSize, dpi=figDPI)
    #     self.canvas = FigureCanvas(figure=self.fig)
    #     self.canvas.setParent(self.panel_fig)
    #     self.axes = self.fig.add_subplot(111)
    #     self.mpl_toolbar = NavigationToolbar(self.canvas, self.panel_fig)
    

    def update_plot_data(self):
        self.xColName = str(self.xSelComboBox.currentText())
        self.yColNames = [ str(item.text())
                         for item in self.ySelList.selectedItems() ]

        if self.xColName in self.yColNames:
            self.yColNames.remove(self.xColName)

        if len(self.yColNames)>0:
            self.plot_mpl()

    
    def set_figure_size_editor(self, w, h):
        self.edit_fig_width.setValue(w)
        self.edit_fig_height.setValue(h)
        
    
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
        
        customFigW = self.edit_fig_width.getValue()
        customFigH = self.edit_fig_height.getValue()            
        currentFigSize = self.fig.get_size_inches()
        if customFigW==0 or customFigH==0: # fig size not given, init to current fig size
            self.set_figure_size_editor(currentFigSize[0], currentFigSize[1])
        elif currentFigSize[0]!=customFigW or currentFigSize[1]!=customFigH: # set to custom fig size
            self.fig.set_size_inches(self.edit_fig_width.getValue(), self.edit_fig_height.getValue(), forward=True)
        
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
        legnStr = str(self.lgdLineEdit.text())
        if len(legnStr)>0:
            legn = self.axes.get_legend()
            if legn is not None:
                for lt, ls in zip(legn.get_texts(), legnStr.split(',')):
                    lt.set_text(ls)
                self.canvas.draw() # refresh
                self.statusBar().showMessage('Legend updated', 2000)


    def save_plot(self):
        path = str(QtWidgets.QFileDialog.getSaveFileName(self, 'Save Image', '',
                                                   "Image files (*.png *.eps *.pdf *.jpg *.tif *.tiff)"))
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


    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
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


    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def on_about(self):
        msg = """ A very simple data plot tool based on PyQT & matplotlib.\nAuthor: RayN"""
        QtWidgets.QMessageBox.about(self, "About the app", msg.strip())


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)

    curFd = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QtGui.QIcon(os.path.join(curFd, 'icons', 'logo.png')))

    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
