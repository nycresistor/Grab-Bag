use <MCAD/regular_shapes.scad>

module m5_nut_mount(depth) {
	bolt_len = 20;
	nut_depth = 4;
	nut_radius=4.6;
	clr = 0.1;
	union() {
		// Cylinder for M5 bolt to pass through
		translate([0,(bolt_len-depth)/2,0]) rotate([90,0,0])
			cylinder(r=2.5,h=bolt_len+depth,center=true);
		// Position of nut
		translate([0,nut_depth/2,0]) rotate([90,90,0])
		hexagon_prism(height=nut_depth+clr,radius=nut_radius);
		translate([0,0,10])
		cube(size=[nut_radius*sqrt(3),nut_depth+2*clr,20],center=true);
	}
}

h=20;
rod_r=6.06;

intersection() {
	translate([0,0,-h/2]) hexagon_prism(height=h,radius=rod_r);
	translate([rod_r*1.5,0,0]) cube(size=[rod_r*4,rod_r*4,h+2],center=true);
}

translate([-10,0,0]) rotate([0,0,90]) m5_nut_mount(10);

