# -*- coding: utf-8 -*-
"""
******************************             
* Filename: gui_base.py
* Author: RayN
* Created on 2016/1/3
******************************
RayN's GUI base type widgets definition.

Python 3 only.
"""
###############################################################################

import os
import sys
import numpy as np
from os.path import split, abspath, exists
from collections import OrderedDict, Iterable, Mapping

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QTextCursor
from PyQt5.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, \
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLayout, QLineEdit, QMessageBox, \
    QPushButton, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, \
    QTextEdit, QVBoxLayout, QWidget, QListWidget, QAbstractItemView, QSizePolicy


###############################################################################
# TODO
# def makeProgressBar(self):
#     pbar = QProgressBar(self)
#     style ="""
#     QProgressBar {
#         border: 2px solid grey;
#         border-radius: 5px;
#         text-align: center;
#     }
#     QProgressBar::chunk {
#         background-color: #37DA7E;
#         width: 20px;
#     }"""
#     pbar.setStyleSheet(style)
#     # self.pbar.setMaximumHeight(10)
#     # self.pbar.setMinimumWidth(400)
#     return pbar
#
# def addProgressBar(self, num):
#     self.pbar.setValue(self.pbar.value()+num)
#
# # def expandProgressBarMax(self, num):
# #     """ expand progress bar range. """
# #     self.pbar.setMaximum(self.pbar.maximum()+num)


def absjoin(path, *paths):
    return os.path.abspath(os.path.join(path, *paths))


def SetEnabledInLayout(lay, boolval=True):
    """ enable or disable all widgets inside layout. """
    for i in range(lay.count()):
        wgt = lay.itemAt(i).widget()
        if isinstance(wgt, QWidget): # skip QSpacerItem
            wgt.setEnabled(boolval)


def MakeVertLine():
    """ draw a line widget for gui split.
    http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    """
    frame = QFrame()
    frame.setFrameShape(QFrame.VLine)
    frame.setFrameShadow(QFrame.Sunken)
    return frame


def MakeHrznLine():
    """ draw a line widget for gui split.
    http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    """
    frame = QFrame()
    frame.setFrameShape(QFrame.HLine)
    frame.setFrameShadow(QFrame.Sunken)
    return frame


def MakePushButton(labelText, clickFunc=None,
                   minWidth=None, maxWidth=None, minHeight=None, maxHeight=None, default=False, tooltip=None):
    btn = QPushButton(labelText)
    if tooltip : btn.setToolTip(tooltip)
    if minWidth is not None  : btn.setMinimumWidth(minWidth)
    if maxWidth is not None  : btn.setMaximumWidth(maxWidth)
    if minHeight is not None : btn.setMinimumHeight(minHeight)
    if maxHeight is not None : btn.setMaximumHeight(maxHeight)
    if clickFunc is not None : btn.clicked.connect(clickFunc)
    btn.setDefault(default)
    btn.setAutoDefault(False)
    return btn


def MakeVBoxLayout(widgets):
    """make Vbox layout with gievn widgets/layout. """
    vbox = QVBoxLayout()
    for w in widgets:
        if isinstance(w, QWidget):
            vbox.addWidget(w)
        elif isinstance(w, QLayout):
            vbox.addLayout(w)
        elif isinstance(w, int):
            vbox.addStretch(w)
        else:
            raise TypeError
    return vbox


def MakeHBoxLayout(widgets):
    """make Hbox layout with gievn widgets/layout. """
    hbox = QHBoxLayout()
    for w in widgets:
        if isinstance(w, QWidget):
            hbox.addWidget(w)
        elif isinstance(w, QLayout):
            hbox.addLayout(w)
        elif isinstance(w, int):
            hbox.addStretch(w)
        else:
            raise TypeError('type:%s'%type(w))
    return hbox


def MakeFormLayout(wgts, fillLayout=None):
    """ Make form layout from the ordered widget dict.
        - wgts: ordered dict of widgets or list of widgets.
        - fillLayout: the form layout to append widgets to.
    """
    if fillLayout is not None:
        formlay = fillLayout # fill in given formlayout
    else: # make new formlayout
        formlay = QFormLayout()
    formlay.setFieldGrowthPolicy(2) # AllNonFixedFieldsGrow

    wgtsItr = iter(wgts.values()) if isinstance(wgts, Mapping) else wgts
    for wgt in wgtsItr:
        if hasattr(wgt, 'layoutInited') and not wgt.layoutInited:
            wgt.initLayout() # make layout if not inited before (for sub WidgetPage or GroupBox)
            formlay.addRow(wgt)
        else:
            if hasattr(wgt, "labelText") and wgt.labelText is not None:
                formlay.addRow(wgt.labelText, wgt)
            else:
                formlay.addRow(wgt)
    return formlay


