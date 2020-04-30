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

"""
Export:
Only the reinforcement objs should be exported not the base rebar objs.
https://forum.freecadweb.org/viewtopic.php?f=39&t=35848

Import:
If a mark number (Postion) exists, no new base rebar will be created.
The existant base rebar which starts on 0, 0, 0 will be used.
It would make sense to create all base rebars in x-y-plain

"""

__title__ = "FreeCAD rebar IFC importer based on Yorik van Havres IFC importer"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import os

import FreeCAD
from FreeCAD import Vector as vec

import Draft
import Part
from exportIFC import getPropertyData
from importIFCHelper import decode as ifcdecode
from importIFCHelper import getIfcProperties
from importIFCHelper import getIfcPropertySets

import archadd
import lattice2Executer
import lattice2JoinArrays
import lattice2LinearArray
import lattice2Placement

if FreeCAD.GuiUp:
    import FreeCADGui


if open.__module__ == "__builtin__":
    pyopen = open  # because we'll redefine open below


def getPreferences():
    """retrieves IFC preferences"""
    global DEBUG, SKIP, FITVIEW_ONIMPORT, ROOT_ELEMENT
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch")
    SKIP = p.GetString("ifcSkip", "").split(",")
    ROOT_ELEMENT = p.GetString("ifcRootElement", "IfcProduct")
    FITVIEW_ONIMPORT = p.GetBool("ifcFitViewOnImport", False)
    DEBUG = True

    # strandard will be no lattice placement for reinforcement
    global REINFORCEMENT_LATTICE
    REINFORCEMENT_LATTICE = p.GetBool("ifcReinforcmentType", False)
    # REINFORCEMENT_LATTICE = True


def open(filename, skip=[], only=[], root=None):
    "opens an IFC file in a new document"
    docname = os.path.splitext(os.path.basename(filename))[0]
    docname = ifcdecode(docname, utf=True)
    doc = FreeCAD.newDocument(docname)
    doc.Label = docname
    doc = insert(filename, doc.Name, skip, only, root)
    return doc


