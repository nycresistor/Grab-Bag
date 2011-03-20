use <MCAD/regular_shapes.scad>

module m5_nut_mount(depth) {
	bolt_len = 20;
	nut_depth = 4;
	nut_radius=4.6;
	union() {
		// Cylinder for M5 bolt to pass through
		translate([0,(bolt_len-depth)/2,0]) rotate([90,0,0])
			cylinder(r=2.5,h=bolt_len+depth,center=true);
		// Position of nut
		translate([0,nut_depth/2,0]) rotate([90,90,0])
		hexagon_prism(height=4,radius=nut_radius);
	}
}

m5_nut_mount(10);

