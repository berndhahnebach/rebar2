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

__title__ = "FreeCAD min IFC importer based on Yorik van Havres IFC importer"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import os

import FreeCAD
from FreeCAD import Vector as vec

import Draft
import Part

import lattice2Executer
import lattice2JoinArrays
import lattice2LinearArray
import lattice2Placement
import rebar2

from exportIFC import getPropertyData
from importIFCHelper import decode as ifcdecode
from importIFCHelper import getIfcProperties
from importIFCHelper import getIfcPropertySets

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

    # global ifcfile # keeping global for debugging purposes
    filename = ifcdecode(filename, utf=True)
    ifcfile = ifcopenshell.open(filename)
    from ifcopenshell import geom
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_BREP_DATA, True)
    settings.set(settings.SEW_SHELLS, True)
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, False)
    settings.set(settings.INCLUDE_CURVES, True)
    settings.set(settings.EXCLUDE_SOLIDS_AND_SURFACES, True)

    rebars = ifcfile.by_type("IfcReinforcingBar")
    rebar_objs = []

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
                    length_scale = 1.0
                elif u.Prefix is None and u.Name == "METRE":
                    length_scale = 1000  # convert meter into mille meter
                else:
                    print(
                        "Not known length unit found, "
                        "set attibute length scale to 1.0"
                    )
                    print(u)
                    length_scale = 1.0
            else:
                print(
                    "Two LENGTHUNIT defined, "
                    "this is not allowed in IFC-Standard."
                )
    print("Length scale = {}\n".format(length_scale))

    # TODO: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # might be a distribution is only the first distribution
    # of many distributions of the mark
    # the attributes should be read to get the MarkNumber
    # equal MarkNumber should get the same
    # base goemetry as rebar shape
    # means these distributions should share a base rebar shape
    #
    # PROBLEM: the placement needs to be checked,
    # because the base rebar could be the same for
    # different distributions, but not the place in the orbit
    # than in distribution the placement needs to be
    # moved and turned global
    # see bsp example_04_vat.ifc
    #
    # Thus ATM any distribution gets his own rebar base shape
    # create groups for any rebar base shape (mark number)
    mark_numbers = []

    # rebars
    for pno, rebar in enumerate(rebars):
        pid = rebar.id()
        ptype = rebar.is_a()
        print("Product {} of {} is Entity #{}: {}, ".format(
            pno + 1,
            len(rebars),
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
        ifc_mark_number = 0
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
                and pname == "Position number"
            ):  # need to be Position here!
                ifc_mark_number = pvalue
        # print(ifc_mark_number)
        # print("")
        mark_numbers.append(ifc_mark_number)

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
        wire = Draft.makeWire(sweep_path.Wires[0])

        # rebar shape
        rebar_shape = rebar2.makeRebarShape(
            wire,
            diameter=2*radius,
            mark=ifc_mark_number,
            name="RebarShape_Mark_"+str(ifc_mark_number)
        )
        rebar_shape.IfcProperties = ifc_properties
        rebar_objs.append(rebar_shape)

        # rebar distribution
        # coord placements
        vec_pls = []
        for ifc_mapped_item in ifc_shape_representation.Items:
            ifc_cartesian_point = ifc_mapped_item.MappingTarget.LocalOrigin
            coord = ifc_cartesian_point.Coordinates
            co_vec = vec(
                coord[0] * length_scale,
                coord[1] * length_scale,
                coord[2] * length_scale
            )
            vec_pls.append(co_vec)
        # print("\n{}".format(vec_pls))

        # check if we have a linear distribution
        is_linear_distribution = False
        space_one = 0
        if len(vec_pls) > 1:
            # edge from first point to last point
            ed = Part.Edge(Part.LineSegment(vec_pls[0], vec_pls[-1]))
            # spacing between first and second point
            space_one = vec_pls[1] - vec_pls[0]
            for i, co_vec in enumerate(vec_pls):
                # check distance point to edge
                dist = ed.distToShape(Part.Vertex(co_vec))[0]
                if dist > 2:
                    # 2 mm, much better would be some dimensionless value
                    break
                # check spaceing, if they are constant
                if i > 0:
                    space_i = vec_pls[i] - vec_pls[i-1]
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
        if is_linear_distribution is True:
            # linear lattice2 distribution
            print("Linear distribution found")
            # print(len(vec_pls))
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
            la.SpanEnd = (len(vec_pls) - 1) * space_length
            la.Step = space_length
            la.MarkerSize = marker_size
            # direction of linear lattice2 placement
            la.Dir = space_one
            # do not change the orientation of the little planes
            # https://forum.freecadweb.org/viewtopic.php?f=22&t=37893&p=322427#p322421
            la.OrientMode = "None"
            lattice2Executer.executeFeature(la)
            la.Placement = firstbar_pl
            if la.Count != len(vec_pls):
                print("Problem: {} != {}".format(la.Count, len(vec_pls)))
            lattice_placement = la
        else:
            # custom lattice placement for every rebar of this distribution
            print("custom distribution found")
            custom_pls = []
            for co_vec in vec_pls:
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

        # rebar2 lattice2 distribution
        rebar2.makeRebarDistributionLattice(
            rebar_shape,
            lattice_placement,
            name="Distribution_No_"+str(ifc_mark_number)
        )

        # move rebar shape to the first bar of distribution
        rebar_shape.Placement = firstbar_pl

        # all_entities_group.addObject(rebar_shape)
        print("")
    FreeCAD.ActiveDocument.recompute()
    # End rebars loop

    groups = {}
    for no in sorted(list(set(mark_numbers))):
        groups[no] = FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroup",
            "MarkNo_" + str(no)
        )
        # print(groups[no].Name)
    for reb in rebar_objs:
        groups[reb.MarkNumber].addObject(reb)

    if FreeCAD.GuiUp:
        FreeCADGui.activeDocument().activeView().viewAxometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")
    return doc