def insert(filename, docname, skip=[], only=[], root=None):
    """insert(filename,docname,skip=[],only=[],root=None):
    imports the contents of an IFC file.
    skip can contain a list of ids of objects to be skipped,
    only can restrict the import to certain object ids
    (will also get their children) and root can be used to
    import only the derivates of a certain element type
    (default = ifcProduct)."""

    getPreferences()

    # *****************************************************************
    # we are going to overwrite skip and only
    # needs to be after getPreferences
    # skip = [1030, 1922, 9813, 13030, 28999, 30631, 34909, 39120]
    #
    # only = [679567]
    # add this modules to the modules to reload on my reload tool

    try:
        import ifcopenshell
    except:
        FreeCAD.Console.PrintError(
            "IfcOpenShell was not found on this system. "
            "IFC support is disabled\n"
        )
        return

    if DEBUG:
        print("Opening ", filename, "...", end="")
    try:
        doc = FreeCAD.getDocument(docname)
    except:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc

    if DEBUG:
        print("done.")

    global ROOT_ELEMENT
    if root:
        ROOT_ELEMENT = root

    from ifcopenshell import geom
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_BREP_DATA, True)
    settings.set(settings.SEW_SHELLS, True)
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, False)
    settings.set(settings.INCLUDE_CURVES, True)
    settings.set(settings.EXCLUDE_SOLIDS_AND_SURFACES, True)

    # global ifcfile # keeping global for debugging purposes
    filename = ifcdecode(filename, utf=True)
    ifcfile = ifcopenshell.open(filename)

    # get the length scale facter from of unit of the ifc file
    length_scale = get_prj_unit_length_scale(ifcfile)
    print("Length scale = {}\n".format(length_scale))

    reinforcements = ifcfile.by_type("IfcReinforcingBar")
    rebar_objs = []
    base_rebars = {}  # {rebar_mark_number : rebar_obj}
    reinforcement_counter = 1

    # reinforcements
    for pno, rebar in enumerate(reinforcements):
        pid = rebar.id()
        ptype = rebar.is_a()
        print("Product {} of {} is Entity #{}: {}, ".format(
            pno + 1,
            len(reinforcements),
            pid,
            ptype,
        ), end="", flush=True)

        if pid in skip:
            print(" --> is in skip list, thus skipped", end="\n")
            continue
        if only and pid not in only:
            print(
                " --> only list is no empty and pid "
                "not in only list, thus skipped",
                end="\n"
            )
            continue

        # properties, get the mark number
        # print("")
        # build list of related property sets
        psets = getIfcPropertySets(ifcfile, pid)
        # print(psets)
        # build dict of properties
        ifc_properties = {}
        rebar_mark_number = 0
        ifc_properties = getIfcProperties(ifcfile, pid, psets, ifc_properties)
        # print(ifc_properties)
        # get the mark number (Position number)
        for key, value in ifc_properties.items():
            pset, pname, ptype, pvalue = getPropertyData(
                key, value,
                {"Debug": True}
            )
            if (
                pset == "Allplan_ReinforcingBar"
                and pname == "Position number"  # need to be Position not Mark!
            ):
                rebar_mark_number = pvalue
        # print(rebar_mark_number)
        # print("")
        # for debuging, TODO some Parameter to only import certain mark numbers
        # if rebar_mark_number != 3:
        #     continue

        # get the radius and the IfcCurve (Directrix) out of the ifc
        ifc_shape_representation = rebar.Representation.Representations[0]
        item_ifc_shape_representation = ifc_shape_representation.Items[0]
        mapping_source = item_ifc_shape_representation.MappingSource
        ifc_swept_disk_solid = mapping_source.MappedRepresentation.Items[0]
        radius = ifc_swept_disk_solid.Radius * length_scale
        # print(radius)
        entity_polyline = ifc_swept_disk_solid.Directrix

        # sweep path
        # get the geometry out of the IfcCurve (Directrix) and create a Wire
        cr = ifcopenshell.geom.create_shape(settings, entity_polyline)
        brep = cr.brep_data
        sweep_path = Part.Shape()
        sweep_path.importBrepFromString(brep)
        sweep_path.scale(1000.0)  # IfcOpenShell always outputs in meters

        # does it makes sense to check if the sweep_path and Radius
        # really are the same if mark number equals (yes, thus TODO)
        base_placement = FreeCAD.Placement()
        if rebar_mark_number not in base_rebars:
            # create a new rebar shape
            wire = Draft.makeWire(sweep_path.Wires[0])
            rebar_shape = archadd.BaseRebar(
                wire,
                diameter=2*radius,
                mark=rebar_mark_number,
                name="BaseRebar_Mark_"+str(rebar_mark_number)
            )
            rebar_shape.IfcProperties = ifc_properties
            rebar_objs.append(rebar_shape)
            base_rebars[rebar_mark_number] = rebar_shape
        else:
            # get the relative placement between
            # the base wire (the one in base_rebars already)
            # the sweep_path
            base_wire_obj = base_rebars[rebar_mark_number].Base
            print(base_wire_obj.Name)
            base_placement = get_relative_placement(
                base_wire_obj.Shape,
                sweep_path
            )
            # print(base_placement)

        # reinforcement made out of the imported rebar
        # coord placements
        vec_base_rebar = []
        for ifc_mapped_item in ifc_shape_representation.Items:
            ifc_cartesian_point = ifc_mapped_item.MappingTarget.LocalOrigin
            coord = ifc_cartesian_point.Coordinates
            co_vec = vec(
                coord[0] * length_scale,
                coord[1] * length_scale,
                coord[2] * length_scale
            )
            vec_base_rebar.append(co_vec)
        # print("\n{}".format(vec_base_rebar))

        # check if we have a linear distribution
        is_linear_distribution = False
        space_one = 0
        if len(vec_base_rebar) > 1:
            # edge from first point to last point
            ed = Part.Edge(Part.LineSegment(
                vec_base_rebar[0],
                vec_base_rebar[-1])
            )
            # spacing between first and second point
            space_one = vec_base_rebar[1] - vec_base_rebar[0]
            for i, co_vec in enumerate(vec_base_rebar):
                # check distance point to edge
                dist = ed.distToShape(Part.Vertex(co_vec))[0]
                if dist > 2:
                    # 2 mm, much better would be some dimensionless value
                    break
                # check spaceing, if they are constant
                if i > 0:
                    space_i = vec_base_rebar[i] - vec_base_rebar[i-1]
                    difference_length = (space_one - space_i).Length
                    if difference_length > 2:
                        # 2 mm, much better would be some dimensionless value
                        break
            else:
                is_linear_distribution = True

        # get placement for first distribution bar
        relplacement_firstbar = rebar.ObjectPlacement.RelativePlacement
        coord_firstbar = relplacement_firstbar.Location.Coordinates
        vec_firstbar = vec(
            coord_firstbar[0] * length_scale,
            coord_firstbar[1] * length_scale,
            coord_firstbar[2] * length_scale
        )
        firstbar_pl = FreeCAD.Placement(
            vec_firstbar,
            FreeCAD.Rotation(vec(0, 0, 1), 0),
            vec(0, 0, 0)
        )

        marker_size = 25
        lattice_placement = None
        if (
            is_linear_distribution is True
            and REINFORCEMENT_LATTICE is True
        ):
            # linear lattice2 distribution
            print("Linear distribution found")
            # print(len(vec_base_rebar))
            # print(space_one)
            space_length = space_one.Length
            la = lattice2LinearArray.makeLinearArray(name="LinearArray")
            # SpanN ... put in Count
            # Step will be calculated
            # SpanStep ... put in Step (space between rebars)
            # Count will be calculated
            la.GeneratorMode = "SpanStep"
            # https://forum.freecadweb.org/viewtopic.php?f=22&t=37657#p320586
            la.Alignment = "Justify"
            la.SpanEnd = (len(vec_base_rebar) - 1) * space_length
            la.Step = space_length
            la.MarkerSize = marker_size
            # direction of linear lattice2 placement
            la.Dir = space_one
            # do not change the orientation of the little planes
            # https://forum.freecadweb.org/viewtopic.php?f=22&t=37893&p=322427#p322421
            la.OrientMode = "None"
            lattice2Executer.executeFeature(la)
            la.Placement = firstbar_pl
            if la.Count != len(vec_base_rebar):
                print(
                    "Problem: {} != {}"
                    .format(la.Count, len(vec_base_rebar))
                )
            lattice_placement = la
        if (
            is_linear_distribution is True
            and REINFORCEMENT_LATTICE is False
        ):
            # linear reinforcement
            if space_one == 0:
                continue  # handle a reinforcement with one rebar
            amount = len(vec_base_rebar)
            spacing = space_one.Length
            # distance = (len(vec_base_rebar) - 1) * spacing

            archadd.ReinforcementLinear(
                rebar_shape,
                amount=amount,
                spacing=spacing,
                direction=space_one,
                base_placement=firstbar_pl.multiply(base_placement),
                # name="Reinforcement_"+str(reinforcement_counter)
                name="ReinforcementLinear_"+str(pid)
            )

        else:
            # custom lattice placement for every rebar of this distribution
            print("custom distribution found")
            custom_pls = []
            for co_vec in vec_base_rebar:
                custom_pl = lattice2Placement.makeLatticePlacement(
                    name=str(ifc_cartesian_point.id())
                )
                custom_pl.PlacementChoice = "Custom"
                custom_pl.MarkerSize = marker_size
                lattice2Executer.executeFeature(custom_pl)
                custom_pl.Placement = FreeCAD.Placement(
                    co_vec,
                    FreeCAD.Rotation(vec(0, 0, 1), 0),
                    vec(0, 0, 0)
                )
                custom_pls.append(custom_pl)

                # lattice array placement from custom lattice placements
                cpa = lattice2JoinArrays.makeJoinArrays(
                    name="CustomPlacementArray"
                )
                cpa.Links = custom_pls
                cpa.MarkerSize = marker_size
                lattice2Executer.executeFeature(cpa)
                cpa.Placement = firstbar_pl
                lattice_placement = cpa
                if FreeCAD.GuiUp:
                    for child in cpa.ViewObject.Proxy.claimChildren():
                        child.ViewObject.hide()

        if lattice_placement is not None:
            # lattice2 reinforcement
            archadd.ReinforcementLattice(
                rebar_shape,
                lattice_placement,
                base_placement,
                # name="Reinforcement_"+str(reinforcement_counter)
                name="ReinforcementLattice_"+str(pid)
            )

        reinforcement_counter += 1
        # print("")

    FreeCAD.ActiveDocument.recompute()
    # End reinforcements loop

    if FreeCAD.GuiUp:
        FreeCADGui.activeDocument().activeView().viewAxometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")
    return doc


