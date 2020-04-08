# ***************************************************************************
# *   Copyright (c) 2020 Bernd Hahnebach <bernd@bimstatik.org>              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "FreeCAD base rebar object"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD

import Arch
import ArchComponent
import Draft
import Part

import ArchVPRebar

if FreeCAD.GuiUp:
    # import FreeCADGui
    # from PySide import QtCore, QtGui
    from DraftTools import translate
    from PySide.QtCore import QT_TRANSLATE_NOOP
else:
    # \cond
    def translate(ctxt, txt):
        return txt

    def QT_TRANSLATE_NOOP(ctxt, txt):
        return txt
    # \endcond


# ****************************************************************************
def makeBaseRebar(
    base,
    diameter=None,
    mark=None,
    name="BaseRebar"
):
    """
    makeBaseRebar(base, [diameter, mark, name]):
    Adds a Reinforcement Bar object using the given base
    (sketch or wire) as sweep path.
    """

    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch")
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Rebar")
    obj.Label = translate("Arch", name)
    # may be set the label to the mark number
    # or even have an attribute which does it on any recompute

    BaseRebar(obj)
    if FreeCAD.GuiUp:
        ViewProviderBaseRebar(obj.ViewObject)

    obj.Base = base
    if FreeCAD.GuiUp:
        base.ViewObject.hide()
    if diameter:
        obj.Diameter = diameter
    else:
        obj.Diameter = p.GetFloat("RebarDiameter", 6)
    if mark:
        obj.MarkNumber = mark
    else:
        obj.MarkNumber = 1

    obj.Document.recompute()
    return obj


# ****************************************************************************
class BaseRebar(Arch.ArchComponent.Component):

    """
    A base reinforcement bar (rebar) object for a rebar shape

    Information
    -----------
    Retrieved from ArchComponent class Component.
    TODO bending roll radius, concrete cover, predefined rebar shapes.
    The object in TreeView has one child, its base and could
    have dozens of childreen, the reinforcements. The link between
    child and father is defined in the child. See Reinforcement class.
    The base rebar should normally not be exported to IFC.

    Known Attributes
    ----------------
    Base : App::PropertyLink
        ATM for base rebar only one Wire is supported
        TODO Sketch should be supported as well.
    Material : App::PropertyLink
        Material object. TODO implement use of Material in base rebar

    Additional Attributes
    ---------------------
    Diameter : App::PropertyLength
        Diameter of the base rebar. It would make sense to limit
        the available diameter to the diameter known in the country
        the base rebar will be made for.
    MarkNumber : App::PropertyInteger
        Needed to identify reinforcements on the bar shape cut list.

        Unique number on one bar shape cut list for manufactor
        or for the building site. But for quantity report to know
        how much material (kg steel) was used a bar shape cut list
        could be made for a whole building. In this list duplicate
        MarkNumber would be allowed. The user should be able
        to explicit decide if in a rebar shape cut list
        duplicate MarkNumbers are allowed.

        May be a String should be used as MarkNumber. With this
        MarkNumber could be integer, big or small ASCII character
        or even Rome letter. But than another property is needed
        to set the type mentioned above. But for what should it be set?
        For each base rebar.
    """

    def __init__(
        self,
        obj
    ):
        super(BaseRebar, self).__init__(obj)
        self.setProperties(obj)
        obj.IfcType = "Reinforcing Bar"

    def setProperties(
        self,
        obj
    ):
        self.Type = "RebarShape"
        pl = obj.PropertiesList

        # ArchComponent properties will be inherited
        # Material, Base, MoveBase, ...
        # base is a sketch or profil the ArchComponent is based on,
        # for rebar the host is the father element,
        # for rebar the structure the rebar is in

        # do not show some not needed Component attributes in Editor
        obj.setEditorMode("Additions", 2)
        obj.setEditorMode("Axis", 2)
        obj.setEditorMode("HorizontalArea", 2)
        obj.setEditorMode("MoveWithHost", 2)
        obj.setEditorMode("PerimeterLength", 2)
        obj.setEditorMode("StandardCode", 2)  # useful,  not used ATM
        obj.setEditorMode("Subtractions", 2)
        obj.setEditorMode("VerticalArea", 2)
        # CloneOf makes sense if two rebars are identical
        # but should have different MarkNumber

        # New properties
        # Diameter
        if "Diameter" not in pl:
            obj.addProperty(
                "App::PropertyLength",
                "Diameter",
                "Rebar Shape",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "The diameter of this rebar shape"
                )
            )
        # MarkNumber
        if "MarkNumber" not in pl:
            obj.addProperty(
                "App::PropertyInteger",
                "MarkNumber",
                "Rebar Shape",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "The mark number of this rebar shape"
                )
            )
        # Length
        if "Length" not in pl:
            obj.addProperty(
                "App::PropertyLength",
                "Length",
                "Rebar Shape",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "The length of this rebar shape"
                )
            )
            obj.setEditorMode("Length", 1)

    def onDocumentRestored(
        self,
        obj
    ):
        super().onDocumentRestored(self, obj)
        self.setProperties(obj)

    def execute(
        self,
        obj
    ):
        if self.clone(obj):
            return
        if not obj.Base:
            FreeCAD.Console.PrintError(
                "No Base, return without a rebar shape for {}.\n"
                .format(obj.Name)
            )
            return
        if not obj.Base.Shape:
            FreeCAD.Console.PrintError(
                "No Shape in Base, return without a rebar shape for {}.\n"
                .format(obj.Name)
            )
            return
        if not obj.Base.Shape.Edges:
            FreeCAD.Console.PrintError(
                "No Edges in Shape of Base, "
                "return without a rebar shape for {}.\n"
                .format(obj.Name)
            )
            return
        if obj.Base.Shape.Faces:
            FreeCAD.Console.PrintError(
                "Faces in Shape of Base, "
                "return without a rebar shape for {}.\n"
                .format(obj.Name)
            )
            return
        if not obj.Diameter.Value:
            FreeCAD.Console.PrintError(
                "No diameter value, return without a rebar shape for {}.\n"
                .format(obj.Name)
            )
            return
        if not obj.MarkNumber:
            FreeCAD.Console.PrintError(
                "No mark number, return without a rebar shape for {}.\n"
                .format(obj.Name)
            )
            return

        # corner cases:
        #    compound from more Wires
        #    compound without Wires but with multiple Edges
        # Does they make sense? If yes handle them.
        # Does it makes sense to handle Shapes with Faces or even Solids?
        if not obj.Base.Shape.Wires and len(obj.Base.Shape.Edges) == 1:
            wire = Part.Wire(obj.Base.Shape.Edges[0])
        else:
            wire = obj.Base.Shape.Wires[0]
        edge = wire.Edges[0]
        bpoint = edge.Vertexes[0].Point
        bvec = edge.tangentAt(edge.FirstParameter)
        if not bpoint:
            return
        # all tests ok!

        # is length allong the rounding or not?
        # in the users head and in material bill without rounding
        # but with sharp edges instead
        if hasattr(obj, "Length"):
            from ArchRebar import getLengthOfRebar
            length = getLengthOfRebar(obj)
            if length:
                obj.Length = length
        # somehow the rebar has no Length proterty ...

        circle = Part.makeCircle(obj.Diameter.Value / 2, bpoint, bvec)
        circle = Part.Wire(circle)
        try:
            obj.Shape = wire.makePipeShell([circle], True, False, 2)
        except Part.OCCError:
            print("Arch: error sweeping rebar profile along the base geometry")
            return


