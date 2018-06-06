import math
from maya import cmds

import pymel.core as pm
import maya.mel as mel
from pymel.core.uitypes import AETemplate
import maya.OpenMayaUI as omui
import maya.OpenMaya as om

from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QListWidget
from shiboken2 import wrapInstance


import window_utils
import node_utils
import message_utils
#  import navigator_ctrl
reload(window_utils)
#  reload(navigator_ctrl)
reload(node_utils)


class AEsporeNodeTemplate(AETemplate):

    def __init__(self, node):
        super(AEsporeNodeTemplate, self).__init__(node)

        print 'init template:', node
        self._node = node
        self.callbacks = om.MCallbackIdArray()
        self.jobs = []
        self.io = message_utils.IOHandler()
        self.navigator = None
        self.context = None

        self.beginScrollLayout()
        self.build_ui() # build bui
        #  pm.mel.AElocatorInclude(node) # add defaul controls
        self.addExtraControls('Extra Attributes') # add extra attributes
        self.endScrollLayout()

        self.add_script_job()

    def __del__(self):
        for i in xrange(self.callbacks.length()):
            print 'remove cb'
            om.Message().removeCallback(self.callbacks[i])

        # kill script jobs
        for job in self.jobs:
            print 'kill script job:', job
            cmds.scriptJon(kill=job)

    def add_script_job(self):
        self.jobs.append(cmds.scriptJob(event=["ToolChanged", self.tool_changed]))

    def tool_changed(self, *args):
        current_tool = cmds.currentCtx()
        if not current_tool.startswith('spore'):
            try:
                cmds.button('placeBtn', e=True, bgc=(0.366, 0.366, 0.366))
                cmds.button('sprayBtn', e=True, bgc=(0.366, 0.366, 0.366))
                cmds.button('scaleBtn', e=True, bgc=(0.366, 0.366, 0.366))
                cmds.button('alignBtn', e=True, bgc=(0.366, 0.366, 0.366))
                #  cmds.button('moveBtn', e=True, bgc=(0.366, 0.366, 0.366))
                cmds.button('idBtn', e=True, bgc=(0.366, 0.366, 0.366))
                cmds.button('removeBtn', e=True, bgc=(0.366, 0.366, 0.366))
            except RuntimeError:
                pass


    def add_callbacks(self):
        """ register a bunch of node callbacks to hook our qt widget
        this is kind of hacky solution since this only adds our custom
        navigator widgets after one of the callbacks has been triggered.
        desireably we'd like to hook the widget after node initialization.
        but since the the parent layout in the AE does not exist at node init,
        we need to find a way to parent the widget at a later point in time """

        if self.callbacks.length() <= 1:
            m_node = node_utils.get_mobject_from_name(self._node)
            self.callbacks.append(om.MNodeMessage().addAttributeChangedCallback(m_node, self.hook_qt_widget))
            self.callbacks.append(om.MDGMessage().addConnectionCallback(self.hook_qt_widget))

    def hook_qt_widget(self, *args):
        """ hook the navigator widget to the attribute editor
        update the navigator widget if it already exists """

        if not self.navigator:
            container_wdg = get_nav_layout()
            container_lay = container_wdg.layout() #.children()
            self.navigator = navigator_ctrl.Navigator(self._node)
            navigator_wdg = self.navigator.get_widget()
            container_lay.addWidget(navigator_wdg)

        else:
            self.navigator.update_ui()

    def build_ui(self):

        # instance source
        self.beginLayout('Instanced Objects', collapse=0)
        self.callCustom(self.add_instance_list, self.update_instance_list)
        self.endLayout()

        # placement options
        self.beginLayout('Instance Transforms', collapse=False)
        self.addSeparator()
        self.addControl('alignTo', label='Align To')
        self.addControl('strength', label='Weight')
        self.addControl('minRotation', label='Min Rotation')
        self.addControl('maxRotation', label='Max Rotation')
        self.addSeparator()
        self.addControl('uniformScale', label='Uniform Scale', changeCommand=self.uniform_scale_toggle)
        self.addControl('minScale', label='Min Scale')
        self.addControl('maxScale', label='Max Scale')
        self.addControl('scaleFactor', label='Scale Factor')
        self.addControl('scaleAmount', label='Randomize / Smooth')
        self.dimControl(self._node, 'scaleFactor', True)
        self.addSeparator()
        self.addControl('minOffset', label='Min Offset')
        self.addControl('maxOffset', label='Max Offset')
        #  self.beginLayout('Flood', collapse=True)
        #  cmds.button('floodBtn', l='Flood Values')
        #  self.endLayout()
        #  self.addSeparator()
        #  self.addControl('minId', label='Min Id', changeCommand=lambda _: self.index_cc('min'))
        #  self.addControl('maxId', label='Max Id', changeCommand=lambda _: self.index_cc('max'))
        #  self.addSeparator()
        #  self.addControl('usePressureMapping', label='Use Pen Pressure', changeCommand=self.use_pressure_cc)
        #  self.addControl('pressureMapping', label='Pessure Mapping')
        #  self.addControl('minPressure', label='Min Pessure')
        #  self.addControl('maxPressure', label='Max Pessure')
        self.endLayout()

        # brush properties
        self.beginLayout('Brush', collapse=True)
        self.callCustom(self.add_brush_btn, self.update_brush_btn, 'contextMode')
        self.addControl('brushRadius', label='Radius')
        self.addControl('numBrushSamples', label='Number Of Samples')
        self.addControl('minDistance', label='Min Distance')
        self.addControl('fallOff', label='Falloff')
        self.dimControl(self._node, 'fallOff', True)
        self.endLayout()
        # emit properties
        self.beginLayout('Emit', collapse=1)
        self.addControl('emitType', label='Type', changeCommand=self.emit_type_cc)
        self.addControl('numSamples', label='Number Of Samples')
        self.addControl('cellSize', label='Cell Size', changeCommand=self.estimate_num_samples)
        self.addControl('minRadius', label='Min Radius', changeCommand=self.estimate_num_samples)
        self.addControl('minRadius2d', label='Min Radius 2d')
        self.beginLayout('Filter', collapse=0)
        self.beginLayout('Texture', collapse=1)
        self.addControl('emitFromTexture', label='Emit from Texture')
        self.addControl('emitTexture', label='Texture')
        self.endLayout()
        self.beginLayout('Altitude', collapse=1)
        self.addControl('minAltitude', 'Min Altitude', changeCommand=self.change_min_altitude)
        self.addControl('maxAltitude', 'Max Altitude', changeCommand=self.change_max_altitude)
        self.addSeparator()
        self.addControl('minAltitudeFuzz', 'Min Altitude Fuzziness')
        self.addControl('maxAltitudeFuzz', 'Max Altitude Fuzziness')
        self.endLayout()
        self.beginLayout('Slope', collapse=1)
        self.addControl('minSlope', 'Min Slope', changeCommand=self.change_min_slope)
        self.addControl('maxSlope', 'Max Slope', changeCommand=self.change_max_slope)
        self.addSeparator()
        self.addControl('slopeFuzz', 'Slope Fuzziness')
        self.endLayout()
        self.endLayout()
        #  self.beginLayout('Geo Cache', collapse=1)
        #  self.addControl('geoCached', label='Geometry Cached')
        #  self.endLayout()
        #  self.addControl('emitDummy', label='emitDummy')
        self.callCustom(self.add_emit_btn, self.update_emit_btn, "emit" )
        self.endLayout()


        self.beginLayout('Count', collapse=True)
        self.addControl('numSpores', label='Count')
        self.dimControl(self._node, 'Count', True)
        self.endLayout()
        # I/O
        #  self.beginLayout('I/O', collapse=1)
        #  self.beginLayout('input', collapse=1)
        #  self.endLayout()
        #  self.beginLayout('output', collapse=1)
        #  self.endLayout()
        #  self.endLayout()

        # display properties
        #  self.beginLayout('Display', collapse=1)
        #  self.addControl('numSpores', label='Number of Points')
        #  self.addControl('pointVisibility', label='Display Spores')
        #  self.addControl('normalVisibility', label='Display Normals')
        #  self.addControl('displaySize', label='Spore Radius')
        self.endLayout()

    # ------------------------------------------------------------------------ #
    # instance geometry list
    # ------------------------------------------------------------------------ #

    def add_instance_list(self, *args):

        instanced_geo = node_utils.get_instanced_geo(self._node)
        if instanced_geo:
            instanced_geo = ['[{}]: {}'.format(i, name) for i, name in enumerate(instanced_geo)]
        else:
            return
            #  instanced_geo = ['No source objects selected']


        form = cmds.formLayout()
        help_lbl = cmds.text(l='Select item(s) to specify an index', align='left')
        scroll_list = cmds.textScrollList('instanceList', ams=True, append=instanced_geo)
        add_btn = cmds.symbolButton('addInstanceBtn', width=30, i='UVTBAdd.png', c=pm.Callback(self.add_instance))
        rm_btn = cmds.symbolButton('removeInstanceBtn', width=30, i='UVTBRemove.png', c=pm.Callback(self.remove_instance))
        cmds.formLayout(form, e=True, attachForm=[(help_lbl, 'left', 2),
                                                  (help_lbl, 'right', 2),
                                                  (help_lbl, 'top', 0),
                                                  (add_btn, 'right', 2),
                                                  (add_btn, 'top', 17),
                                                  (rm_btn, 'top', 45),
                                                  (rm_btn, 'right', 2),
                                                  (scroll_list, 'right', 35),
                                                  (scroll_list, 'top', 17),
                                                  (scroll_list, 'left', 2),
                                                  (scroll_list, 'bottom', 2)],
                        height=115)

    def update_instance_list(self, *args):

        selection = cmds.ls(sl=True)[-1]
        if cmds.objectType(selection) == 'sporeNode':
            self._node = selection
        #  print 'update:' , args, self._node, self.nodeName
        instanced_geo = node_utils.get_instanced_geo(self._node)
        #  if instanced_geo:
        instanced_geo = ['[{}]: {}'.format(i, name) for i, name in enumerate(instanced_geo)]
        #  else:
        #      instanced_geo = ['No source geometry selected']

        cmds.textScrollList('instanceList', e=1, removeAll=True)
        cmds.textScrollList('instanceList', e=1, append=instanced_geo)

    def add_instance(self):
        """ add a source to the instancer and the sporeNode """

        selection = cmds.ls(sl=True, l=True)
        spore_node = selection.pop(-1)

        num_items = cmds.textScrollList('instanceList', numberOfItems=True, q=True)
        items = cmds.textScrollList('instanceList', q=True, ai=True)
        instances = node_utils.get_instanced_geo(self._node)

        for i, obj in enumerate(selection):
            # TODO - check if object type is valid
            if obj not in instances:
                obj_name = '[{}]: {}'.format(i + num_items, obj)
                cmds.textScrollList('instanceList', e=1, append=obj_name)
                node_utils.connect_to_instancer(obj, self._node)

    def remove_instance(self):
        selection = cmds.textScrollList('instanceList', q=1, selectItem=True)
        instancer = node_utils.get_instancer(self._node)

        if selection:
            for item in selection:
                print 'remove:', item
                obj_name = item.split(' ')[-1]
                connections = cmds.listConnections(obj_name, instancer, p=True, d=True, s=False)
                print connections, obj_name
                connection = [c for c in connections if c.split('.')[0] == instancer]
                print connections
                for connection in connections:
                    print connection, instancer
                    if connection.split('.')[0] == instancer.split('|')[-1]:
                        cmds.disconnectAttr('{}.matrix'.format(obj_name), connection)

        self.update_instance_list()

    # ------------------------------------------------------------------------ #
    # emit button
    # ------------------------------------------------------------------------ #

    def add_emit_btn(self, attr):
        """ add button to trigger emit checkbox """

        #  cmd = 'cmds.setAttr("{}", 1)'.format(attr)
        cmds.button('emitButton', l='Emit', c=self.emit)

    def update_emit_btn(self, attr):
        """ update button to trigger emit checkbox """

        #  cmd = 'cmds.setAttr("{}", 1)'.format(attr)
        cmds.button('emitButton', e=True, c=self.emit)

    def emit(self, *args):
        """ run the actual sample command """

        in_mesh = node_utils.get_connected_in_mesh(self._node)
        transform = cmds.listRelatives(in_mesh, p=True, f=True)[0]
        if cmds.getAttr(transform + '.translateX') != 0\
        or cmds.getAttr(transform + '.translateY') != 0\
        or cmds.getAttr(transform + '.translateZ') != 0\
        or cmds.getAttr(transform + '.rotateX') != 0\
        or cmds.getAttr(transform + '.rotateY') != 0\
        or cmds.getAttr(transform + '.rotateZ') != 0\
        or cmds.getAttr(transform + '.scaleX') != 1\
        or cmds.getAttr(transform + '.scaleY') != 1\
        or cmds.getAttr(transform + '.scaleZ') != 1:
            msg = 'Feeze inMesh\'s transformations in order to sample the geomety!'
            result = message_utils.IOHandler().confirm_dialog(msg, 'Freeze Transformations')
            if result:
                cmds.makeIdentity(transform, a=True, s=True, r=True, t=True, n=0)
            else:
                return

        cmds.setAttr('{}.emit'.format(self._node), 1)
        cmds.sporeSampleCmd()

    # ------------------------------------------------------------------------ #
    # context mode buttons
    # ------------------------------------------------------------------------ #

    def add_brush_btn(self, attr):
        """ replace the default combobox with a button for each entry """

        cmds.rowLayout('instanceLayout', nc=8 ) #, adjustableColumn=6) #, w=270 ) #, columnWidth3=(80, 75, 150),  columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 0), (3, 'both', 0)] )
        cmds.text(l='Tool', align='right', w=145)
        cmds.button('placeBtn', l='Place', c=pm.Callback(self.activateContext, 'place', attr, 0))
        cmds.button('sprayBtn', l='Spray', c=pm.Callback(self.activateContext, 'spray', attr, 1))
        cmds.button('scaleBtn', l='Scale', c=pm.Callback(self.activateContext, 'scale', attr, 2))
        cmds.button('alignBtn', l='Align', c=pm.Callback(self.activateContext, 'align', attr, 3))
        #  cmds.button('moveBtn', l='Move', c=pm.Callback(self.activateContext, 'move', attr, 4))
        cmds.button('idBtn', l='Id', c=pm.Callback(self.activateContext, 'id', attr, 5))
        cmds.button('removeBtn', l='Remove', c=pm.Callback(self.activateContext, 'remove', attr, 6))
        cmds.setParent('..')


    def update_brush_btn(self, attr):

        cmds.button('placeBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'place', attr, 0))
        cmds.button('sprayBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'spray', attr, 1))
        cmds.button('scaleBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'scale', attr, 2))
        cmds.button('alignBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'align', attr, 3))
        #  cmds.button('moveBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'move', attr, 4))
        cmds.button('idBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'id', attr, 5))
        cmds.button('removeBtn', e=True, bgc=(0.366, 0.366, 0.366), c=pm.Callback(self.activateContext, 'remove', attr, 6))

        self._node = attr.split('.')[0]
        if cmds.currentCtx().startswith('spore'):
            ctx_mode = cmds.getAttr(attr)
            print ctx_mode
            if ctx_mode == 0:
                cmds.button('placeBtn', e=True, bgc=(0.148, 0.148, 0.148))
            elif ctx_mode == 1:
                cmds.button('sprayBtn', e=True, bgc=(0.148, 0.148, 0.148))
            elif ctx_mode == 2:
                cmds.button('scaleBtn', e=True, bgc=(0.148, 0.148, 0.148))
            elif ctx_mode == 3:
                cmds.button('alignBtn', e=True, bgc=(0.148, 0.148, 0.148))
            elif ctx_mode == 4:
                pass
            elif ctx_mode == 5:
                cmds.button('idBtn', e=True, bgc=(0.148, 0.148, 0.148))
            elif ctx_mode == 6:
                cmds.button('removeBtn', e=True, bgc=(0.148, 0.148, 0.148))



    def activateContext(self, context_mode, attr, index):
        """ called whenever a brush button is clicked
        enable/disable context controls & activate tool context
        @param context_mode: indicates which button has been clicked
        @param attr: holds the current node and attribute name
        @param index: the index of the child attr in the combobox """

        # check if there are any source objects
        if not cmds.textScrollList('instanceList', q=True, ai=True):
            self.io.set_message('No source objects selected', 0)
            return

        cmds.setAttr(attr, index)
        attr_name = attr.split('.')[-1]
        node_name = attr.split('.')[0]

        # create a tuple of all controls and a dict that associates each control
        # to a specific context style
        brush_crtls = ('brushRadius', 'minDistance', 'fallOff', 'strength',
                       'numBrushSamples', 'alignTo', 'minRotation',
                       'maxRotation', 'uniformScale', 'minScale',
                       'maxScale', 'scaleFactor', 'scaleAmount',
                       'minOffset', 'maxOffset',
                       'usePressureMapping', 'pressureMapping',
                       'minPressure', 'maxPressure')
        p_map = cmds.getAttr('{}.usePressureMapping'.format(self._node))
        dim_ctrl = {                #    rad    minD,  foff,   stren,  numS,   aliTo   minR,   maxR,   uniS    minS,   maxS,   sFac,   sAmou,  minO,   maxO,   pre,    map,    minP,   maxP
                    'place':            (False, True,  False,  True,   False,  True,   True,   True,   True,   True,   True,   False,  False,  True,   True,   True,   p_map,  p_map,  p_map),
                    'spray':            (True,  True,  False,  True,   True,   True,   True,   True,   True,   True,   True,   False,  False,  True,   True,   True,   p_map,  p_map,  p_map),
                    'scale':            (True,  False, True,   False,  False,  False,  False,  False,  False,  False,  False,  True,   True,   False,  False,  True,   False,  p_map,  p_map),
                    'align':            (True,  False, True,   True,   False,  True,   False,  False,  False,  False,  False,  False,  False,  False,  False,  True,   False,  p_map,  p_map),
                    'move':             (True,  False, False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  True,   False,  p_map,  p_map),
                    'id':               (True,  False, False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  True,   False,  p_map,  p_map),
                    'remove':           (True,  False, False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False,  False),
                    }

        #  dim controls
        for i, ctrl in enumerate(brush_crtls):
            self.dimControl(node_name, ctrl, not dim_ctrl[context_mode][i])

        # colorize button
        buttons = ['placeBtn', 'sprayBtn', 'scaleBtn', 'alignBtn', 'idBtn', 'removeBtn']
        for btn in buttons:
            cmds.button(btn, e=True, bgc=(0.366, 0.366, 0.366))
        button_name = '{}Btn'.format(context_mode)
        cmds.button(button_name, e=True, bgc=(0.148, 0.148, 0.148))

        # set context
        self.context = cmds.sporeContext()
        cmds.select(self._node)
        cmds.setToolTo(self.context)

    # ------------------------------------------------------------------------ #
    # pen pressure checkbox
    # ------------------------------------------------------------------------ #

    def emit_type_cc(self, node):
        """ """
        self._node = node
        emit_type = cmds.getAttr('{}.emitType'.format(node))

        if emit_type == 0:
            self.dimControl(node, 'numSamples', False)
            self.dimControl(node, 'cellSize', True)
            self.dimControl(node, 'minRadius', True)
            self.dimControl(node, 'minRadius2d', True)
        elif emit_type == 1:
            self.dimControl(node, 'numSamples', True)
            self.dimControl(node, 'cellSize', False)
            self.dimControl(node, 'minRadius', True)
            self.dimControl(node, 'minRadius2d', True)
            self.estimate_num_samples(node)
        elif emit_type == 2:
            self.dimControl(node, 'numSamples', True)
            self.dimControl(node, 'cellSize', True)
            self.dimControl(node, 'minRadius', False)
            self.dimControl(node, 'minRadius2d', True)
            self.estimate_num_samples(node)
        elif emit_type == 3:
            self.dimControl(node, 'numSamples', True)
            self.dimControl(node, 'cellSize', True)
            self.dimControl(node, 'minRadius', True)
            self.dimControl(node, 'minRadius2d', False)

    def estimate_num_samples(self, node):
        """ estimate how many random samples we need for grid or disk sampling """

        self._node = node
        emit_type = cmds.getAttr('{}.emitType'.format(node))
        if emit_type == 1:
            cell_size = cmds.getAttr(self._node + '.cellSize')
        elif emit_type == 2:
            cell_size = cmds.getAttr(self._node + '.minRadius') / math.sqrt(3)
        else:
            return

        in_mesh = node_utils.get_connected_in_mesh(self._node)
        area = cmds.polyEvaluate(in_mesh, worldArea=True)
        cmds.setAttr(self._node + '.numSamples', int(area/cell_size) * 5)


    def change_min_altitude(self, node):
        min_altitude = cmds.getAttr('{}.minAltitude'.format(node))
        max_altitude = cmds.getAttr('{}.maxAltitude'.format(node))
        if min_altitude > max_altitude:
            cmds.setAttr('{}.maxAltitude'.format(node), min_altitude)

    def change_max_altitude(self, node):
        min_altitude = cmds.getAttr('{}.minAltitude'.format(node))
        max_altitude = cmds.getAttr('{}.maxAltitude'.format(node))
        if min_altitude > max_altitude:
            cmds.setAttr('{}.minAltitude'.format(node), max_altitude)

    def change_min_slope(self, node):
        min_slope = cmds.getAttr('{}.minSlope'.format(node))
        max_slope = cmds.getAttr('{}.maxSlope'.format(node))
        if min_slope > max_slope:
            cmds.setAttr('{}.maxSlope'.format(node), min_slope)

    def change_max_slope(self, node):
        min_slope = cmds.getAttr('{}.minSlope'.format(node))
        max_slope = cmds.getAttr('{}.maxSlope'.format(node))
        if min_slope > max_slope:
            cmds.setAttr('{}.minSlope'.format(node), max_slope)


    def use_pressure_cc(self, node):
        """ use pen pressure change command is triggered when the "Use Pen Pressure"
        checkbox is toggled """
        use_pressure = not cmds.getAttr('{}.usePressureMapping'.format(node))

        self.dimControl(node, 'pressureMapping', use_pressure)
        self.dimControl(node, 'minPressure', use_pressure)
        self.dimControl(node, 'maxPressure', use_pressure)

        context_mode = cmds.getAttr('{}.contextMode'.format(node))
        if context_mode in (2, 3, 4): # disable for mode 2,3,4
            self.dimControl(node, 'pressureMapping', True)
        elif context_mode == 5:
            self.dimControl(node, 'minPressure', True)
            self.dimControl(node, 'maxPressure', True)


    def update_pressure_cbx(self, attr):
        pass

    # ------------------------------------------------------------------------ #
    # uniform scale toggle
    # ------------------------------------------------------------------------ #

    def uniform_scale_toggle(self, node):
        """ toggle between uniform and non-uniform scale
        :param node: the current node name """

        self._node = node
        print 'toggle', node
        uniform_scale = not cmds.getAttr('{}.uniformScale'.format(node))
        print 'foo', cmds.getAttr('{}.minScaleX'.format(node))

        #  self.dimControl(node, 'minScaleX', uniform_scale)
        #  self.dimControl(node, 'maxScaleX', uniform_scale)
        #  self.dimControl(node, 'minScale', uniform_scale)
        #  self.dimControl(node, 'minScaleX', False)
        #  self.dimControl(node, 'minScaleY', False)

    def index_cc(self, typ):
        """ """
        min_id = cmds.getAttr('{}.minId'.format(self._node))
        max_id = cmds.getAttr('{}.maxId'.format(self._node))

        if typ == 'min' and min_id > max_id:
            cmds.setAttr('{}.maxId'.format(self._node), min_id)
        elif typ == 'max' and max_id < min_id:
            cmds.setAttr('{}.minId'.format(self._node), max_id)

        #  if min_id > max_id

    # ------------------------------------------------------------------------ #
    # utils
    # ------------------------------------------------------------------------ #

    #  def dim_controls(self, *args):
    #      """ dim / undim all brush controls
    #      :param dim: bool if we dim or undim the controls """
    #      dim = True
    #      print 'args', args
    #
    #      for crtl in self.brush_crtls:
    #          #  self.suppress(crtl)
    #          #  print 'dim: ', self._node, crtl, dim
    #          self.dimControl(self._node, crtl, dim)
    #
    #

def get_nav_layout():

    def find_first_frame_layout(layout):
        """ recursivley get all child layout until we find the first framelayout """

        children = cmds.layout(layout, ca=True, q=True)
        for child in children:

            if child.startswith('frameLayout'):
                return child

            else:
                return find_first_frame_layout(child)


    nav_layout = find_first_frame_layout('AttrEdsporeNodeFormLayout')
    return wrapInstance(long(omui.MQtUtil.findControl(nav_layout)), QWidget)



#
#  def get_nav_layout():
#      """ get the navigator frame layout and return and wrap it as qWidget """
#
#      def find_first_frame_layout(layout):
#          """ recursivley get all child layout until we find the first framelayout """
#
#          print layout
#          children = cmds.layout(layout, ca=True, q=True)
#          print children
#          if children is None:
#              return
#          for child in children:
#              if child.startswith('frameLayout'):
#                  return child
#              if child:
#                  return find_first_frame_layout(child)
#
#      print 'l', cmds.layout('AttrEdsporeNodeFormLayout', q=1, ex=1)
#      nav_layout = find_first_frame_layout('AttrEdsporeNodeFormLayout')
#      return wrapInstance(long(omui.MQtUtil.findControl(nav_layout)), qw.QWidget)
#
