# -*- coding: utf-8 -*-
#
# Ganeti backend configuration
###################################

# The RAPI endpoint and associated credentials to use
# for talking to the Ganeti backend.
GANETI_MASTER_IP = "10.0.0.1"
GANETI_CLUSTER_INFO = (GANETI_MASTER_IP, 5080, "username", "password")

# This prefix gets used when determining the instance names
# of Synnefo VMs at the Ganeti backend.
# The dash must always appear in the name!
BACKEND_PREFIX_ID = "snf-"

# The following dictionary defines deployment-specific
# arguments to the RAPI CreateInstance call.
# At a minimum it should contain the
# 'disk_template', 'os_provider', and 'hvparams' keys.
#
# More specifically:
# a) disk_template:
#    The disk template to use when creating the instance.
#    Suggested values: 'plain', or 'drbd'.
# b) os:
#    The OS provider to use (customized Ganeti Instance Image)
# c) hvparams:
#    Hypervisor-specific parameters (serial_console = False, see #785)
# d) If using the DRBD disk_template, you may want to include
#    wait_for_sync = False (see #835).
#
GANETI_CREATEINSTANCE_KWARGS = {
    'os': 'snf-image+default',
    'hvparams': {'serial_console': False},
    'wait_for_sync': False}