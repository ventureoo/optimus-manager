import sys
import os
import socket
import json
from envs import SOCKET_PATH
from .. import var
from ..xorg import do_xsetup, is_xorg_running
from ..log_utils import set_logger_config, get_logger


def main():

    prev_state = var.load_state()

    if prev_state is None:
        return

    elif prev_state["type"] == "pending_pre_xorg_start":

        switch_id = var.make_switch_id()
        setup_kernel = True
        requested_mode = prev_state["requested_mode"]

    elif prev_state["type"] == "done":

        switch_id = prev_state["switch_id"]
        setup_kernel = False
        requested_mode = prev_state["current_mode"]

    else:
        return


    set_logger_config("switch", switch_id)
    logger = get_logger()

    try:
        logger.info("# Xorg pre-start hook")

        if os.environ.get("RUNNING_UNDER_GDM", False) and is_xorg_running():
            logger.info(
                "RUNNING_UNDER_GDM is set and Xorg is still running. "
                "Aborting this hook because it was likely called by GDM "
                "when closing its login screen.")
            sys.exit(0)

        logger.info("Previous state was: %s", str(prev_state))
        logger.info("Requested mode is: %s", requested_mode)

        command = {
            "type": "do_switch",
            "args": {
                "kernel_setup": setup_kernel,
            }
        }
        _send_switch_command(command)

        do_xsetup(requested_mode)

        state = {
            "type": "done",
            "switch_id": switch_id,
            "current_mode": requested_mode,
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:

        logger.exception("Xorg pre-start setup error")

        state = {
            "type": "pre_xorg_start_failed",
            "switch_id": switch_id,
            "requested_mode": requested_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Xorg pre-start hook completed successfully.")

def _send_switch_command(command):
    msg = json.dumps(command).encode('utf-8')

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(SOCKET_PATH)
        client.send(msg)
        client.close()

    except (ConnectionRefusedError, OSError):
        print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
              "\nYou can enable and start it by running those commands as root :\n"
              "\nsystemctl enable optimus-manager.service\n"
              "systemctl start optimus-manager.service\n" % SOCKET_PATH)
        sys.exit(1)

if __name__ == "__main__":
    main()
