# -*- coding: utf-8 -*-
"""
******************************             
* Filename: df_columns.py
* Author: RayN
* Created on 1/30/18
******************************
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

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
    


class DataFrameTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel('DataFrameTree')
        # self.df_nodes = dfNodes
        # self.root_node = QtWidgets.QTreeWidgetItem(self)
        # self.root_node.setText(0, dfname)
        # self.root_node.setFlags(Qt.ItemIsEnabled) #| Qt.ItemIsEditable)
        # self.addTopLevelItem(self.root_node)
        
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection) # allow multiple selection
        self.setRootIsDecorated(True)
        self.setIndentation(20)



class DataFrameNode(QtWidgets.QTreeWidgetItem):
    """ A dataframe node, with multiple column names as sub-node,
        column sub-node's child is customs style widgets
    """
    def __init__(self, dfName, columns, parent:DataFrameTree, styleChangedCallback=None):
        assert parent is not None
        super().__init__(parent)
        self.tree = parent
        # self.root_node = QtWidgets.QTreeWidgetItem(self)
        self.setText(0, dfName)
        self.setFlags(Qt.ItemIsEnabled) #| Qt.ItemIsEditable)
        self.tree.addTopLevelItem(self)
        
        # self.setRootIsDecorated(True)
        # self.setIndentation(20)
        # self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        self.column_names = columns
        self.column_user_styles = { c : UserDefinedStyle() for c in columns } # columnName => userStyleObj
        
        # styWgt = self.makeUserStyleWidget(styleChangedCallback)
        for colname, usrsty in self.column_user_styles.items():
            col = QtWidgets.QTreeWidgetItem(self)
            col.setText(0, colname)
            col.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
            # self.root_node.addTopLevelItem(col)
            # self.column_items.append(col)
            
            subItem = QtWidgets.QTreeWidgetItem(col)
            subItem.setFlags(Qt.ItemIsEnabled)
            self.tree.setItemWidget(subItem, 0, self.makeUserStyleWidget(styleChangedCallback))
            
            # for w in subWidgets:
            #     # AsNamedWidget(w)
            #     w = gui.WidgetWithLabel(w)
            #     subItem = QtWidgets.QTreeWidgetItem(col)
            #     self.setItemWidget(subItem, 0, w)
            #     subItem.setFlags(Qt.ItemIsEnabled)
        
        # self.collapseAll()
        # self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # self.setRootIsDecorated(True)
        # self.setIndentation(20)
    
    
    def makeUserStyleWidget(self, callback=None):
        """ make the widget for user style control """
        comboLs = gui.ComboBox(   
            label='LineStyle', 
            textList=['','-','--','-.',':'], 
            default='' )
        editorLw = gui.Float(      
            label='LineWidth(+/-)', 
            low=-50, high=50, step=0.1, default=0, digits=2)
        comboMk = gui.ComboBox(   
            label='Marker',
            textList=['', 'o','>','<', 'v','^', 's', 'D', 'd', 'h','H'], 
            default='')
        editorMs = gui.Float(      
            label='MarkerSize(+/-)', 
            low=-50, high=50, step=0.2, default=0, digits=2)
        
        if callback:
            comboLs.currentIndexChanged.connect(callback)
            editorLw.valueChanged.connect(callback)
            comboMk.currentIndexChanged.connect(callback)
            editorMs.valueChanged.connect(callback)
            
        w = QtWidgets.QWidget()
        w.setLayout(gui.MakeFormLayout([comboLs, editorLw, comboMk, editorMs]))
        return w
        
    
    def getUserStyles(self, col:str):
        return self.column_user_styles[col]
    
    