def MakeTabWidget(wgts):
    """ make tab widgets. """
    tabs = QTabWidget()
    wgtIter = iter(wgts.values()) if isinstance(wgts, Mapping) else wgts
    for wgt in wgtIter:
        if hasattr(wgt, 'layoutInited') and not wgt.layoutInited:
            wgt.initLayout()
        tabs.addTab(wgt, wgt.labelText)
    return tabs


class WidgetsPage(QWidget, object):
    """A basic page widget with some config wgts"""
    def __init__(self, parent=None, hierarchyKey=None):
        super(WidgetsPage, self).__init__(parent)
        self.layoutInited = False # used for checking whether layout is maked
        self._widgets = OrderedDict() # wgtName => wgtObj
        self._hrkey = hierarchyKey

    def initLayout(self, extraWgtRows=None, usetabs=False):
        """make form layout from widgets"""
        if not self.layoutInited:
            if not usetabs: # form layout for base widgets
                lay = MakeFormLayout(self._widgets)
                if extraWgtRows is not None: # add extra rows (pushbuttons, etc..)
                    lay = MakeFormLayout(extraWgtRows, lay)
            else: # tabbed layout for widget pages
                lay = MakeVBoxLayout([MakeTabWidget(self._widgets)])
            self.setLayout(lay)
            self.layoutInited = True

    def setDefault(self, wgtNames=None):
        """reset wgts value to default"""
        if wgtNames is not None: # reset specified wgts
            for k in wgtNames:
                self._widgets[k].setDefault()
        else: # reset all wgts
            for w in self._widgets.values():
                w.setDefault()

    def setValues(self, valDict):
        """set wgts value by given value dict. """
        if self._hrkey is not None and self._hrkey in valDict:
            self.setValues(valDict[self._hrkey])
        for k, w in self._widgets.items():
            if isinstance(w, (GroupBox, WidgetsPage)):
                w.setValues(valDict)
            else:
                if k in valDict:
                    w.setValue(valDict[k])

    def getValueDict(self):
        """ return wgts value as dict. """
        valDict = {}
        for key, wgt in self._widgets.items():
            if isinstance(wgt, (GroupBox, WidgetsPage)):
                valDict.update(wgt.getValueDict())
            else:
                valDict[key] = wgt.getValue()
        if self._hrkey is not None:  # hierarchy
            return {self._hrkey: valDict}
        else:  # flat
            return valDict
        # return valDict

    def getWidget(self, wgtName):
        return self._widgets[wgtName]

    def getWidgetValue(self, wgtName, valuedict=False):
        """ return page widget's value.
            NOTE: can not return sub-widgets' value (i.e. widgets inside GrounpBox etc.)
        """
        if valuedict:
            return self._widgets[wgtName].getValueDict()
        else:
            return self._widgets[wgtName].getValue()

    def addWidget(self, wgtName, wgtObj):
        self._widgets[wgtName] = wgtObj
        return wgtObj


