#!/bin/sh
#
switcher=/sbin/prime-switch

[ -f "$switcher" ] && exec "$switcher"
