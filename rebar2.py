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

__title__ = "FreeCAD rebar based on bar shape class and distribution class"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD

import Arch
import ArchCommands
import ArchComponent
import Draft
import Part

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
# rebar shape
def makeRebarShape(
    base,
    diameter=None,
    mark=None,
    name="RebarShape"
):
    """
    makeRebarShape(base, [diameter, mark, name]):
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

    _RebarShape(obj)
    if FreeCAD.GuiUp:
        _ViewProviderRebarShape(obj.ViewObject)

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


class _RebarShape(Arch.ArchComponent.Component):

    "A reinforcement bar (rebar) object for a rebar shape"

    def __init__(
        self,
        obj
    ):
        ArchComponent.Component.__init__(self, obj)
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
        # for rebar the wire host is the father element,
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
        # but need different MarkNumber

        # New properties
        # Diameter
        if "Diameter" not in pl:
            obj.addProperty(
                "App::PropertyLength",
                "Diameter",
                "Rebar",
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
                "Rebar",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "The mark number of this rebar shape"
                )
            )

    def onDocumentRestored(
        self,
        obj
    ):
        ArchComponent.Component.onDocumentRestored(self, obj)
        self.setProperties(obj)

    def execute(
        self,
        obj
    ):
        if self.clone(obj):
            return
        if not obj.Base:
            return
        if not obj.Base.Shape:
            return
        if not obj.Base.Shape.Wires:
            return
        if not obj.Diameter.Value:
            return
        if not obj.MarkNumber:
            return

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
            print("Arch: error sweeping rebar profile along the base sketch")
            return


class _ViewProviderRebarBase(Arch.ArchComponent.ViewProviderComponent):

    """A View Provider for the rebar shape and rebar distribution object"""
    # inherite this class and only use a different icon
    # color may be not brown, may be depending on diameter

    def __init__(
        self,
        vobj
    ):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

        pl = vobj.PropertiesList
        if "RebarShape" not in pl:
            vobj.addProperty(
                "App::PropertyString",
                "RebarShape",
                "Rebar",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Shape of rebar"
                )
            ).RebarShape
            vobj.setEditorMode("RebarShape", 2)

        vobj.ShapeColor = ArchCommands.getDefaultColor("Rebar")

    def onDocumentRestored(
        self,
        vobj
    ):
        self.setProperties(vobj)

    def setEdit(
        self,
        vobj,
        mode
    ):
        if mode == 0:
            if vobj.RebarShape:
                try:
                    # Import module of RebarShape
                    module = __import__(vobj.RebarShape)
                except ImportError:
                    FreeCAD.Console.PrintError(
                        "Unable to import RebarShape module\n"
                    )
                    return
                module.editDialog(vobj)

    def updateData(
        self,
        obj,
        prop
    ):
        if prop == "Shape":
            if hasattr(self, "centerline"):
                if self.centerline:
                    self.centerlinegroup.removeChild(self.centerline)
            if hasattr(obj.Proxy, "wires"):
                if obj.Proxy.wires:
                    from pivy import coin
                    import re
                    self.centerline = coin.SoSeparator()
                    comp = Part.makeCompound(obj.Proxy.wires)
                    pts = re.findall(
                        "point \[(.*?)\]",
                        comp.writeInventor().replace("\n", "")
                    )
                    pts = [p.split(",") for p in pts]
                    for pt in pts:
                        ps = coin.SoSeparator()
                        plist = []
                        for p in pt:
                            c = []
                            for pstr in p.split(" "):
                                if pstr:
                                    c.append(float(pstr))
                            plist.append(c)
                        coords = coin.SoCoordinate3()
                        coords.point.setValues(plist)
                        ps.addChild(coords)
                        ls = coin.SoLineSet()
                        ls.numVertices = -1
                        ps.addChild(ls)
                        self.centerline.addChild(ps)
                    self.centerlinegroup.addChild(self.centerline)
        ArchComponent.ViewProviderComponent.updateData(self, obj, prop)  # ???

    def attach(
        self,
        vobj
    ):
        self.ViewObject = vobj
        self.Object = vobj.Object
        from pivy import coin
        self.centerlinegroup = coin.SoSeparator()
        self.centerlinegroup.setName("Centerline")
        self.centerlinecolor = coin.SoBaseColor()
        self.centerlinestyle = coin.SoDrawStyle()
        self.centerlinegroup.addChild(self.centerlinecolor)
        self.centerlinegroup.addChild(self.centerlinestyle)
        vobj.addDisplayMode(self.centerlinegroup, "Centerline")
        ArchComponent.ViewProviderComponent.attach(self, vobj)  # ???

    def onChanged(
        self,
        vobj,
        prop
    ):
        if (prop == "LineColor") and hasattr(vobj, "LineColor"):
            if hasattr(self, "centerlinecolor"):
                c = vobj.LineColor
                self.centerlinecolor.rgb.setValue(c[0], c[1], c[2])
        elif (prop == "LineWidth") and hasattr(vobj, "LineWidth"):
            if hasattr(self, "centerlinestyle"):
                self.centerlinestyle.lineWidth = vobj.LineWidth
        ArchComponent.ViewProviderComponent.onChanged(self, vobj, prop)  # ???

    def getDisplayModes(
        self,
        vobj
    ):
        modes = ArchComponent.ViewProviderComponent.getDisplayModes(
            self, vobj
        )
        modes.append("Centerline")
        return modes


class _ViewProviderRebarShape(_ViewProviderRebarBase):

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

            # claim distributions for this rebar shape
            for o in self.Object.Document.Objects:
                # print(Draft.getType(o))
                if (
                    Draft.getType(o) == "RebarDistributionLattice"
                    or Draft.getType(o) == "RebarDistribution"
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
    # it is possible to copy a distribution into another rebar shape
    # this should not be possible
    # a distribution can only have one BaseRebar, see class distribution
    def canDragObjects(self):
        return True

    def canDropObjects(self):
        return True

    def canDragObject(self, dragged_object):
        if (
            Draft.getType(dragged_object) == "RebarDistributionLattice"
            or Draft.getType(dragged_object) == "RebarDistribution"
        ):
            return True
        else:
            return False

    def canDropObject(self, incoming_object):
        return True

    def dragObject(self, selfvp, dragged_object):
        if (
            Draft.getType(dragged_object) == "RebarDistributionLattice"
            or Draft.getType(dragged_object) == "RebarDistribution"
        ):
            dragged_object.BaseRebar = None
            # mark the object we move out to recompute
            selfvp.Object.touch()
        FreeCAD.ActiveDocument.recompute()

    def dropObject(self, selfvp, incoming_object):
        if (
            Draft.getType(incoming_object) == "RebarDistributionLattice"
            or Draft.getType(incoming_object) == "RebarDistribution"
        ):
            incoming_object.BaseRebar = selfvp.Object
            # mark the object we move in to recompute
            selfvp.Object.touch()
        FreeCAD.ActiveDocument.recompute()


# ****************************************************************************
# rebar distribution
def makeRebarDistribution(
    base_rebar,
    placements=[],
    name="RebarDistribution"
):
    """
    makeRebarDistribution(base_rebar, placements, [name])
    Adds a reinforcement distribution object.
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Rebar")
    obj.Label = translate("Arch", name)

    _RebarDistribution(obj)
    if FreeCAD.GuiUp:
        _ViewProviderRebarDistribution(obj.ViewObject)

    obj.BaseRebar = base_rebar
    obj.Placements = placements

    # mark base_rebar obj for recompute to make it collect its new child
    base_rebar.touch()
    obj.Document.recompute()
    return obj