class GroupBox(QGroupBox):
    """ Group basic type widgets together.
        GroupBox in GroupBox recursion is allowed.
        Can be used as:
            + a group ON/OFF widget with real config key&value
            + a logic group for put some widgets together (usually corresponding to a config sub-dict)
        If GroupBox is checkable, then its check status is a config var;
        Uncheckable GroupBox is not saved as config, for visual identification:
            wgts['_GroupBox_Xxxxx'] = GroupBox(...)
    """
    def __init__(self, wgtsDict=None, label="GroupBox",
                 chkKey=None, defaultChk=False, hierarchyKey=None, connectFunc=None,
                 tooltip=None):
        """
        wgtsDict: widgets to be groupped. { wgtName=>wgtObj }
        chkKey: if groupbox self is a binary (True/False) config value, use this key to store config
        defaultChk: the default value of groupbox check status
        hierarchyKey: if group's wgts config are in sub-dict, use this as sub-dict key in config, i.e.
            { hierarchyKey=>{ wgtName=>wgtValue } }
        """
        super(GroupBox, self).__init__(label)
        self.layoutInited = False # used for checking whether layout is maked
        self._widgets = OrderedDict() if wgtsDict is None else wgtsDict
        self._hrkey = hierarchyKey
        if chkKey is not None: # check status depends on config
            self.setCheckable(True)
            self.setChecked(defaultChk)
            self._chkKey = chkKey # chkKey => (True/False) check status
            self._defaultChk = defaultChk
            if connectFunc is not None: # when check status changed call connectFunc(idx)
                self.toggled.connect(connectFunc)
        if tooltip is not None:
            self.setToolTip(tooltip)

    def initLayout(self, extraWgtRows=None):
        """make formlayout from widgets"""
        if not self.layoutInited:
            formlay = MakeFormLayout(self._widgets)
            if extraWgtRows is not None: # add extra rows (pushbuttons, etc..)
                formlay = MakeFormLayout(extraWgtRows, formlay)
            self.setLayout(formlay)
            self.layoutInited = True

    def addWidget(self, wgtName, wgtObj):
        self._widgets[wgtName] = wgtObj
        return wgtObj

    def setDefault(self):
        for wgt in self._widgets.values():
            wgt.setDefault()
        if self.isCheckable():
            self.setChecked(self._defaultChk)

    def setValues(self, valDict):
        """set groupped wgts value. """
        if self._hrkey is not None and self._hrkey in valDict:
            self.setValues(valDict[self._hrkey])
        # set self value if checkable
        if self.isCheckable() and self._chkKey in valDict:
            self.setChecked(valDict[self._chkKey])
        # set in group wgts value
        for key, wgt in self._widgets.items():
            if isinstance(wgt, GroupBox):
                wgt.setValues(valDict)
            elif key in valDict:
                wgt.setValue(valDict[key])

    def setValue(self, key, val):
        self._widgets[key].setValue(val)

    def getValueDict(self):
        valDict = {}
        if self.isCheckable():
            valDict[self._chkKey] = self.isChecked()
        for key, wgt in self._widgets.items():
            if isinstance(wgt, GroupBox):
                valDict.update(wgt.getValueDict())
            else:
                valDict[key] = wgt.getValue()
        if self._hrkey is not None: # hierarchy
            return {self._hrkey:valDict}
        else: # flat
            return valDict

    def getWidget(self, wgtName):
        return self._widgets[wgtName]

    def getWidgetsIter(self):
        return iter(self._widgets.values())

    def getWidgetValue(self, wgtName, valuedict=False):
        """ return page widget's value.
            NOTE: can not return sub-widgets' value (i.e. widgets inside GrounpBox etc.)
        """
        if valuedict:
            return self._widgets[wgtName].getValueDict()
        else:
            return self._widgets[wgtName].getValue()

    def enable(self, boolVal):
        self.setEnabled(boolVal)

    def disable(self, bool):
        self.setDisabled(bool)


class TextBox(QTextEdit):
    """ textbox for info printing. """
    def __init__(self, default=None, readonly=True, fontsize=9, minWidth=50, minHeight=10,
                 txColor=None, bgColor=None):
        super(TextBox, self).__init__()
        self.setColor(txColor, bgColor)
        # self.setFontFamily('microsoft yahei, consolas')
        self.setFontPointSize(fontsize)

        self._default = default if default is not None else "Hello World!"
        self.setReadOnly(readonly)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setDefault()
        self.setMinimumSize(minWidth, minHeight)

    def write(self, text, prefix=None, newline=True):
        text = text if prefix is None else prefix + text
        if newline:
            self.append(text)
            self.moveCursor(QTextCursor.End)
        else:
            self.insertPlainText(text)
            self.moveCursor(QTextCursor.End)
        # sbar = self.verticalScrollBar()
        # sbar.setValue(sbar.maximum())

    def setColor(self, txColor=None, bgColor=None):
        if txColor:
            self.setTextColor(txColor)
        if bgColor:
            p = QPalette()
            p.setColor(p.Base, bgColor)
            self.setPalette(p)

    def setValue(self, text):
        self.setPlainText(text)

    def setDefault(self):
        """ reset to default value. """
        self.clear()
        self.setPlainText(self._default)

    def getValue(self):
        return self.toPlainText()

    def getLines(self):
        return self.toPlainText().split('\n')

    def enable(self, bool):
        self.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)

