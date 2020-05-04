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
# archadd and ArchReinforcement ************************************************************
# ************************************************************************************************

# ************************************************************************************************
# reinforcment with base rebar, rebar placements created with Draft
import FreeCAD, Arch, Draft, archadd
from FreeCAD import Vector as vec
wire1 = Draft.makeWire([vec(0, 0, 0), vec(0, 0, 1000)])
baserebar1 = archadd.BaseRebar(wire1, diameter=100, mark=1, name="BaseRebar_1")
FreeCAD.ActiveDocument.recompute()

import DraftVecUtils
pl_list = []
rot = FreeCAD.Rotation()
move = 0
for i in range(10):
    move += 150 
    barlocation = DraftVecUtils.scaleTo(FreeCAD.Base.Vector(1, 0, 0), move)
    pl_list.append(FreeCAD.Placement(barlocation, rot))

archadd.ReinforcementGeneric(baserebar1, pl_list, name="Reinforcement_1")
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# reinforcment with base rebar, rebar placement retrieved from a lattice2 placement
# since only the placements of the lattice2 object are used,
# the lattice2 object stays outside in tree view
import FreeCAD, Draft, archadd
from FreeCAD import Vector as vec
wire2 = Draft.makeWire([vec(0, 0, 0), vec(0, 0, 2000)])
baserebar2 = archadd.BaseRebar(wire2, diameter=30, mark=2, name="BaseRebar_2")
FreeCAD.ActiveDocument.recompute()

# linear placements with lattice2
import lattice2LinearArray, lattice2Executer
la1 = lattice2LinearArray.makeLinearArray(name="LinearArray")
la1.GeneratorMode = "StepN"
la1.Alignment = "Justify"  # https://forum.freecadweb.org/viewtopic.php?f=22&t=37657#p320586
la1.SpanEnd = 1500
la1.Count = 5
# 1500/5 = 300
la1.MarkerSize = 100
la1.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 2500, 0),
    FreeCAD.Rotation(0, 0, 0),
    FreeCAD.Vector(0, 0, 0),
)
lattice2Executer.executeFeature(la1)
FreeCAD.ActiveDocument.recompute()

from lattice2BaseFeature import getPlacementsList as getpl
# standard reinforcement, only the placments of the lattice2 use the placements, 
archadd.ReinforcementGeneric(baserebar2, placements=getpl(la1), name="Reinforcement_2")
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# reinforcment with base rebar, rebar placements with lattice2 placement
import FreeCAD, Draft, archadd
from FreeCAD import Vector as vec
wire3 = Draft.makeWire([vec(300, 0, 0), vec(0, 0, 0), vec(0, 0, 140), vec(300, 0, 140)])
baserebar3 = archadd.BaseRebar(wire3, diameter=30, mark=3, name="BaseRebar_3")
FreeCAD.ActiveDocument.recompute()

# linear placements with lattice2
import lattice2LinearArray, lattice2Executer
la2 = lattice2LinearArray.makeLinearArray(name="LinearArray")
la2.GeneratorMode = "StepN"
la2.Alignment = "Justify"  # https://forum.freecadweb.org/viewtopic.php?f=22&t=37657#p320586
la2.SpanEnd = 5000
la2.Count = 10
# 5000/10 = 500
la2.MarkerSize = 100
la2.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 5000, 0),
    FreeCAD.Rotation(0, 0, 0),
    FreeCAD.Vector(0, 0, 0),
)
lattice2Executer.executeFeature(la2)

# polar placements with lattice2
import lattice2PolarArray2, lattice2Executer
pa1 = lattice2PolarArray2.make()
pa1.GeneratorMode = "SpanN"
pa1.Radius = 500
pa1.MarkerSize = 100
pa1.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 7500, 0),
    FreeCAD.Rotation(0, 0, 0),
    FreeCAD.Vector(0, 0, 0),
)
lattice2Executer.executeFeature(pa1)
# TODO something deos not work if the pa is not at coortinate origin