class _RebarDistribution(Arch.ArchComponent.Component):

    "A reinforcement bar (rebar) object for a rebar distribution"

    def __init__(
        self,
        obj
    ):
        ArchComponent.Component.__init__(self, obj)
        self.setProperties(obj)
        obj.IfcType = "Undefined"  # only set in rebar shape class
        obj.setEditorMode("IfcType", 2)
        # obj.setEditorMode("PredefinedType", 2)  # attribute no longer used?

    def setProperties(
        self,
        obj
    ):
        self.Type = "RebarDistribution"
        pl = obj.PropertiesList

        # ArchComponent properties will be inherited
        # lots of them are not needed, hide them in editor ATM
        obj.setEditorMode("Additions", 2)
        obj.setEditorMode("Axis", 2)
        obj.setEditorMode("Base", 2)
        obj.setEditorMode("HorizontalArea", 2)
        obj.setEditorMode("Material", 2)
        obj.setEditorMode("MoveBase", 2)
        obj.setEditorMode("MoveWithHost", 2)
        obj.setEditorMode("PerimeterLength", 2)
        obj.setEditorMode("StandardCode", 2)  # useful, but not used ATM
        obj.setEditorMode("Subtractions", 2)
        obj.setEditorMode("VerticalArea", 2)
        # CloneOf makes sense if two rebars are identical
        # but need different MarkNumber

        # New properties
        # Placements
        if "Placements" not in pl:
            obj.addProperty(
                "App::PropertyPlacementList",
                "Placements",
                "Rebar",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Placement for each rebar of the distribution"
                )
            )

        # BaseRebar
        # see my notes pros and cons which obj should link to which
        # search topic in forum and keep link here
        # direct access to BaseRebar is needed,
        # thus link from distribution to rebar shape
        # in rebar shape is distribution needed only for tree view
        # this can be done by a search in doc objects
        #
        # Could a distribution be used in more than one rebar shape
        # would make a collision between the two rebars
        # for this make a clone of the distribution
        # and move a little bit and use this on in the other rebar
        # than not collision
        if "BaseRebar" not in pl:
            obj.addProperty(
                "App::PropertyLink",
                "BaseRebar",
                "Rebar",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Base rebar for this distribution"
                )
            )

    def onDocumentRestored(
        self,
        obj
    ):
        ArchComponent.Component.onDocumentRestored(self, obj)
        self.setProperties(obj)

    def execute(
        self,
        obj  # why obj? self is the obj?
    ):
        if self.clone(obj):
            return
        if not obj.BaseRebar:
            return
        if not obj.Placements:
            return
        self.build_shape(obj)

        # set Visibility of BaseRebar
        # this should be done in the Gui Command,
        # but this dos not yet exist TODO
        # set view of base rebar to off
        # if distribution shape is not a null shape
        # TODO may be use another color for base rebar
        if FreeCAD.GuiUp:
            if obj.Shape.isNull() is not True:
                obj.BaseRebar.ViewObject.Visibility = False

    def build_shape(
        self,
        obj
    ):
        from Part import Shape as sh
        """
        if obj has no attribute Shape
        a empty Shape can not be assigned :-)
        if not hasattr(obj, 'Shape'):
            print('{} has no Shape'.format(obj.Label))
            obj.Shape = sh()
            return
        """
        if hasattr(obj, "BaseRebar") and obj.BaseRebar is None:
            FreeCAD.Console.PrintMessage(
                "BaseRebar property is not set for rebar distribution: {}. "
                "Shape the the distribution will be an empty shape.\n"
                .format(obj.Label)
            )
            obj.Shape = sh()
            return

        # build compound shape with base rebar and distribution placements
        shapes = []
        for pl in obj.Placements:
            bar = obj.BaseRebar.Shape.copy()
            bar.Placement = pl
            shapes.append(bar)
        if shapes:
            obj.Shape = Part.makeCompound(shapes)


class _ViewProviderRebarDistribution(_ViewProviderRebarBase):

    def getIcon(
        self
    ):
        import Arch_rc
        False if Arch_rc.__name__ else True  # dummy usage
        return ":/icons/Arch_Rebar_Tree.svg"


# ****************************************************************************
# rebar lattice2 distribution
def makeRebarDistributionLattice(
    base_rebar,
    latice_obj,
    name="RebarDistributionLattice"
):
    """
    makeRebarDistribution(base_rebar, placements, [name])
    Adds a reinforcement distribution object.
    """
    from lattice2BaseFeature import isObjectLattice as islattice
    if islattice(latice_obj) is not True:
        FreeCAD.Console.PrintError(
            "The object provided: {} is not a Lattice2 object\n"
            .format(latice_obj.Name)
        )
        return None

    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Rebar")
    obj.Label = translate("Arch", name)

    _RebarDistributionLattice(obj)
    if FreeCAD.GuiUp:
        _ViewProviderRebarDistributionLattice(obj.ViewObject)

    obj.BaseRebar = base_rebar
    obj.LatticePlacement = latice_obj

    # mark base_rebar obj for recompute to make it collect its new child
    base_rebar.touch()
    obj.Document.recompute()
    return obj


class _RebarDistributionLattice(_RebarDistribution):

    """A reinforcement bar (rebar) object
    for a rebar distribution based on a lattic2 placement"""

    def __init__(
        self,
        obj
    ):
        _RebarDistribution.__init__(self, obj)

        # self.setPropertiesLattice(obj)
        # why the Distribution properties should have been added ...
        # move to __init__ :-)

        self.Type = "RebarDistributionLattice"

        # LatticePlacement
        # can a distribution have multiple lattice placement
        # example stirrups of a column
        # but this will be difficault
        # to automatically create text for bar space etc
        # means not used ATM
        # further more dangerous because collisons,
        # cause double placements
        # same if one distribution in more rebar shapes
        # such is cool but corner cases could make problems
        if "LatticePlacement" not in obj.PropertiesList:
            obj.addProperty(
                "App::PropertyLink",
                "LatticePlacement",
                "Rebar",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Lattice placement obj for this distribution"
                )
            )

    def onDocumentRestored(
        self,
        obj
    ):
        ArchComponent.Component.onDocumentRestored(self, obj)
        self.setProperties(obj)

    def execute(
        self,
        obj
    ):
        if self.clone(obj):
            return
        if not obj.LatticePlacement:
            return

        from lattice2BaseFeature import isObjectLattice as islattice
        if islattice(obj.LatticePlacement) is True:
            from lattice2BaseFeature import getPlacementsList as getpl
            obj.Placements = getpl(obj.LatticePlacement)
            self.build_shape(obj)

            # set Visibility of BaseRebar
            # this should be done in the Gui Command,
            # but this dos not yet exist TODO
            # set view of base rebar to off
            # if distribution shape is not a null shape
            # TODO may be use another color for base rebar
            if FreeCAD.GuiUp:
                if obj.Shape.isNull() is not True:
                    obj.BaseRebar.ViewObject.Visibility = False
        else:
            FreeCAD.Console.PrintError(
                "The object provided: {} is not a Lattice2 object\n"
                .format(obj.Name)
            )


class _ViewProviderRebarDistributionLattice(_ViewProviderRebarDistribution):

    def getIcon(
        self
    ):
        import Arch_rc
        False if Arch_rc.__name__ else True  # dummy usage
        return ":/icons/Arch_Profile.svg"

    def claimChildren(
        self
    ):
        # collect the children for TreeView

        # children from Arch.Component
        # since we overwrite the method we need to explicit call it
        children = ArchComponent.ViewProviderComponent.claimChildren(self)

        # special rebar distribution children
        if hasattr(self, "Object"):

            # claim lattice2 placements for this rebar distribution lattice
            if self.Object.LatticePlacement is not None:
                children.append(self.Object.LatticePlacement)

            # print(children)
            return children
        return []

    # Drag and Drop for the children
    # TODO: implement Drag and Drop
