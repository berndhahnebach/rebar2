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

# sample code to copy to create and import rebars
# TODO
# put code in defs and use import to easily run the code
# use for unit tests and documentation

import importlib
importlib.reload(rebar2)


# ************************************************************************************************
# standard FreeCAD rebar *************************************************************************
# ************************************************************************************************

# ************************************************************************************************
# https://forum.freecadweb.org/viewtopic.php?f=23&t=35849
# code to make a rebar based on a simple wire
from FreeCAD import Vector as vec
import FreeCAD, Arch, Draft
Wire = Draft.makeWire([vec(0, 2000, 0), vec(0, 2000, 2000)])
Rebar = Arch.makeRebar(None, Wire, diameter=30, amount=1)
FreeCAD.ActiveDocument.recompute()


# code to make a rebar based on a wire and a structure
import FreeCAD, Arch, Draft
from FreeCAD import Vector as vec
myh = 3000

Structure = Arch.makeStructure(None, length=1000, width=1000, height=myh)
Structure.ViewObject.Transparency = 80
FreeCAD.ActiveDocument.recompute()

p1 = vec(0, 0, 0)
p2 = vec(0, 0, myh)
Wire1 = Draft.makeWire([p1, p2])
FreeCAD.ActiveDocument.recompute()

Rebar = Arch.makeRebar(Structure, Wire1, diameter=30, amount=1, offset=0)
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# rebar2 *****************************************************************************************
# ************************************************************************************************

# ************************************************************************************************
# rebar distributed with placements created with Draft
import FreeCAD, Arch, Draft, rebar2
from FreeCAD import Vector as vec
wire1 = Draft.makeWire([vec(0, 0, 0), vec(0, 0, 1000)])
rebshape1 = rebar2.makeRebarShape(wire1, diameter=100, mark=1, name="Rebar1")
FreeCAD.ActiveDocument.recompute()

import DraftVecUtils
pl_list = []
rot = FreeCAD.Rotation()
move = 0
for i in range(10):
    move += 150 
    barplacement = DraftVecUtils.scaleTo(FreeCAD.Base.Vector(0, 1, 0), move)
    pl_list.append(FreeCAD.Placement(barplacement, rot))

rebdistribution1 = rebar2.makeRebarDistribution(rebshape1, pl_list, name="Distribution1")
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# rebar distributed with placements retrieved from a lattic2 placement
# since only the placements of the lattice2 object are used,
# the lattice2 object stays outside in tree
import FreeCAD, Arch, Draft, rebar2
from FreeCAD import Vector as vec
wire3 = Draft.makeWire([vec(0, 0, 0), vec(0, 0, 2000)])
rebshape3 = rebar2.makeRebarShape(wire3, diameter=30, mark=1, name="Rebar2")
FreeCAD.ActiveDocument.recompute()

# linear placements with lattice2
import lattice2LinearArray, lattice2Executer
la = lattice2LinearArray.makeLinearArray(name="LinearArray")
la.GeneratorMode = "StepN"
la.Alignment = "Justify"  # https://forum.freecadweb.org/viewtopic.php?f=22&t=37657#p320586
la.SpanEnd = 1500
la.Count = 5
# 1500/5 = 300
la.MarkerSize = 100
lattice2Executer.executeFeature(la)
FreeCAD.ActiveDocument.recompute()

from lattice2BaseFeature import getPlacementsList as getpl
# standard distributions, only the placments of the lattice2 use the placements, 
rebdistribution2 = rebar2.makeRebarDistribution(rebshape3, placements=getpl(la), name="Distribution2")
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# rebars distributed by lattice2 placements
import FreeCAD, Arch, Draft, rebar2
from FreeCAD import Vector as vec
wire2 = Draft.makeWire([vec(300, 0, 0), vec(0, 0, 0), vec(0, 0, 140), vec(300, 0, 140)])
rebshape2 = rebar2.makeRebarShape(wire2, diameter=30, mark=2, name="Rebar3")
FreeCAD.ActiveDocument.recompute()

