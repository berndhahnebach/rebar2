
# *****************************************************************************************************************
# like ifc export, two objects with IfcType = IfcReinforcementBar
# only the distribution count !

# *****************************************************************************************************************
# in TreeView:
# object _RebarShape
# has as child a wire or sketch object
# could have 1 to x more children, the _RebarDistribution objects (property link list)


# *****************************************************************************************************************
# class _RebarShape
# Attributes:
## Base (wire or Sketch)
## Diameter
## MarkNumber
## property link list _RebarDistributions (liste der groupe obj.)
## Material (in base _RebarShape class but implemented later)

# bending roll radius, concrete cover, predefined rebar shapes, materials, etc
# will be in classes which are inherited from base rebar shape class
# conversion from one inherited _RebarShape class in another one is not so importand
# much more importand is, the distribution should not get lost, if the _RebarShape sis exchanged

# PostitionNumber
# later there will be a rebar shape cut list object, a MarkNumber is unique in one rebar shape cut list
# really? it is possible to make a bill above the whole building, the results in dozens of MarkNumber 1
# for a rebar shape cut list which will go to the building site, the MarkNumber should be unique
# for a quantity report to know how much material is used it would be ok to have multiple MarkNumber in one rebar shape cut list
# the user should be able to explicit decide if in a rebar shape cut list multiple MarkNumbers are allowed
# May be a String should be used as MarkNumber,
# thus it can be integer, big or small ASCII character, rome letter
# but than another property or preference is needed to set the type mentioned above
# but for which rebar shapes, for a rebar shape cut list for the whole file for each rebar shape separately


# *****************************************************************************************************************
# class _RebarDistribution

# idea 1
# group of clones
# every distribution is a group of clones
# this would mean, _RebarDistribution can not be created without a _RebarShape
# is a special clone, scale = 1.0 and all clones of the distribution use the same base object
# Draft --> Clone, or a own clone object for rebar only?
# ATM much simpler just to take Draft --> clone obj
# would be fine anyway in TreeView if they could be expanded and than every rebar could be clicked and deleted
# on a special distribution like linear distribution (rebar distance or rebar count are given), the single objects could not be changed
# this would destroy the distribution, on recompute the deleted or changed rebars would reapear

# What if the distribution is not a real shape, but a coin representation, performance would gain on huge modells!
# what happes with ifc export in FreeCADCmd mode? Does it work than?

# idea 2
# same as current FreeCAD rebar implementation
# placement list with the placements of each rebar is calculated
# a compound from all rebars is made
# the compound is the distribution

# but to create the rebars with Python the place needs to be given somehow
# attribute placements, on recompute or first creation the whole distribution compound will be created
# list of placements

# later there will be class inherited for:
## linear distribution: wire and a attribute for distance or wire and attribute count
## vertex distribution: list of vertieces, on each vertex


# *****************************************************************************************************************
# should the rebar shape know the distribution objs?
# or
# should any distribution object know his rebar shape?
# use case
# there is a distributen and the user would like to change the diameter
# diameter of the PostionNumber (_RebarShape) will be changed --> all distributions which use this base _RebarShape will be changed
# if this is not wanted, this only one distribution to change gets a new _RebarShape thus a new MarkNumber and diameter will be changed

# How about the TreeView ... ?
# a rebar shape (MarkNumber) has all distributions as children
# distribution could be moved from one rebar shape to another (_RebarShape)
# that makes sense, but does it makes sense the other way?
# No not really, every distribution would have the rebar shape as child, this would be confusing


# *****************************************************************************************************************
# parametric?
# _RebarShape and _RebarDistribution depend on Shapes, which would be overwrite the rebar shape and rebar placements of the two base clases
# seams make sense


# *****************************************************************************************************************
# problem how to make the current class out of these two classes
# we have three objs, _Rebar, RebarShape, _RebarDistribution
# we have three make methods makeRebar, makeRebarDistribution, makeRebarShape
# means the new rebar works in parallel, and hopefully some rebar tools will be moved to the new rebar classes


# *****************************************************************************************************************
# my rebar IFC export topic, may be exchange the ifc because it has still buero name inside
# https://forum.freecadweb.org/viewtopic.php?f=39&t=35848
