use base "installbasetest";
use strict;
use testapi;

sub run() {
	assertscreen "inst-welcome", 120;
	send_key 'right';
	send_key 'ret';
	assert_screen "inst-langselection", 60;
	send_key 'alt-c';
}

sub load_inst_test() {
	loadtest "installation/bootloader.pm";
}
