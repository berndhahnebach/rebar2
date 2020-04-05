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

__title__ = "FreeCAD reinforcement object"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD

import Arch
import ArchComponent
import Part

import rebar2

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
# reinforcement
def makeReinforcement(
    base_rebar,
    placements=[],
    base_placement=FreeCAD.Placement(),
    name="Reinforcement"
):
    """
    makeReinforcement(base_rebar, placements, [base_placement], [name])
    Adds a reinforcement object.
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Rebar")
    obj.Label = translate("Arch", name)

    _Reinforcement(obj)
    if FreeCAD.GuiUp:
        _ViewProviderReinforcement(obj.ViewObject)

    obj.BaseRebar = base_rebar
    obj.RebarPlacements = placements
    obj.BasePlacement = base_placement

    # mark base_rebar obj for recompute to make it collect its new child
    base_rebar.touch()
    obj.Document.recompute()
    return obj


class _Reinforcement(Arch.ArchComponent.Component):

    "A reinforcement object based on a rebar object"

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
        self.Type = "Reinforcement"
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

        # BaseRebar
        if "BaseRebar" not in pl:
            obj.addProperty(
                "App::PropertyLink",
                "BaseRebar",
                "Reinforcement",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Base rebar for this reinforcement"
                )
            )

        # RebarPlacements
        if "RebarPlacements" not in pl:
            obj.addProperty(
                "App::PropertyPlacementList",
                "RebarPlacements",
                "Reinforcement",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Placement for each rebar of the reinforcement"
                )
            )
        # TODO: Why ist this property not shown in PropertyEditor

        # BasePlacement
        if "BasePlacement" not in pl:
            obj.addProperty(
                "App::PropertyPlacement",
                "BasePlacement",
                "Reinforcement",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    (
                        "Rotations of the first rebar in "
                        "the reinforcement (Yaw-Pitch-Roll)"
                    )
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
        if not obj.RebarPlacements:
            return
        self.build_shape(obj)

        # set Visibility of BaseRebar
        # this should be done in the Gui Command,
        # but this dos not yet exist TODO
        # set view of base rebar to off
        # if reinforcement shape is not a null shape
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
                "BaseRebar property is not set for reinforcement: {}. "
                "Shape the the reinforcement will be an empty shape.\n"
                .format(obj.Label)
            )
            obj.Shape = sh()
            return

        # build compound shape with base rebar
        # and reinforcement placements and BasePlacement
        shapes = []
        for pl in obj.RebarPlacements:
            bar = obj.BaseRebar.Shape.copy()
            # ATM there is no check
            # if translation vector of BasePlacement is 0, 0, 0
            bar.Placement = pl.multiply(obj.BasePlacement)
            shapes.append(bar)
        if shapes:
            obj.Shape = Part.makeCompound(shapes)


class _ViewProviderReinforcement(rebar2._ViewProviderRebarBase):

    def getIcon(
        self
    ):
        import Arch_rc
        False if Arch_rc.__name__ else True  # dummy usage
        return ":/icons/Arch_Rebar_Tree.svg"


# ****************************************************************************
# rebar lattice2 reinforcement
def makeReinforcementLattice(
    base_rebar,
    latice_obj,
    base_placement=FreeCAD.Placement(),
    name="ReinforcementLattice"
):
    """
    makeReinforcementLattice(base_rebar, placements, [base_placement], [name])
    Adds a lattice reinforcement object.
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

    _ReinforcementLattice(obj)
    if FreeCAD.GuiUp:
        _ViewProviderReinforcementLattice(obj.ViewObject)

    obj.BaseRebar = base_rebar
    obj.LatticePlacement = latice_obj
    obj.BasePlacement = base_placement

    # mark base_rebar obj for recompute to make it collect its new child
    base_rebar.touch()
    obj.Document.recompute()
    return obj


class _ReinforcementLattice(_Reinforcement):

    """A reinforcement bar (rebar) object
    for a reinforcement based on a lattic2 placement"""

    def __init__(
        self,
        obj
    ):
        _Reinforcement.__init__(self, obj)

        # self.setPropertiesLattice(obj)
        # why the reinforcement properties should have been added ...
        # move to __init__ :-)

        self.Type = "ReinforcementLattice"

        # LatticePlacement
        # can a reinforcement have multiple lattice placement
        # example stirrups of a column
        # but this will be difficault
        # to automatically create text for bar space etc
        # means not used ATM
        # further more dangerous because collisons,
        # cause double placements
        # same if one reinforcement in more rebar shapes
        # such is cool but corner cases could make problems
        if "LatticePlacement" not in obj.PropertiesList:
            obj.addProperty(
                "App::PropertyLink",
                "LatticePlacement",
                "Reinforcement",
                QT_TRANSLATE_NOOP(
                    "App::Property",
                    "Lattice placement obj for this reinforcement"
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
            obj.RebarPlacements = getpl(obj.LatticePlacement)
            self.build_shape(obj)

            # set Visibility of BaseRebar
            # this should be done in the Gui Command,
            # but this dos not yet exist TODO
            # set view of base rebar to off
            # if reinforcement shape is not a null shape
            # TODO may be use another color for base rebar
            if FreeCAD.GuiUp:
                if obj.Shape.isNull() is not True:
                    obj.BaseRebar.ViewObject.Visibility = False
        else:
            FreeCAD.Console.PrintError(
                "The object provided: {} is not a Lattice2 object\n"
                .format(obj.Name)
            )


class _ViewProviderReinforcementLattice(_ViewProviderReinforcement):

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

        # special reinforcement children
        if hasattr(self, "Object"):

            # claim lattice2 placements for this reinforcement lattice
            if self.Object.LatticePlacement is not None:
                children.append(self.Object.LatticePlacement)

            # print(children)
            return children
        return []

    # Drag and Drop for the children
    # TODO: implement Drag and Drop