# custom single placement with lattice2
import lattice2Placement, lattice2JoinArrays, lattice2Executer
cs1 = lattice2Placement.makeLatticePlacement(name="CustomSinglePlacement1")
cs1.PlacementChoice = "Custom"
cs1.MarkerSize = 100
lattice2Executer.executeFeature(cs1)
cs1.Placement=FreeCAD.Placement(vec(0,10000,1000), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))

# custom array placement with lattice2
import lattice2Placement, lattice2JoinArrays, lattice2Executer
ca1 = lattice2Placement.makeLatticePlacement(name="CustomPlacementForArray1")
ca1.PlacementChoice = "Custom"
ca1.MarkerSize = 100
lattice2Executer.executeFeature(ca1)
ca1.Placement=FreeCAD.Placement(vec(200,10500,200), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))
ca2 = lattice2Placement.makeLatticePlacement(name="CustomPlacmentForArray2")
ca2.PlacementChoice = "Custom"
ca2.MarkerSize = 100
lattice2Executer.executeFeature(ca2)
ca2.Placement=FreeCAD.Placement(vec(200,10600,-200), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))
FreeCAD.ActiveDocument.recompute()
cpa = lattice2JoinArrays.makeJoinArrays(name="CustomPlacementArray")
cpa.Links = [ca1, ca2]
for child in cpa.ViewObject.Proxy.claimChildren():
    child.ViewObject.hide()

lattice2Executer.executeFeature(cpa)

# base placement to rotate the rebar in linear distribution
# base_placement1
translation = FreeCAD.Vector(0, 0, 0)
rotaxis = FreeCAD.Vector(0, 0, 1)
rotangle = 90  # degrees
base_placement1 = FreeCAD.Placement(translation,FreeCAD.Rotation(rotaxis,rotangle))

# lattice2 distribution
archadd.ReinforcementLattice(baserebar3, la2, base_placement1, "Reinforcement_3")
archadd.ReinforcementLattice(baserebar3, pa1, name="Reinforcement_4")
archadd.ReinforcementLattice(baserebar3, cs1, name="Reinforcement_5")
archadd.ReinforcementLattice(baserebar3, cpa, name="Reinforcement_6")
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# reinforcment linear with base rebar
# rebar placements calculated inside linear reinforcement object based on its attributes
import FreeCAD, Draft, archadd
from FreeCAD import Vector as vec
wire4 = Draft.makeWire([vec(0, 0, 0), vec(3000, 0, 0)])
baserebar4 = archadd.BaseRebar(wire4, diameter=30, mark=4, name="BaseRebar_4")
FreeCAD.ActiveDocument.recompute()
archadd.ReinforcementLinear(baserebar4, amount=20, spacing=100, name="Reinforcement_7")
FreeCAD.ActiveDocument.recompute()

# ************************************************************************************************
# reinforcment individual with base rebar
# rebar placements calculated inside individual reinforcement object based on linked vertieces
import FreeCAD, Draft, archadd
from FreeCAD import Vector as vec
wire5 = Draft.makeWire([vec(0, 0, 0), vec(0, 0, 500)])
baserebar5 = archadd.BaseRebar(wire5, diameter=14, mark=5, name="BaseRebar_5")
doc = FreeCAD.ActiveDocument
v1 = doc.addObject("Part::Vertex","Vertex1")
v1.X = 300
v1.Y = 150
v1.Z = 200
v1.ViewObject.PointColor=(1.0,0.7,0.0,0.0)
v1.ViewObject.PointSize=20
v2 = doc.addObject("Part::Vertex","Vertex2")
v2.X = 200
v2.Y = 100
v2.Z = 50
v2.ViewObject.PointColor=(1.0,0.7,0.0,0.0)
v2.ViewObject.PointSize=20
v3 = doc.addObject("Part::Vertex","Vertex3")
v3.X = 400
v3.Y = 250
v3.Z = 100
v3.ViewObject.PointColor=(1.0,0.7,0.0,0.0)
v3.ViewObject.PointSize=20
doc.recompute()
archadd.ReinforcementIndividual(baserebar5, vertieces=[v1, v2, v3], name="Reinforcement_8")
doc.recompute()