# helper
def get_relative_placement(shape1, shape2):
    """returns the placement that must be
    applied to shape1 to move it to shape_2"""
    # https://forum.freecadweb.org/viewtopic.php?f=22&t=44880
    # Assuming that the first 3 vertexes of the shape
    # correctly define a plane (not coincident, nor colinear)
    plane1 = Part.Plane(*[v.Point for v in shape1.Vertexes[0:3]])
    plane2 = Part.Plane(*[v.Point for v in shape2.Vertexes[0:3]])
    pl1 = FreeCAD.Placement(plane1.Position, plane1.Rotation)
    pl2 = FreeCAD.Placement(plane2.Position, plane2.Rotation)
    return pl2.multiply(pl1.inverse())


def get_prj_unit_length_scale(ifcfile):
    # get the length scale facter from of unit of the ifc file
    # new Allplan exporter uses milli meter
    # old Allplan exporter uses meter
    prj_units = ifcfile.by_type("IfcProject")[0].UnitsInContext.Units
    length_scale = 1.0
    found_length_unit = False
    for u in prj_units:
        if u.UnitType == "LENGTHUNIT":
            if found_length_unit is False:
                found_length_unit = True
                # print(u.Prefix)
                # print(u.Name)
                if u.Prefix == "MILLI" and u.Name == "METRE":
                    pass
                elif u.Prefix is None and u.Name == "METRE":
                    length_scale = 1000  # convert meter into mille meter
                else:
                    print(
                        "Not known length unit found, "
                        "set attibute length scale to 1.0"
                    )
                    print(u)
            else:
                print(
                    "Two LENGTHUNIT defined, "
                    "this is not allowed in IFC-Standard."
                )
    # print("Length scale = {}\n".format(length_scale))
    return length_scale
