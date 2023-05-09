use base "installbasetest";
use strict;
use testapi;

sub run() {

    assert_screen "inst-bootmenu", 6;
    send_key 'ret';
 
}

1;

# vim: set sw=4 et:
