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

# code for debugging and implementation of rebar ifc importer
# code to copy for rebar import
# may be there are some HACK s
# there have been takes place renamming and moving methods and class


# ************************************************************************************************
# ifc import into rebar2 objects *****************************************************************
# ************************************************************************************************

# ************************************************************************************************
# use new rebar2 module
import ifcopenshell, rebar2, Part, Draft, os
import lattice2Placement, lattice2JoinArrays, lattice2Executer
from FreeCAD import Vector as vec
from ifcopenshell.geom import settings
prefs = settings()
prefs.set(prefs.USE_BREP_DATA, True)
prefs.set(prefs.USE_WORLD_COORDS, True)
prefs.set(prefs.INCLUDE_CURVES, True)
prefs.set(prefs.EXCLUDE_SOLIDS_AND_SURFACES, True)

path_to_rebar2 = rebar2.__file__.rstrip(os.path.basename(rebar2.__file__))
ifcfile = path_to_rebar2 + "example_01_two_stirrups.ifc"  # imports :-)
# ifcfile = path_to_rebar2 + "example_02_channel_foundation.ifc"  # imports :-)
# ifcfile = path_to_rebar2 + "example_03_crane_foundation.ifc"  # does import crap, was exported with old Allplan exporter
# ifcfile = path_to_rebar2 + "example_04_vat.ifc"  # imports :-)
f = ifcopenshell.open(ifcfile)

for rebar in f.by_type("IfcReinforcingBar"):
    ifc_shape_representation = rebar.Representation.Representations[0]
    ifc_swept_disk_solid = ifc_shape_representation.Items[0].MappingSource.MappedRepresentation.Items[0]
    radius = ifc_swept_disk_solid.Radius
    entity_polyline = ifc_swept_disk_solid.Directrix

    # sweep path
    cr = ifcopenshell.geom.create_shape(prefs, entity_polyline)
    brep = cr.brep_data
    sweep_path = Part.Shape()
    sweep_path.importBrepFromString(brep)
    sweep_path.scale(1000.0)  # IfcOpenShell always outputs in meters
    wire = Draft.makeWire(sweep_path.Wires[0])

    # rebar shape
    markno = rebar.id()  # use ifc entity as mark number
    rebar_shape = rebar2.makeRebarShape(wire, diameter=2*radius, mark=markno, name="RebarShape_No_"+str(markno))

    # rebar distribution
    # TODO mght be there is only the first distribution of many distributions of the MarkNumber rebar
    # lattice2 placements
    custom_pls = []
    for ifc_mapped_item in ifc_shape_representation.Items:
        ifc_cartesian_point = ifc_mapped_item.MappingTarget.LocalOrigin
        coord = ifc_cartesian_point.Coordinates
        custom_pl = lattice2Placement.makeLatticePlacement(name=str(ifc_cartesian_point.id()))
        custom_pl.PlacementChoice = "Custom"
        custom_pl.MarkerSize = 25
        lattice2Executer.executeFeature(custom_pl)
        custom_pl.Placement = FreeCAD.Placement(vec(coord[0], coord[1], coord[2]), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))
        custom_pls.append(custom_pl)

    # lattice2 array placement
    cpa = lattice2JoinArrays.makeJoinArrays(name="CustomPlacementArray")
    cpa.Links = custom_pls
    cpa.MarkerSize = 25
    for child in cpa.ViewObject.Proxy.claimChildren():
        child.ViewObject.hide()

    lattice2Executer.executeFeature(cpa)
    ifc_cartesian_point_cpa = rebar.ObjectPlacement.RelativePlacement.Location
    coord_cpa = ifc_cartesian_point_cpa.Coordinates
    cpa_pl = FreeCAD.Placement(vec(coord_cpa[0], coord_cpa[1], coord_cpa[2]), FreeCAD.Rotation(vec(0,0,1),0), vec(0,0,0))
    cpa.Placement = cpa_pl

    # move rebar shape to the first bar of distribution
    rebar_shape.Placement = cpa_pl
    
    # rebar2 distribution
    rebdistribution6 = rebar2.makeRebarDistributionLattice(rebar_shape, cpa, name="Distribution_No"+str(markno))

FreeCAD.ActiveDocument.recompute()





# ************************************************************************************************
# ifc import other debug code ********************************************************************
# ************************************************************************************************

# ************************************************************************************************
# TODO better path implementation
import os, rebar2
path_to_rebar2 = rebar2.__file__.rstrip(os.path.basename(rebar2.__file__))
print(path_to_rebar2)


# ************************************************************************************************
# length scale unit
import os, rebar2, ifcopenshell
path_to_rebar2 = rebar2.__file__.rstrip(os.path.basename(rebar2.__file__))

ifcfile = path_to_rebar2 + "example_01_two_stirrups.ifc"  # imports :-)
# ifcfile = path_to_rebar2 + "example_03_crane_foundation.ifc"