######################################################################
# basic data type widgets
######################################################################

class Text(QLineEdit):
    def __init__(self, default=None, minWidth=64, label="Text", readonly=False ,tooltip=None):
        super(Text, self).__init__()
        self._tooltip = tooltip
        self.labelText = QLabel(label+':')
        self._default = default if default is not None else ""
        self.setDefault()
        self.setMinimumWidth(minWidth)

        if readonly : self.enable(False)
        if tooltip  : self.setToolTip(tooltip)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # horizon fill

    def setValue(self, text):
        self.setText(text)
        if self._tooltip is None: # use value as tooltip
            self.setToolTip(text)

    def setDefault(self):
        """ reset to default value. """
        self.setValue(self._default)

    def getValue(self):
        return str(self.text())

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)


class Int(QSpinBox):
    def __init__(self, low, high, step, default=None,
                 prefix=None, suffix=None, readonly=False, minWidth=50, label="Integer", tooltip=None):
        super(Int, self).__init__()
        self.labelText = QLabel(label+':')
        self.default = default if default is not None else low # use 'low' as default if not given
        self.setRange(low, high)
        self.setSingleStep(step)
        self.setDefault() # after setRange
        if prefix is not None : self.setPrefix(prefix)
        if suffix is not None : self.setSuffix(suffix)
        if readonly : self.enable(False) # self.setReadOnly(True)
        if tooltip  : self.setToolTip(tooltip)
        self.setMinimumWidth(minWidth)
        self.setFocusPolicy(Qt.StrongFocus) # diable wheel focus
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # horizon fill
    # def setValue(self, val):
    #     super(Int, self).setValue(val)

    def wheelEvent(self, event):
        """ overide default wheel envent to prevent accidently changing value by scrolling.
        """
        pass

    def setDefault(self):
        """ reset to default value. """
        self.setValue(self.default)

    def getValue(self):
        return int(self.value())

    def getLimit(self):
        """ widget min & max limit """
        return self.minimum(), self.maximum()

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)


class Float(QDoubleSpinBox):
    def __init__(self, low, high, step, digits=3, default=None,
                 prefix=None, suffix=None, readonly=False, minWidth=50, label="Float", tooltip=None):
        super(Float, self).__init__()
        self.labelText = QLabel(label+':')
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
        self.setFocusPolicy(Qt.StrongFocus) # diable wheel focus
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # horizon fill

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


class CheckBox(QCheckBox):
    def __init__(self, default=False, label='CheckBox', connectFunc=None, tooltip=None):
        super(CheckBox, self).__init__(label)
        self._default = Qt.Checked if default else Qt.Unchecked
        self.setTristate(False)
        self.setDefault()
        if tooltip  : self.setToolTip(tooltip)
        if connectFunc is not None:
            self.stateChanged.connect(connectFunc)

    def setDefault(self):
        """ reset to default value. """
        self.setCheckState(self._default)

    def setValue(self, val):
        state = Qt.Checked if bool(val) else Qt.Unchecked
        self.setCheckState(state)

    def getValue(self):
        return self.isChecked()

    def enable(self, bool):
        self.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)


class ComboBox(QComboBox):
    def __init__(self, textList, valueList=None, default=None, readonly=False, minWidth=80,
                 label="ComboBox", tooltip=None, connectFunc=None):
        """
        textList: displayed selection text
        valueList: the real selection value corresponding to textList
        default: default selected value
        """
        super(ComboBox, self).__init__()
            
        self._tooltip = tooltip
        self.labelText = QLabel(label+':')
        
        self.resetItems(textList, valueList, default)
        self.setEditable(False)
        self.view().setSpacing(1)
        if readonly : self.enable(False)
        if tooltip  : self.setToolTip(tooltip)
        # self.view().setSpacing(1) # space between list items
        # self.view().setMinimumWidth(100)
        self.setMinimumWidth(minWidth)
        if connectFunc is not None: # when idx changed call connectFunc(idx)
            self.currentIndexChanged.connect(connectFunc)
    
    def resetItems(self, textList, valueList=None, default=None):
        """"""
        if valueList:
            assert len(textList)==len(valueList)
        else:
            valueList = textList
        self.textList = textList
        self.valueList = valueList
        
        self.clear()
        for text in textList:
            self.addItem(text)
            
        self._default = default
        self.setDefault()
        
    
    def setConnectFunc(self, func):
        self.currentIndexChanged.connect(func)

    def setValue(self, val):
        idx = self.valueList.index(val)
        self.setCurrentIndex(idx)
        if self._tooltip is None: # use value as tooltip
            self.setToolTip(str(self.itemText(idx)))

    def setDefault(self):
        """ reset to default value. """
        if self._default is not None:
            self.setValue(self._default)

    def getValue(self):
        """ return current selected value.  """
        return self.valueList[self.currentIndex()]

    def getText(self):
        """ return current selected text. """
        return self.textList[self.currentIndex()]

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)