# ************************************************************************************************
# reinforcment custom with base rebar
# rebar placements calculated inside custom reinforcement object based on custom spacing
import FreeCAD, Draft, archadd
from FreeCAD import Vector as vec
wire6 = Draft.makeWire([vec(0, 0, 0), vec(0, 1000, 0)])
baserebar6 = archadd.BaseRebar(wire6, diameter=30, mark=6, name="BaseRebar_6")
FreeCAD.ActiveDocument.recompute()
custom = "5@100+10@200+5@100"
archadd.ReinforcementCustom(baserebar6, custom, name="Reinforcement_9")
FreeCAD.ActiveDocument.recompute()

# ************************************************************************************************
# base rebar with rounding
import FreeCAD, Draft, archadd
from FreeCAD import Vector as vec
wire7 = Draft.makeWire([vec(0, 0, 0), vec(0, -300, 0), vec(500, -300, 0), vec(500, 0, 0)])
baserebar7 = archadd.BaseRebar(wire7, diameter=30, mark=7, name="BaseRebar_7")
baserebar7.Rounding = 2
FreeCAD.ActiveDocument.recompute()


# ************************************************************************************************
# ifc import *************************************************************************************
# ************************************************************************************************

# ************************************************************************************************
# bernd min geometry importer, geometry only as solids
import importIFCmin, os, archadd
path_to_importIFCrebar = archadd.__file__.rstrip(os.path.basename(archadd.__file__))
importIFCmin.open(path_to_importIFCrebar + "example_01_two_stirrups.ifc")


# ************************************************************************************************
# FreeCAD ifc importer
import importIFC, os, archadd
importIFC.open(path_to_importIFCrebar + "example_01_two_stirrups.ifc")


# ************************************************************************************************
# rebar importer which uses rebar2
import os, importIFCrebar
path_to_importIFCrebar = importIFCrebar.__file__.rstrip(os.path.basename(importIFCrebar.__file__))
importIFCrebar.open(path_to_importIFCrebar + "example_01_two_stirrups.ifc")
# importIFCrebar.open(path_to_importIFCrebar + "example_02_channel_foundation.ifc")  # takes looong
importIFCrebar.open(path_to_importIFCrebar + "example_03_crane_foundation.ifc")
importIFCrebar.open(path_to_importIFCrebar + "example_04_vat.ifc")
FreeCAD.ActiveDocument.recompute()


# for debugging with reload of importer
import importIFCrebar
import importlib
importlib.reload(importIFCrebar)
importIFCrebar.open(path_to_importIFCrebar + "example_01_two_stirrups.ifc")
FreeCAD.ActiveDocument.recompute()


# flake8 archadd.py
"""
codespell -q 2 -S *.ts  -L childs,vertexes *
flake8 importIFCrebar.py
flake8 archobjects/base_rebar.py
flake8 archobjects/reinforcement_custom.py
flake8 archobjects/reinforcement_generic.py
flake8 archobjects/reinforcement_lattice.py 
flake8 archobjects/reinforcement_linear.py
flake8 archobjects/reinforcement_individual.py
flake8 archviewproviders/view_base_rebar.py 
flake8 archviewproviders/view_rebar_generic.py 
flake8 archviewproviders/view_reinforcement_custom.py 
flake8 archviewproviders/view_reinforcement_generic.py 
flake8 archviewproviders/view_reinforcement_lattice.py
flake8 archviewproviders/view_reinforcement_linear.py
flake8 archviewproviders/view_reinforcement_individual.py
flake8 archmake/make_base_rebar.py 
flake8 archmake/make_reinforcement_custom.py 
flake8 archmake/make_reinforcement_generic.py 
flake8 archmake/make_reinforcement_lattice.py
flake8 archmake/make_reinforcement_linear.py
flake8 archmake/make_reinforcement_individual.py


"""
