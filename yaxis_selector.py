# -*- coding: utf-8 -*-
"""
******************************             
* Filename: df_columns.py
* Author: RayN
* Created on 1/30/18
******************************
"""
import os
from collections import OrderedDict

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
        return bool(
            self.line_style or self.line_width_offset or self.marker or self.marker_size_offset )
    
    
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
    
    signal_style_changed = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.style = UserDefinedStyle()
        # if connectFunc: 
        #     self.signal_modified.connect(connectFunc)
        
        # self.col_name = colName
        self.editor_line_style = gui.ComboBox(   
            label='LineStyle', 
            textList=['','-','--','-.',':'], 
            default=self.style.line_style )
        self.editor_line_width_offset = gui.Float(      
            label='LineWidth(+/-)', 
            low=-50, high=50, step=0.1, 
            default=self.style.line_width_offset, digits=2)
        self.editor_marker = gui.ComboBox(   
            label='Marker',
            textList=['', 'o','>','<', 'v','^', 's', 'D', 'd', 'h','H'], 
            default=self.style.marker)
        self.editor_marker_size_offset = gui.Float(      
            label='MarkerSize(+/-)', 
            low=-50, high=50, step=0.2, 
            default=self.style.marker_size_offset, digits=2)
        
        self.editor_line_style.currentIndexChanged.connect(self.valueModified)
        self.editor_line_width_offset.valueChanged.connect(self.valueModified)
        self.editor_marker.currentIndexChanged.connect(self.valueModified)
        self.editor_marker_size_offset.valueChanged.connect(self.valueModified)

        self.setLayout(
            gui.MakeFormLayout([
                self.editor_line_style, 
                self.editor_line_width_offset, 
                self.editor_marker, 
                self.editor_marker_size_offset ])
        )
    
    @pyqtSlot()
    def valueModified(self):
        self.style.line_style = self.editor_line_style.getValue()
        self.style.line_width_offset = self.editor_line_width_offset.getValue()
        self.style.marker = self.editor_marker.getValue()
        self.style.marker_size_offset = self.editor_marker_size_offset.getValue()
        self.signal_style_changed.emit()
    
    def getStyle(self) -> UserDefinedStyle:
        return self.style



class DataFrameTree(QtWidgets.QTreeWidget):
    
    
    signal_column_renamed = QtCore.pyqtSignal(tuple) # (fn, oldName, newName) 
    signal_active_style_changed = QtCore.pyqtSignal() 
    
    # signal_colnode_renamed = QtCore.pyqtSignal(tuple) # (oldName, newName)
    # signal_colnode_selected_and_style_changed = QtCore.pyqtSignal()
    
    
    def __init__(self, label='DataFrameTree', parent=None):
        super().__init__(parent)
        # self.setHeaderLabel('DataFrameTree')
        self.setHeaderHidden(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection) # allow multiple selection
        self.setRootIsDecorated(True)
        self.setIndentation(20)
        self.labelText = QtWidgets.QLabel(label+':')
        
        self.df_nodes = OrderedDict() # fn => DataFrameNode
    
    def addDataFrame(self, datafn, columns):
        if datafn in self.df_nodes:
            self.df_nodes[datafn].updateColumns(columnNames=columns)
        else:
            self.df_nodes[datafn] = \
                DataFrameNode( parent=self, datafn=datafn, columnNames=columns )
        return self.df_nodes[datafn]
        
        
    def getSelectedColumns(self):
        nodes = {} # fn => [selected column nodes]
        for fn, dfnode in self.df_nodes.items():
            cols = dfnode.getSelectedColumns()
            if cols:
                nodes[fn] = cols
        return nodes
    
    # def getSelectedColumnNames(self, excludeName=None):
    #     names = {} # fn => [selected column names]
    #     for fn, cols in self.getSelectedColumns().items():
    #         if excludeName:
    #             names[fn] = [col.column_name for col in cols if cols.column_name!=excludeName]
    #         else:
    #             names[fn] = [col.column_name for col in cols]
    #     return names
    
    