f = ifcopenshell.open(ifcfile)
f.by_type('IfcProject')
prj_units = f.by_type('IfcProject')[0].UnitsInContext.Units
scale_length = 1.0
found_length_unit = False
for u in prj_units:
    if u.UnitType == "LENGTHUNIT":
        if found_length_unit is False:
            found_length_unit = True
            # print(u.Prefix)
            # print(u.Name)
            if u.Prefix == "MILLI" and u.Name == "METRE":
                scale_length = 1.0
            elif u.Prefix is None and u.Name == "METRE":
                scale_length = 0.001
            else:
                print("Not known length unit found, set attribute length scale to 1.0")
                print(u)
                scale_length = 1.0
        else:
            print("Two LENGTHUNIT defined, this is not allowed in IFC-Standard.")

print(scale_length)




# ************************************************************************************************
import ifcopenshell, os, Part

# from importIFC
from ifcopenshell import geom
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_BREP_DATA,True)
settings.set(settings.SEW_SHELLS,True)
settings.set(settings.USE_WORLD_COORDS,True)

from platform import system
if system() == "Windows":
    ifcfile = 'C:/Users/BHA/Desktop/example_01_two_stirrups.ifc'
elif system() == "Linux":
    ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
    # ifcfile = '/home/hugo/Desktop/example_01_two_stirrups.ifc'
else:
    print("not known OS")

f = ifcopenshell.open(ifcfile)

f.by_type('IfcProject')
f.by_type('IfcPerson')
f.by_type('IfcReinforcingBar')

p = f.by_id(275)
r = p.Representation
print(p, '\n', r)
# to find the attribute names ...
print(p.attribute_name(0))

# make a new FreeCAD document
cr = ifcopenshell.geom.create_shape(settings, p)
brep = cr.geometry.brep_data
shape = Part.Shape()
shape.importBrepFromString(brep)
Part.show(shape)



# *********************************************************************************** 
# https://sourceforge.net/p/ifcopenshell/discussion/1782716/thread/0d5d207b67/
# *********************************************************************************** 
# all rebars of specific mark number, curve
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
import ifcopenshell
f = ifcopenshell.open(ifcfile)
f.by_type('IfcReinforcingBar')
p = f.by_id(275)

from ifcopenshell.geom import settings
prefs = settings()
prefs.set(prefs.USE_BREP_DATA, True)
prefs.set(prefs.SEW_SHELLS, True)
prefs.set(prefs.USE_WORLD_COORDS, True)
prefs.set(prefs.INCLUDE_CURVES, True)
prefs.set(prefs.EXCLUDE_SOLIDS_AND_SURFACES, True)
cr = ifcopenshell.geom.create_shape(prefs, p)


# *********************************************************************************** 
# polyline curve
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
import ifcopenshell
f = ifcopenshell.open(ifcfile)
f.by_type('IfcPolyline')
p = f.by_id(83)

from ifcopenshell.geom import settings
prefs = settings()
prefs.set(prefs.USE_BREP_DATA, True)
prefs.set(prefs.USE_WORLD_COORDS, True)
prefs.set(prefs.INCLUDE_CURVES, True)
prefs.set(prefs.EXCLUDE_SOLIDS_AND_SURFACES, True)
cr = ifcopenshell.geom.create_shape(prefs, p)
brep = cr.brep_data
shape.importBrepFromString(brep)
shape.scale(1000.0)  # IfcOpenShell always outputs in meters
Part.show(shape)


# *********************************************************************************** 
# verteilung
import ifcopenshell

# ifcfile = 'C:/Users/BHA/Desktop/example_01_two_stirrups.ifc'
#ifcfile = 'C:/Users/BHA/Desktop/example_04_vat.ifc'
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
f = ifcopenshell.open(ifcfile)
f.by_type('IfcReinforcingBar')

for rebar in f.by_type('IfcReinforcingBar'):
    rs = rebar.Representation.Representations[0]
    print(rs)
    target = rs.Items[0].MappingSource
    print(target)  # swept solid
    for item in rs.Items:
        if item.MappingSource != target:
            print(item.MappingSource)
        mt = item.MappingTarget
        # mt
        # mt.Axis2
        mt.LocalOrigin
    print('\n')



p = f.by_id(275)
#p = f.by_id(366)
p
r = p.Representation
rs = r.Representations[0]
rs.Items
target = rs.Items[0].MappingSource
print(target)  # swept solid
for item in rs.Items:
    if item.MappingSource != target:
        print(item.MappingSource)
    mt = item.MappingTarget
    mt
    mt.Axis2
    mt.LocalOrigin



p = f.by_id(275)
r = p.Representation
rs = r.Representations[0].item1 = rs.Items[0]
item1.MappingSource
mt1 = item1.MappingTarget
mt1.Axis2

