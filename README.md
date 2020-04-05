## class _Reinforcement
### Idea 1 --> group of clones
+ every distribution is a group of clones
+ this would mean, _RebarDistribution can not be created without a _RebarShape
+ is a special clone, scale = 1.0 and all clones of the distribution use the same base object
+ Draft --> Clone, or a own clone object for rebar only?
+ ATM much simpler just to take Draft --> clone obj
+ would be fine anyway in TreeView if they could be expanded and than every rebar could be clicked and deleted
+ on a special distribution like linear distribution (rebar distance or rebar count are given), the single objects could not be changed
+ this would destroy the distribution, on recompute the deleted or changed rebars would reapear

+ What if the distribution is not a real shape, but a coin representation, performance would gain on huge modells!
+ what happes with ifc export in FreeCADCmd mode? Does it work than?

### Idea 2 --> same as current FreeCAD rebar implementation
+ placement list with the placements of each rebar is calculated
+ a compound from all rebars is made
+ the compound is the distribution

+ but to create the rebars with Python the place needs to be given somehow
+ attribute placements, on recompute or first creation the whole distribution compound will be created
+ list of placements

+ later there will be class inherited for:
    + linear distribution: wire and a attribute for distance or wire and attribute count
    + vertex distribution: list of vertieces, on each vertex


## Who is child of who?
+ should the rebar shape know the distribution objs?
+ or
+ should any distribution object know his rebar shape?
+ use case
+ there is a distributen and the user would like to change the diameter
+ diameter of the PostionNumber (_RebarShape) will be changed --> all distributions which use this base _RebarShape will be changed
+ if this is not wanted, this only one distribution to change gets a new _RebarShape thus a new MarkNumber and diameter will be changed

+ How about the TreeView ... ?
+ a rebar shape (MarkNumber) has all distributions as children
+ distribution could be moved from one rebar shape to another (_RebarShape)
+ that makes sense, but does it makes sense the other way?
+ No not really, every distribution would have the rebar shape as child, this would be confusing


## Parametric?
+ _RebarShape and _RebarDistribution depend on Shapes, which would be overwrite the rebar shape and rebar placements of the two base clases
+ seams to make sense


## Problem: how to make the current class (FreeCAD) out of these two classes
+ we have three objs, _Rebar, RebarShape, _RebarDistribution
+ we have three make methods makeRebar, makeRebarDistribution, makeRebarShape
+ means the new rebar works in parallel, and hopefully some rebar tools will be moved to the new rebar classes


## IFC export
+ https://forum.freecadweb.org/viewtopic.php?f=39&t=35848
+ onle the reinforcement objs should be exported not the base rebar objs
