import sys

import pymel.core as pm
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx

import AEsporeNodeTemplate
from scripted import spore_node
from scripted import spore_context
from scripted import spore_command

reload(spore_node)
reload(spore_context)
reload(spore_command)
reload (AEsporeNodeTemplate)

import maya.mel as mel
mel.eval('refreshEditorTemplates;')


MENU = None
# add items   #Label                    #commande
MENU_ITEMS = {'Spore':                  'import manager;reload(manager)',
              'Create Spore Node':      '',
              'Help':                   ''}


def initializePlugin(mobject):
    """ initialize plugins & create menu"""

    mplugin = ompx.MFnPlugin(mobject)

    # register node prototype
    try:
        mplugin.registerNode(spore_node.SporeNode.name,
                             spore_node.SporeNode.id,
                             spore_node.SporeNode.creator,
                             spore_node.SporeNode.initialize,
                             ompx.MPxNode.kLocatorNode)

    except:
        sys.stderr.write( "Failed to register node: %s" % spore_node.SporeNode.name)
        raise

    # register context & tool command
    try:
        mplugin.registerContextCommand(spore_context.K_CONTEXT_NAME,
                                       spore_context.SporeContextCommand.creator,
                                       spore_context.K_TOOL_CMD_NAME,
                                       spore_context.SporeToolCmd.creator,
                                       spore_context.SporeToolCmd.syntax)
    except:
        sys.stderr.write("Failed to register context command: {}".format(spore_context.K_CONTEXT_NAME))
        raise

    try:
        mplugin.registerCommand(spore_command.SporeCommand.name,
                                spore_command.SporeCommand.creator,
                                spore_command.SporeCommand.syntax)
    except:
        sys.stderr.write('Failed to register spore command: {}'.format(spore_command.SporeCommand.name))

    # cereate menu
    global MENU
    if not MENU:
        main_wnd = pm.language.melGlobals['gMainWindow']
        MENU = pm.menu('Spore', parent=main_wnd)

    # add menu items
    for lbl, cmd in MENU_ITEMS.iteritems():
        pm.menuItem(label=lbl, command=cmd, parent=MENU)

def uninitializePlugin(mobject):
    """ uninitialize plugins in reverse order & delete menu """

    mplugin = ompx.MFnPlugin(mobject)

    # deregister context and tool command
    try:
        mplugin.deregisterContextCommand(spore_context.K_CONTEXT_NAME,
                                         spore_context.K_TOOL_CMD_NAME)
    except:
        sys.stderr.write("Failed to deregister node: %s" % spore_context.K_CONTEXT_NAME)
        raise

    # deregister spore node
    try:
        mplugin.deregisterNode(spore_node.SporeNode.id)
    except:
        sys.stderr.write("Failed to deregister node: %s" % spore_node.SporeNode.name)
        raise

    # delete menu
    pm.deleteUI(MENU)


#  def load_spore_template(node_name):
#
#      print 'ae cb'
#      #  try:
#      import AEsporeNodeTemplate
#      reload (AEsporeNodeTemplate)
#      from maya import mel
#      mel.eval('refreshEditorTemplates;')
#
#      ae_template = AEsporeNodeTemplate.AEsporeNodeTemplate(node_name)
#      print ae_template
#      #  except:
#      #      raise ImportWarning('Could not import sporeNode Attribute Editor ui')