# linear placements with lattice2
import lattice2LinearArray, lattice2Executer
la = lattice2LinearArray.makeLinearArray(name="LinearArray")
la.GeneratorMode = "StepN"
la.Alignment = "Justify"  # https://forum.freecadweb.org/viewtopic.php?f=22&t=37657#p320586
la.SpanEnd = 5000
la.Count = 10
# 5000/10 = 500
la.MarkerSize = 100
la.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 6000, 0),
    FreeCAD.Rotation(0, 0, 0),
    FreeCAD.Vector(0, 0, 0),
)
lattice2Executer.executeFeature(la)

# polar placements with lattice2
import lattice2PolarArray2, lattice2Executer
pa = lattice2PolarArray2.make()
pa.GeneratorMode = "SpanN"
pa.Radius = 500
pa.MarkerSize = 100
pa.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 3000, 0),
    FreeCAD.Rotation(0, 0, 0),
    FreeCAD.Vector(0, 0, 0),
)
lattice2Executer.executeFeature(pa)
# TODO something deos not work if the pa is not at coortinate origin

# custom single placement with lattice2
import lattice2Placement, lattice2JoinArrays, lattice2Executer
cs1 = lattice2Placement.makeLatticePlacement(name="CustomSingelPlacment1")
cs1.PlacementChoice = "Custom"
cs1.MarkerSize = 100
lattice2Executer.executeFeature(cs1)
cs1.Placement=FreeCAD.Placement(vec(0,7000,1000), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))

# custom array placement with lattice2
import lattice2Placement, lattice2JoinArrays, lattice2Executer
ca1 = lattice2Placement.makeLatticePlacement(name="CustomPlacmentForArray1")
ca1.PlacementChoice = "Custom"
ca1.MarkerSize = 100
lattice2Executer.executeFeature(ca1)
ca1.Placement=FreeCAD.Placement(vec(200,6500,200), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))
ca2 = lattice2Placement.makeLatticePlacement(name="CustomPlacmentForArray2")
ca2.PlacementChoice = "Custom"
ca2.MarkerSize = 100
lattice2Executer.executeFeature(ca2)
ca2.Placement=FreeCAD.Placement(vec(200,6600,-200), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))
FreeCAD.ActiveDocument.recompute()
cpa = lattice2JoinArrays.makeJoinArrays(name="CustomPlacementArray")
cpa.Links = [ca1, ca2]
for child in cpa.ViewObject.Proxy.claimChildren():
    child.ViewObject.hide()

lattice2Executer.executeFeature(cpa)

# lattice2 distribution
rebdistribution3 = rebar2.makeRebarDistributionLattice(rebshape2, la, name="Distribution3")
rebdistribution3 = rebar2.makeRebarDistributionLattice(rebshape2, pa, name="Distribution4")
rebdistribution4 = rebar2.makeRebarDistributionLattice(rebshape2, cs1, name="Distribution5")
rebdistribution5 = rebar2.makeRebarDistributionLattice(rebshape2, cpa, name="Distribution6")
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# ifc import *************************************************************************************
# ************************************************************************************************

# ************************************************************************************************
# bernd min geometry importer, geometry only as solids
import importIFCmin, os, rebar2
path_to_rebar2 = rebar2.__file__.rstrip(os.path.basename(rebar2.__file__))
importIFCmin.open(path_to_rebar2 + "example_01_two_stirrups.ifc")


# ************************************************************************************************
# FreeCAD ifc importer
import importIFC, os, rebar2
importIFC.open(path_to_rebar2 + "example_01_two_stirrups.ifc")


# ************************************************************************************************
# rebar importer which usees rebar2
import os, rebar2, importIFCrebar
path_to_rebar2 = rebar2.__file__.rstrip(os.path.basename(rebar2.__file__))
importIFCrebar.open(path_to_rebar2 + "example_01_two_stirrups.ifc")  # imports :-)
# importIFCrebar.open(path_to_rebar2 + "example_02_channel_foundation.ifc")  # imports :-)
# importIFCrebar.open(path_to_rebar2 + "example_03_crane_foundation.ifc")  # does import crap, was exported with old Allplan exporter
# importIFCrebar.open(path_to_rebar2 + "example_04_vat.ifc")  # imports :-)
FreeCAD.ActiveDocument.recompute()


# for debuging with reload of importer
import importIFCrebar
import importlib
importlib.reload(importIFCrebar)
importIFCrebar.open(path_to_rebar2 + "example_01_two_stirrups.ifc")  # imports :-)
FreeCAD.ActiveDocument.recompute()

