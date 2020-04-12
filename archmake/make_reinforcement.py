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

__title__ = "FreeCAD arch make reinforcement"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD

from DraftTools import translate


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

    from archobjects.reinforcement import Reinforcement
    Reinforcement(obj)
    if FreeCAD.GuiUp:
        from archviewproviders.view_reinforcement import ViewProviderReinforcement
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