class DataFrameNode(QtWidgets.QTreeWidgetItem):
    """ A dataframe node, with multiple column names as sub-node,
        column sub-node's child is customs style widgets
    """
    # signal_column_renamed = QtCore.pyqtSignal(tuple) # (fn, oldName, newName) 
    # signal_active_style_changed = QtCore.pyqtSignal() 
    
    def __init__(self, datafn, columnNames, parent:DataFrameTree,
                 # activeStyleChangedCallback=None,  # f()
                 # columnRenamedCallback=None  # f()
                 ):
        assert parent is not None
        super().__init__(parent)
        # self._cbk_any_style_changed = anyStyleChangedCallback # callback if any one of the columns style changed
        # self._cbk_active_style_changed = activeStyleChangedCallback # callback if the active/selected columns style changed
        self._hash = hash(datafn) # constant
        self.datafile = datafn
        self.dfname = os.path.basename(datafn) # can be renamed by user
        self.setText(0, self.dfname)
        self.tree = parent
        self.tree.addTopLevelItem(self)
        self.setFlags(Qt.ItemIsEnabled) #| Qt.ItemIsEditable)
        
        # self.column_names = columns
        # self.column_user_styles = { c : UserDefinedStyle() for c in columns } # columnName => userStyleObj
        self.column_nodes = [ DataColumnNode(colname=cn, parent=self) for cn in columnNames ] 
        # for col in self.column_nodes:
        #     print(col.signal_renamed, type(col.signal_renamed))
        #     col.signal_renamed.connect(self.onColumnRenamed)
        #     col.signal_selected_and_style_changed.connect(self.onActiveStyleChanged)
        
        # for colname, usrsty in self.column_user_styles.items():
        #     col = self.column_items[colname] = QtWidgets.QTreeWidgetItem(self)
        #     col.setText(0, colname)
        #     col.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
        #     # col.
        #     styleModifier = QtWidgets.QTreeWidgetItem(col)
        #     styleModifier.setFlags(Qt.ItemIsEnabled) # not selectable
        #     # styleModifier.parent().isSelected()
        #     modifier = StyleModifier(colName=colname, connectFunc=self.onStyleChanged) # self.makeStyleModifierWidget(callback=styleChangedCallback)
        #     self.tree.setItemWidget(styleModifier, 0, modifier)
    
    # @pyqtSlot(tuple) # (oldName, newName)
    # def onColumnRenamed(self, names:tuple):
    #     self.signal_column_renamed.emit((self.datafile, *names))
    # 
    # @pyqtSlot()
    # def onActiveStyleChanged(self):
    #     self.signal_active_style_changed.emit()
        
    # def onStyleChanged(self, colname:str):
    #     # if self._cbk_any_style_changed:
    #     #     self._cbk_any_style_changed(colname)
    #     if self._cbk_active_style_changed:
    #         if self.column_items[colname].isSelected():
    #             self._cbk_active_style_changed(colname)
    
    def __hash__(self):
        return self._hash
    
    def updateColumns(self, columnNames):
        for c in self.column_nodes:
            self.removeChild(c)
        self.column_nodes.clear()
        self.column_nodes = [ DataColumnNode(colname=cn, parent=self) for cn in columnNames ] 
        
    
    def getSelectedColumns(self):
        return [col for col in self.column_nodes if col.isSelected()]
        
    # def getSelectedColumnNames(self):
    #     return [col.column_name for col in self.column_nodes if col.isSelected()] 
    
    
    # def getUserStyles(self, col:str):
    #     return self.column_user_styles[col]
    
    

class DataColumnNode(QtWidgets.QTreeWidgetItem):
    """A column name node, and its style modifier """
    # signal_renamed = QtCore.pyqtSignal(tuple) # (oldName, newName)
    # signal_selected_and_style_changed = QtCore.pyqtSignal()
    
    def __init__(self, colname, parent:DataFrameNode):
        assert parent is not None
        super().__init__(parent)
        self.dfnode = parent
        self.tree = parent.tree
        self.column_name = colname
        # self.style = UserDefinedStyle()
        
        self.setText(0, colname)
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
        
        self.modifier_modifier = StyleModifier()
        self.modifier_modifier.signal_style_changed.connect(self.onStyleChanged)
        item = QtWidgets.QTreeWidgetItem(self)
        item.setFlags(Qt.ItemIsEnabled) # not selectable
        self.tree.setItemWidget(item, 0, self.modifier_modifier)
    
    
    def onStyleChanged(self):
        if self.isSelected():
            self.tree.signal_active_style_changed.emit()
    
    def setData(self, column, role, newName):
        """override parent text edit function to send both old and new names"""
        # if newName!=oldName:
        super().setData(column, role, newName)
        oldName = self.column_name
        if role == Qt.EditRole and newName!=oldName:
            self.column_name = newName
            self.tree.signal_column_renamed.emit((self.dfnode.datafile, oldName, newName))
            
    
    def getStyle(self):
        return self.modifier_modifier.getStyle()   