class List(QListWidget):
    def __init__(self, items, default=None, multiple=True, readonly=False, minWidth=80,
                 label="List", tooltip=None, connectFunc=None):
        """
        items: text items in list widget.
        multiple: allow multiple selection.
        default: iterable selected items.
        """
        super(List, self).__init__()
        self._tooltip = tooltip
        self.labelText = QLabel(label+':')
        self.resetItems(items, default)
        # self._items = items
        # self.addItems(items)
        # self._default = default
        # self.setDefault()

        if multiple:
            self.setSelectionMode(QAbstractItemView.ExtendedSelection) # multiple selection
        else:
            self.setSelectionMode(QAbstractItemView.SingleSelection)

        if connectFunc is not None:
            self.itemSelectionChanged.connect(connectFunc)

        if readonly : self.enable(False)
        if tooltip  : self.setToolTip(tooltip)

        self.setMinimumWidth(minWidth)

    def setConnectFunc(self, func):
        self.itemSelectionChanged.connect(func)

    def resetItems(self, items, default=None):
        self.clear()
        self._items = items
        self.addItems(items)
        self._default = default
        self.setDefault()
    
    def setItemText(self, idx, text):
        self.item(idx).setText(text)
        
    def getItems(self):
        return self._items
    
    def getIdx(self, text):
        return self._items.index(text)
    
    def setValue(self, val):
        self.clearSelection()
        if isinstance(val, Iterable): # multiple items
            for v in val:
                if v in self._items:
                    self.item(self._items.index(v)).setSelected(True)
        else: # given single item text
            if val in self._items:
                self.item(self._items.index(val)).setSelected(True)

    def setDefault(self):
        """ reset to default value. """
        if self._default is not None:
            self.setValue(self._default)

    def getValue(self):
        """ return current selected value.  """
        # self.currentIndex()
        return [str(v.text()) for v in self.selectedItems()]

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)


class Array(QTableWidget):
    def __init__(self, default=None, shape=None,
                 colHeader=(), rowHeader=(), label="Array", tooltip=None):
        """NOTE: suffix may cause error when read data from the cell text"""
        super(Array, self).__init__()
        self.labelText = QLabel(label+':')
        self.default = np.asarray(default) if default is not None else np.zeros(shape)
        if self.default.ndim==1:
            self.default = self.default[None,:] # 1d -> 2d
        nRow, nCol = self.default.shape
        self.setRowCount(nRow)
        self.setColumnCount(nCol)

        if len(colHeader):
            self.setHorizontalHeaderLabels(colHeader[:nCol])
        else: # hide header if label not given
            self.horizontalHeader().setVisible(False)

        if len(rowHeader):
            self.setVerticalHeaderLabels(rowHeader[:nRow])
        else:
            self.verticalHeader().setVisible(False)

        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setResizeMode(QHeaderView.Stretch)

        # init table cells
        for i in range(nRow):
            for j in range(nCol):
                cellText = str(self.default[i,j])
                item = QTableWidgetItem(cellText)
                item.setTextAlignment(Qt.AlignCenter) # align center
                self.setItem(i, j, item)

        # table size constrait
        # self.resizeRowsToContents()
        self.setMinimumHeight(self.rowHeight(0)*(nRow+1.8))
        if tooltip:
            self.setToolTip(tooltip)

    def setValue(self, valArr):
        nRow, nCol = self.rowCount(), self.columnCount()
        valArr = np.asarray(valArr)
        assert valArr.shape==(nRow, nCol)
        for i in range(nRow):
            for j in range(nCol):
                self.item(i, j).setText(str(valArr[i,j]))

    def setDefault(self):
        """ reset to default value. """
        self.setValue(self.default)

    def getValue(self):
        nRow, nCol = self.rowCount(), self.columnCount()
        valArr = np.zeros([nRow, nCol])
        for i in range(nRow):
            for j in range(nCol):
                item = self.item(i, j)
                if item is not None:
                    valArr[i,j] = float(item.text())

        return valArr.tolist() # return data array as list for yaml save

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)