print(p, '\n', r)
# to find the attribute names ...
print(rs.attribute_name(0))
p.get_info().keys()


# ***********************************************************************************
# create a rebar from polyline curve
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
import ifcopenshell, Part
f = ifcopenshell.open(ifcfile)
entity_polyline = f.by_id(215).Directrix  # the polyline to sweep allong
radius = f.by_id(215).Radius
# radius = f.by_id(215).Radius * 0.999  # to get a Shape without self intersections


from ifcopenshell.geom import settings
prefs = settings()
prefs.set(prefs.USE_BREP_DATA, True)
prefs.set(prefs.USE_WORLD_COORDS, True)
prefs.set(prefs.INCLUDE_CURVES, True)
prefs.set(prefs.EXCLUDE_SOLIDS_AND_SURFACES, True)

cr = ifcopenshell.geom.create_shape(prefs, entity_polyline)
brep = cr.brep_data
sweep_path = Part.Shape()
sweep_path.importBrepFromString(brep)
sweep_path.scale(1000.0)  # IfcOpenShell always outputs in meters
Part.show(sweep_path)

wire = sweep_path.Wires[0]
e = wire.Edges[0]
pnt1 = e.firstVertex().Point
pnt2 = e.lastVertex().Point
direction = pnt2 - pnt1
circle = Part.makeCircle(radius, pnt1, direction)
Part.show(circle)
circle = Part.Wire(circle)
try:
    bar = wire.makePipeShell([circle],True,False,2)
except Part.OCCError:
    print("Arch: error sweeping rebar profile along the base sketch")

Part.show(bar)


# ***********************************************************************************
# create a rebar from polyline curve, improved
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
import ifcopenshell
f = ifcopenshell.open(ifcfile)
es = f.by_id(275).Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[0]
es.Radius
es.Directrix

es = f.by_id(366).Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[0]
es.Radius
es.Directrix

# ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
ifcfile = 'C:/Users/BHA/Desktop/example_04_vat.ifc'
import ifcopenshell
f = ifcopenshell.open(ifcfile)
for rebar in f.by_type('IfcReinforcingBar'):
    es = rebar.Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[0]
    es.Radius
    es.Directrix


# ***********************************************************************************
# create a rebar from polyline curve, for all rebars of a file
import ifcopenshell, Part
from ifcopenshell.geom import settings
prefs = settings()
prefs.set(prefs.USE_BREP_DATA, True)
prefs.set(prefs.USE_WORLD_COORDS, True)
prefs.set(prefs.INCLUDE_CURVES, True)
prefs.set(prefs.EXCLUDE_SOLIDS_AND_SURFACES, True)

# ifcfile = 'C:/Users/BHA/Desktop/example_04_vat.ifc'
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
f = ifcopenshell.open(ifcfile)

for rebar in f.by_type('IfcReinforcingBar'):
    es = rebar.Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[0]
    radius = es.Radius
    entity_polyline = es.Directrix
    
    # sweep path
    cr = ifcopenshell.geom.create_shape(prefs, entity_polyline)
    brep = cr.brep_data
    sweep_path = Part.Shape()
    sweep_path.importBrepFromString(brep)
    sweep_path.scale(1000.0)  # IfcOpenShell always outputs in meters
    Part.show(sweep_path)
    wire = sweep_path.Wires[0]
    
    # sweep profile
    e = wire.Edges[0]
    pnt1 = e.firstVertex().Point
    pnt2 = e.lastVertex().Point
    direction = pnt2 - pnt1
    circle = Part.makeCircle(radius, pnt1, direction)
    Part.show(circle)
    circle = Part.Wire(circle)
    
    # make rebar by sweep
    try:
        bar = wire.makePipeShell([circle],True,False,2)
    except Part.OCCError:
        print("Arch: error sweeping rebar profile along the base sketch")
    
    Part.show(bar)

# :-)



# ***********************************************************************************
import ifcopenshell
ifcfile = '/home/hugo/.FreeCAD/Mod/archrebarnew/example_01_two_stirrups.ifc'
f = ifcopenshell.open(ifcfile)

for rebar in f.by_type('IfcReinforcingBar'):
    rs = rebar.Representation.Representations[0]
    print(rs)
    target = rs.Items[0].MappingSource
    print(target)  # swept solid
    for item in rs.Items:
        if item.MappingSource != target:
            print(item.MappingSource)
        mt = item.MappingTarget
        # mt
        # mt.Axis2
        mt.LocalOrigin
    print('\n')


for rebar in f.by_type('IfcReinforcingBar'):
    print(rebar)


rebar.ObjectPlacement

rebar.ObjectPlacement.PlacementRelTo.RelativePlacement.Location  # should be 0,0,0 ... #68=IfcCartesianPoint((0.,0.,0.))

rebar.ObjectPlacement.RelativePlacement.Location  # is the placement of the array distribution as IfcCartesianPoint

