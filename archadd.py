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

__title__ = "FreeCAD arch make objects methods"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD

# move into the make methods
from archobjects.base_rebar import BaseRebar
from archobjects.reinforcement import Reinforcement
from archobjects.reinforcement_lattice import ReinforcementLattice

from archgui.view_base_rebar import ViewProviderBaseRebar
from archgui.view_reinforcement import ViewProviderReinforcement
from archgui.view_reinforcement_lattice import ViewProviderReinforcementLattice

from DraftTools import translate


# ****************************************************************************
# base reinforcement bar (rebar)
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
# standard reinforcement object
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

    Reinforcement(obj)
    if FreeCAD.GuiUp:
        ViewProviderReinforcement(obj.ViewObject)

    obj.BaseRebar = base_rebar
    obj.RebarPlacements = placements
    obj.BasePlacement = base_placement
    obj.Amount = len(placements)
    obj.TotalLength = obj.Amount * base_rebar.Length

    # mark base_rebar obj for recompute to make it collect its new child
    base_rebar.touch()
    obj.Document.recompute()
    return obj


# ****************************************************************************
# lattice2 reinforcement object
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

    ReinforcementLattice(obj)
    if FreeCAD.GuiUp:
        ViewProviderReinforcementLattice(obj.ViewObject)

    obj.BaseRebar = base_rebar
    obj.LatticePlacement = latice_obj
    obj.BasePlacement = base_placement

    # mark base_rebar obj for recompute to make it collect its new child
    base_rebar.touch()
    obj.Document.recompute()
    return obj