class File(QWidget):
    """ A LineEdit with file path and a botton for file selection. """
    def __init__(self, default=None, minWidth=80, label="FilePath", chkFile=True, readonly=False,
                 dlgTitle='选择指定文件', dlgDir=None, dlgFilter='(*.*)',  tooltip=None, 
                 selectedPostFunc=None):
        super(File, self).__init__()
        self._dlg_title = dlgTitle
        self._dlg_dir = dlgDir
        self._dlg_filter = dlgFilter
        self._tooltip = tooltip
        self._selectedPostFunc = selectedPostFunc

        self.labelText = QLabel(label+':')
        self.text = QLineEdit()
        self.text.setMinimumWidth(minWidth)
        self.default = abspath(default) if default and exists(abspath(default)) else ""
        self.setDefault()
        if tooltip  : self.text.setToolTip(tooltip)
        if chkFile  : self.text.editingFinished.connect(self.checkFile)
        if readonly : self.enable(False)

        self.button = MakePushButton("选择", clickFunc=self.selectFile, tooltip='选择指定文件',
                                     maxWidth=80)
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.button)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.setLayout(layout)

    def checkFile(self):
        """ init user-defined working dir. """
        filePath = str(self.text.text())
        if len(filePath) and not exists(filePath):
            QMessageBox.warning(self, "注意", "找不到文件<%s>，请检查输入路径是否正确！"%filePath)

    def selectFile(self):
        if self._dlg_dir is None:
        # use current date path as default open dir
            curDir = os.path.dirname(self.getValue()) # split(unicode(self.text.text()))[0]
        else:
            curDir = self._dlg_dir
        fileName, _ = QFileDialog.getOpenFileName(self, self._dlg_title, curDir, self._dlg_filter)
        if fileName: # selected
            self.text.setText(abspath(fileName))
            if self._selectedPostFunc:
                self._selectedPostFunc()

    def setValue(self, fileName):
        self.text.setText(fileName)
        if self._tooltip is None: # use value as tooltip
            self.setToolTip(fileName)

    def setDefault(self):
        """ reset to default value. """
        self.setValue(self.default)

    def getValue(self):
        return str(self.text.text())

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)


class Path(QWidget):
    """ A LineEdit with file path and a botton for path selection. """
    def __init__(self, default='./', chkDir=False, minWidth=80, label="FilePath", readonly=False, tooltip=None):
        super(Path, self).__init__()
        self._tooltip = tooltip
        self.labelText = QLabel(label+':')
        self.text = QLineEdit()
        self.text.setMinimumWidth(minWidth)
        self.labelText.setBuddy(self.text)

        if chkDir: # check give path existence
            self.text.editingFinished.connect(self.checkPath)

        self._default = abspath(default)
        self.setDefault()

        if readonly : self.enable(False)
        if tooltip  : self.text.setToolTip(tooltip)

        self.button = MakePushButton("选择", tooltip='选择指定目录', maxWidth=80,
                                      clickFunc=self.selectPath,)
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.button)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.setLayout(layout)

    def checkPath(self):
        filePath = str(self.text.text())
        if len(filePath) and not exists(filePath):
            QMessageBox.warning(self, "注意", "找不到指定的路径，请检查输入路径是否正确！")

    def selectPath(self):
        try: # use current date path as default open dir
            curDir = split(str(self.text.text()))[0]
        except:
            curDir = ''
        fileName, _ = QFileDialog.getExistingDirectory(self, '选择指定路径', curDir)
        if fileName: # selected
            self.text.setText(abspath(fileName))

    def setValue(self, fileName):
        self.text.setText(fileName)
        if self._tooltip is None: # use value as tooltip
            self.setToolTip(fileName)

    def setDefault(self):
        """ reset to default value. """
        self.setValue(self._default)

    def getValue(self):
        return os.path.normpath(str(self.text.text()))

    def enable(self, bool):
        self.setEnabled(bool)
        self.labelText.setEnabled(bool)

    def disable(self, bool):
        self.setDisabled(bool)
        self.labelText.setDisabled(bool)