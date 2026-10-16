# Figure captions

One sentence on what the panel shows, then the data source and n, then the one takeaway.

## `fig1_degree_bound_to_cross_term` (main text, \label{fig:setup})

The model, the two-qubit overlap constraint, a depth-6 colouring that fails it, and the depth-7 schedule that meets it. The lattice and the two circuit insets are built from data/fig1_scene.json; the violating overlap pair is data/fig1_violation.csv (bb72, N = 36, Delta = 6) and the depth-7 schedule is schedules/bb72_d7_inv.json. A depth-Delta colouring exists but cannot be proper: the two corners of one overlap pair take opposite orientations, so their parities do not cancel.

*the depth-6 colouring drawn is a global proper 6-edge-colouring of all 432 edges; only properness fails*  

## `fig2_why_six_layers_fail` (main text, \label{fig:mechanism})

The four ingredients of the lower bound, and the one change that makes depth six attainable. The staircase is built from data/fig2_scene.json; a + b = Delta + 1 is verified on all 417 enumerated schedules of data/lemma_checks.csv. F_L + F_R = 9 is odd while a proper schedule needs F_L = F_R, so depth Delta is impossible when the overlaps are two-qubit.

*gamma(i) is a property of the model (MODEL.md), not of a data file*  *the right-hand cap states the 2-height hypothesis of Theorem 15*  

## `fig3_where_depth6_is_attainable` (main text, \label{fig:sharpness})

Minimum depth of a proper schedule by collision structure. 664 instances with a recorded depth-6 outcome, read from data/coverage.csv; the even-order column is data/thm_six_coverage.csv and the certified share of the solver refutations is data/c1_odd_unobstructed_certs.csv. Two of the three columns are settled by a theorem for their whole class; the odd-order column is decided instance by instance and 30 are open.

*the even-order cells were merged: the 2-height lemma covers the whole class*  *the supplementary table is quoted by the number LaTeX printed, read from build_tex/main.aux*  

## `figS1_proof_map` (supplementary, \label{figS:proofmap})

What depends on what: the three general obstructions, the main chain and the depth-six chain. Counts are read from data/instances.csv, data/c1_final.csv and data/thm_six_coverage.csv; the largest enumerated modulus from templates/C1_m*.json. The three obstructions are parallel consequences of M_pi = 0; only the depth-six chain rests on computation.  The two corollaries of the mod-4 theorem quote data/cor3_hgp.csv, the template chain data/template_force.csv and the competitive codes data/pareto_front.csv.

*solid = proved, dashed = computational evidence, dotted = open*  

## `figS2_sweep_by_group` (supplementary, \label{figS:sweep})

Depth-6 outcome of the exhaustive sweep, by group and by the largest sum multiplicity S(delta). 1,441 instances of data/sweep.csv over six abelian groups of order at most 8. Only one sweep instance is UNSAT at depth 6, and no sweep group has distinct sums.

## `figS3_templates_by_q` (supplementary, \label{figS:templates})

Exhaustive epsilon-template outcome by twist modulus q. Every epsilon-vector at q = 2, 3, 4, 5, 6, 8 (144 to 9,216 per modulus) from templates/C1_m*.json; q = 7, 9–12 and 16 were not computed. No vector with |M| odd admits a depth-6 twisted schedule at any q.

*the figure aborts if the |M| odd row is ever non-zero*  

## `figS4_periods` (supplementary, \label{figS:periods})

Smallest proper divisor q* of N carrying a verified twisted schedule. The class-C1 instances data/coverage.csv records as satisfiable at depth 6, with q* from data/mstar.csv. Every q* found is even; 6 instances have no period within the cap.

*log scale with a count on every bar, so the small bars stay readable*  

## `figS5_theorem1_profile` (supplementary, \label{figS:mod4})

Where the componentwise mod-4 condition obstructs, and the resolved status of the same instances. 598 class-C1 instances joined from data/h1_predictions.csv and data/coverage.csv. Obstruction coincides exactly with the residue 2 and ord(d) odd on this set, and no obstructed instance is satisfiable.

*the figure aborts if an obstructed instance is drawn as SAT*  

## `figS6_certificates` (supplementary, \label{figS:certificates})

Cost of the depth-6 certificates, with and without the layer-reversal clause. The eight depth-6 refutations of data/results.csv paired with the reversal-clause-free runs of data/r4_no_reversal.csv. The refutations survive removal of the only symmetry-breaking clause, at a modest cost in time and proof size.

*MB = 10^6 bytes; Table I reports the values without the clause*  
