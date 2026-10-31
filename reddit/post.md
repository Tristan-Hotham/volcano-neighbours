## Title

[OC] At least 147 million people live within 30 km of a volcano that has been active in the last 12,000 years. 76 volcanoes have a million or more neighbours, and the most crowded is beside Taipei

## Body

I mapped all 1,215 Holocene volcanoes in the Smithsonian's Global Volcanism Program database with the GVP's own figures for how many people live within 30 km of each. Simply adding them up gives 274 million, but that counts Naples twice (Vesuvius and Campi Flegrei are 24 km apart) and parts of Java ten times, so I also summed only volcanoes whose circles do not overlap: at least 147 million people, counting each person once. Indonesia alone has at least 42 million. The most crowded volcanoes are the Tatun group above Taipei (6.7m within 30 km), Michoacán-Guanajuato in Mexico (5.8m) and Tangkuban Parahu above Bandung (5.7m). 21 of the million-plus volcanoes have erupted since 2000. Caveats: the population figures are a fixed GVP snapshot, not current counts, and distance is not the same as hazard. Interactive map where you can click any volcano to draw its 10, 30 and 100 km rings: https://maps.tristanhotham.com/volcano-neighbours/

## Source comment

Source: Global Volcanism Program, Volcanoes of the World v. 5.3.5 (Smithsonian Institution, compiled by Venzke, E., https://volcano.si.edu/, accessed via GitHub mirrors) for volcanoes and last eruptions; population within 30 km from the GVP's v. 5.1.7 list. Plate boundaries: Bird (2003), PB2002, GeoJSON by Hugo Ahlenius, Nordpil. Outlines: Natural Earth. "At least" sums only volcanoes whose 30 km circles do not overlap, so it is a firm lower bound.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/volcano-neighbours/
Paper: https://doi.org/10.5281/zenodo.23847550
Blog post: https://blog.tristanhotham.com/2026/10/31/volcano-neighbours/
