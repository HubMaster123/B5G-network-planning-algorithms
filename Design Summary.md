# Redundant Pathways GA

## Representation
Variable-length nested list: one group of k paths per demand. Each path is a sequence of node IDs. 
(Could be changed to a set. Order of paths within a demand currently preserved as a list.)

## Initialisation. 

- **Pure GA**: Mixture of Shortest paths and random walks. 
- **Hybrid**: Seeded from a pool of up to 6 k-shortest paths. 

## Fitness

```
Fitness = Total Cost + Overlap Penalty - (Resilience * 8000)
```

- **Overlap Penalty** = 10000 per shared edge within a demand + 20,000 per invalid path. 
- **Resilience** = Fraction of paths still connected after removing two random edges (Stochastic)

## Operators
- **Selection**: Tournament (size 3)
- **Crossover**: Two-point on path groups (whole demand gropus are swapped)
- **Mutation**: Index-shuffling only (reorders existing paths; **does not create new pathways**)

## Constraint Handling
Encouraged a initialisation. Enforced mainly by heavy penalties in the fitness function. No repair operator after crossover/mutation. 

## Known Limitations (for discussion)
1 - **Mutation is weak** - Only shuffles existing material. 
2 - **Constraint handling relies solely on penalties** - Might be inefficient. 
3 - **Resilience term is stochastic** - Meaning random , probabilistic, or chance based. Meaning my algorithm cannot be know as 100% certainty in future. Only supported by probability. Inaccurate. 
4 - Regenerative Repair Operator are not present in the current code. 

## Next steps
1 - How to improve mutation so it can generate new pathways. 
2 - Whether ot keep penalty-only constraints or add repair. 
3 - List vs set for path groups. 
4 - Whether to add a simple GA baseline comparison. 
5 - Input a regenerative repair operator that actually works. Since mine does not. 

## Overlap and Crossover

Proposition to Julien. 
1 - **Crossover**: Keep the current group-level two-point crossover, but add a **greedy least-overlap selection step afterwards.**
2 - **Repair**: Add a simple **regenerative repair* that replaces any invalid path with a shortest path. 
3 - **Encoding**: Describe it as a set in the thesis, keep a list in the code. 
4 - **Fitness**: Keep the current structure for now, but note that the large constant penalties may later be softened once repair is in place. 

## Friday Message
So, following our messages last week. I think these refinements make sense. 

The chromosome will be described as a set of paths per demand in the thesis with order not mattering. While the implementation will retain a list for compatibility with DEAP. The existing two-point crossover that swaps whole path groups will be kept, and I have updated it in Overleaf. To reduce the overlap that this crossover can produce, I will add a greedy-post processing step that selects, for each demand, the k paths with the least edge overlap. In addition, to address the problem of infeasible offspring simply being eliminated, I propose introducing a simple regenerative repair operator: after crossover and mutation, any invalid or disconnected path is replaced with a valid shortest path between the correct source and target. This operator directly supports Sub-question 1.1and should improve the algorithm's ability to explore the search space. Let me konw if this is the right direection before I start implementing :)