# ****************************************************************************
class ViewProviderBaseRebar(ArchVPRebar.ViewProviderRebarCommon):

    def getIcon(
        self
    ):
        import Arch_rc
        False if Arch_rc.__name__ else True  # dummy usage
        return ":/icons/Arch_Pipe_Tree.svg"

    def onDelete(self, feature, subelements):
        try:
            for o in self.claimChildren():
                o.ViewObject.show()
        except Exception:
            FreeCAD.Console.PrintError("Error in onDelete: ")
        return True

    def claimChildren(
        self
    ):
        # collect the children for TreeView

        # children from Arch.Component
        # since we overwrite the method we need to explicit call it
        children = ArchComponent.ViewProviderComponent.claimChildren(self)

        # special rebar shape children
        if hasattr(self, "Object"):

            # claim reinforcements for this rebar
            for o in self.Object.Document.Objects:
                # print(Draft.getType(o))
                if (
                    Draft.getType(o) == "ReinforcementLattice"
                    or Draft.getType(o) == "Reinforcement"
                ):
                    if o.BaseRebar == self.Object:
                        children.append(o)

            # print(children)
            return children
        return children

    # Drag and Drop for the children
    """
    # https://forum.freecadweb.org/viewtopic.php?f=10&t=28760
    # https://forum.freecadweb.org/viewtopic.php?f=10&t=37632
    # drag ... in German: ausschneiden, ziehen
    # drop ... in German: loslassen, einfuegen, ablegen
    """
    # TODO !!!!!!!!!!!!!!!!!!!!!!
    # it is possible to copy a reinforcement into another base rebar
    # this should not be possible
    # a reinforcement can only have one base rebar, see class reinforcement
    def canDragObjects(self):
        return True

    def canDropObjects(self):
        return True

    def canDragObject(self, dragged_object):
        if (
            Draft.getType(dragged_object) == "ReinforcementLattice"
            or Draft.getType(dragged_object) == "Reinforcement"
        ):
            return True
        else:
            return False

    def canDropObject(self, incoming_object):
        return True

    def dragObject(self, selfvp, dragged_object):
        if (
            Draft.getType(dragged_object) == "ReinforcementLattice"
            or Draft.getType(dragged_object) == "Reinforcement"
        ):
            dragged_object.BaseRebar = None
            # mark the object we move out to recompute
            selfvp.Object.touch()
        FreeCAD.ActiveDocument.recompute()

    def dropObject(self, selfvp, incoming_object):
        if (
            Draft.getType(incoming_object) == "ReinforcementLattice"
            or Draft.getType(incoming_object) == "Reinforcement"
        ):
            incoming_object.BaseRebar = selfvp.Object
            # mark the object we move in to recompute
            selfvp.Object.touch()
        FreeCAD.ActiveDocument.recompute()
