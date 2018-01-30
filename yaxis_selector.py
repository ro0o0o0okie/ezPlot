# -*- coding: utf-8 -*-
"""
******************************             
* Filename: df_columns.py
* Author: RayN
* Created on 1/30/18
******************************
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSlot

import gui_base as gui




# def AsNamedWidget(wgt):
#     layout = QtWidgets.QHBoxLayout()
#     layout.addWidget(wgt.labelText)
#     layout.addWidget(wgt)
#     # layout.setContentsMargins(0,0,0,0)
#     # layout.setSpacing(5)
#     wgt.setLayout(layout)
#     # return wgt

class UserDefinedStyle(object):
    
    def __init__(self):
        super().__init__()
        self.line_style         = ''
        self.line_width_offset  = 0
        self.marker             = ''
        self.marker_size_offset = 0
        # self.line_color         = None
        # self.marker_facecolor   = None
        # self.marker_edgecolor   = None
    
    def __bool__(self):
        """ return True if any of the styles is given """
        return self.line_style or \
               self.line_width_offset or \
               self.marker or \
               self.marker_size_offset 
    
    
    def apply(self, line):
        """ apply user defined plot style to given line"""
        if self.line_style:     
            line.set_linestyle(self.line_style)
        if self.line_width_offset:     
            line.set_linewidth(self.line_width_offset + line.get_linewidth())
        if self.marker:         
            line.set_marker(self.marker)
        if self.marker_size_offset:    
            line.set_markersize(self.marker_size_offset + line.get_markersize())
        # if self.line_color is not None:     
        #     line.set_color(self.line_color)
        # if self.marker_facecolor is not None: 
        #     line.set_markerfacecolor(self.marker_facecolor)
        # if self.marker_edgecolor is not None: 
        #     line.set_markeredgecolor(self.marker_edgecolor)
    

class StyleModifier(QtWidgets.QWidget):
    
    signal_modified = QtCore.pyqtSignal(str)
    
    def __init__(self, colName:str, parent=None, connectFunc=None):
        super().__init__(parent)     
        if connectFunc: 
            self.signal_modified.connect(connectFunc)
        
        self.col_name = colName
        self.editor_line_style = gui.ComboBox(   
            label='LineStyle', 
            textList=['','-','--','-.',':'], 
            default='' )
        self.editor_line_width = gui.Float(      
            label='LineWidth(+/-)', 
            low=-50, high=50, step=0.1, default=0, digits=2)
        self.editor_marker = gui.ComboBox(   
            label='Marker',
            textList=['', 'o','>','<', 'v','^', 's', 'D', 'd', 'h','H'], 
            default='')
        self.editor_marker_size = gui.Float(      
            label='MarkerSize(+/-)', 
            low=-50, high=50, step=0.2, default=0, digits=2)
        
        self.editor_line_style.currentIndexChanged.connect(self.valueModified)
        self.editor_line_width.valueChanged.connect(self.valueModified)
        self.editor_marker.currentIndexChanged.connect(self.valueModified)
        self.editor_marker_size.valueChanged.connect(self.valueModified)

        self.setLayout(
            gui.MakeFormLayout([
                self.editor_line_style, 
                self.editor_line_width, 
                self.editor_marker, 
                self.editor_marker_size ])
        )
    
    def valueModified(self):
        self.signal_modified.emit(self.col_name)
    


class DataFrameTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel('DataFrameTree')
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection) # allow multiple selection
        self.setRootIsDecorated(True)
        self.setIndentation(20)



class DataFrameNode(QtWidgets.QTreeWidgetItem):
    """ A dataframe node, with multiple column names as sub-node,
        column sub-node's child is customs style widgets
    """
    def __init__(self, dfName, columns, parent:DataFrameTree,
                 anyStyleChangedCallback=None, activeStyleChangedCallback=None):
        assert parent is not None
        super().__init__(parent)
        self._cbk_any_changed = anyStyleChangedCallback # callback if any one of the columns style changed
        self._cbk_active_changed = activeStyleChangedCallback # callback if the active/selected columns style changed
        
        self.tree = parent
        self.setText(0, dfName)
        self.setFlags(Qt.ItemIsEnabled) #| Qt.ItemIsEditable)
        self.tree.addTopLevelItem(self)
        
        self.column_names = columns
        self.column_user_styles = { c : UserDefinedStyle() for c in columns } # columnName => userStyleObj
        self.column_items = {}
        
        
        for colname, usrsty in self.column_user_styles.items():
            col = self.column_items[colname] = QtWidgets.QTreeWidgetItem(self)
            col.setText(0, colname)
            col.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
            
            styleModifier = QtWidgets.QTreeWidgetItem(col)
            styleModifier.setFlags(Qt.ItemIsEnabled) # not selectable
            # styleModifier.parent().isSelected()
            modifier = StyleModifier(colName=colname, connectFunc=self.callback) # self.makeStyleModifierWidget(callback=styleChangedCallback)
            self.tree.setItemWidget(styleModifier, 0, modifier)
    
    @pyqtSlot(str)
    def callback(self, colname:str):
        if self._cbk_any_changed:
            self._cbk_any_changed(colname)
        if self._cbk_active_changed:
            if self.column_items[colname].isSelected():
                self._cbk_active_changed(colname)
    
    
    # def makeStyleModifierWidget(self, callback=None):
    #     """ make the widget for user style control """
    #     comboLs = gui.ComboBox(   
    #         label='LineStyle', 
    #         textList=['','-','--','-.',':'], 
    #         default='' )
    #     editorLw = gui.Float(      
    #         label='LineWidth(+/-)', 
    #         low=-50, high=50, step=0.1, default=0, digits=2)
    #     comboMk = gui.ComboBox(   
    #         label='Marker',
    #         textList=['', 'o','>','<', 'v','^', 's', 'D', 'd', 'h','H'], 
    #         default='')
    #     editorMs = gui.Float(      
    #         label='MarkerSize(+/-)', 
    #         low=-50, high=50, step=0.2, default=0, digits=2)
    #     
    #     if callback:
    #         comboLs.currentIndexChanged.connect(callback)
    #         editorLw.valueChanged.connect(callback)
    #         comboMk.currentIndexChanged.connect(callback)
    #         editorMs.valueChanged.connect(callback)
    #         
    #     w = QtWidgets.QWidget()
    #     w.setLayout(gui.MakeFormLayout([comboLs, editorLw, comboMk, editorMs]))
    #     return w
        
    
    def getUserStyles(self, col:str):
        return self.column_user_styles[col]
    
    


