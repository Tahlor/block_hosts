# block_hosts
Block websites using the hosts file on Linux

    block 0 - nothing
    block 1 - block Twitter/linkedin
    block 2 - block news/shopping
    block 3 - block email

    # unblock
    unblock 2 - this is the same as block 1
    we're not really in a block/unblock paradigm anymore, so much as a block-level paradigm

## Set cron job
    sudo crontab -e
    
    0 * * * * python3 /media/data/GitHub/personal_projects/block_hosts/block.py --unblock
    5 * * * * python3 /media/data/GitHub/personal_projects/block_hosts/block.py 


## Run

    sudo python3 /media/data/GitHub/personal_projects/block_hosts/block.py
    sudo python3 /media/data/GitHub/personal_projects/block_hosts/block.py --unblock 

    
## VOLUME
You can either send that HUGE powershell command, or set it up in your "powershell" bashrc.

    @echo off
    # Create profile
    set "ps1_path=%USERPROFILE%\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
    if not exist "%USERPROFILE%\Documents\WindowsPowerShell" mkdir "%USERPROFILE%\Documents\WindowsPowerShell"
    (echo # $PROFILE script) > "%ps1_path%"

    # Add Volume Script to profile
    (echo . `"%USERPROFILE%\bashrc\windows\alias_scripts\profile.ps1`" ) >> "%ps1_path%"

## WINDOWS - choose a different sound when at the office
    on_work_network: Right now just checks for the DNS server; if I'm at the office/on the VPN, it will beep instead of talking 
    
    
# Block Hosts Utility

Block Hosts Utility is a Python-based tool that manipulates your system's hosts file to block distracting websites based on configurable blocking levels. It is designed to help improve productivity by restricting access to designated sites during work intervals while allowing for controlled breaks.

## Features

- **Website Blocking by Level:**  
  The tool categorizes websites into different levels (e.g., level0, level1, level2, etc.). You can choose a blocking intensity with the `--level` option so that websites from that level and below are blocked.

- **Unblocking Options:**  
  - **`--unblock`:** Disable website blocking for the current session by setting the block level to 0.  
  - **`--unblock_all`:** Remove all website blocking rules from your hosts file, reverting it to its default state.  
  - **`--site` / `--youtube`:** Unblock a specific website or YouTube separately.

- **Work/Break Mode:**  
  - **`--break_mode`:** Enter a cyclical work/break mode by providing two comma‑separated values (work duration and break duration, in minutes). For example, `--break_mode 25,5` starts a cycle of 25 minutes of work and 5 minutes of break.
  - **`--break_level`:** Specify the blocking level during break intervals (default is 1, which is typically less restrictive).

- **Lunch Break Mode:**  
  With the `--lunch` option (default 30 minutes), the tool temporarily disables blocking, allowing you to have an uninterrupted lunch break.

- **Interactive Prompts and Notifications:**  
  The tool offers speech notifications and interactive prompts via either graphical message boxes (using Tkinter) or command-line prompts. These behaviors can be modified with:
  - **`--skip_confirm_break` & `--skip_confirm_work`:** Skip confirmation dialogs for break and work transitions.
  - **`--dont_use_message_boxes`:** Force the use of CLI prompts instead of graphical dialogs.
  - **`--mute`:** Mute any speech notifications.

- **Platform Compatibility:**  
  Automatically detects whether it’s running on Linux, Windows, or WSL. It adjusts the paths and system commands accordingly.

- **User Customization:**  
  Use the `--user` option to set a username for the session.

## Installation

1. **Clone the Repository:**
   \[
   git clone https://your.repo.url.git
   \]

2. **Install Dependencies:**
   Use pip to install the necessary packages:
   \[
   pip install tqdm requests
   \]  
   (Note: Tkinter is typically included with your Python installation.)

3. **Usage:**
   Run the tool from the command line. For example:
   - Block sites at level 3:  
     \[
     python block_hosts/block_v2.py --level 3 --block
     \]
   - Start work/break mode (25/5 minutes cycle):  
     \[
     python block_hosts/block_v2.py --break_mode 25,5 --break_level 1
     \]

## Command Line Options

- **`--level <integer>`**:  
  Set the blocking intensity level. Websites from levels up to this value will be blocked. (Default: 3)

- **`--unblock`**:  
  Disable website blocking by setting the block level to 0.

- **`--unblock_all`**:  
  Remove all website blocking rules and revert the hosts file to its initial state.

- **`--block`**:  
  Force blocking of websites using the specified level.

- **`--off`**:  
  Apply a blocking configuration based on the provided level (an alias for setting blocking level).

- **`--on`**:  
  Enable website blocking according to the specified block level.

- **`--break_mode <work_minutes,break_minutes>`**:  
  Enter work/break mode. Provide two comma-separated values for work and break durations (e.g., `25,5`).

- **`--break_level <integer>`**:  
  Specify the blocking level used during break intervals (default: 1; typically less restrictive).

- **`--lunch <minutes>`**:  
  Temporarily disable blocking for a lunch break of the specified duration (default: 30 minutes).

- **`--user <username>`**:  
  Specify the username for the session (default: "taylor").

- **`--youtube`**:  
  Unblock YouTube specifically. If no additional argument is provided, it defaults to "youtube".

- **`--site <website>`**:  
  Unblock a specific website by providing its URL or domain.

- **`--skip_confirm_break`**:  
  Skip the confirmation prompt before starting break intervals in break mode.

- **`--skip_confirm_work`**:  
  Skip the confirmation prompt before starting work intervals in break mode.

- **`--mute`**:  
  Mute speech notifications (disabling voice feedback).

- **`--dont_use_message_boxes`**:  
  Disable graphical message boxes and use command‑line prompts instead.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please submit issues or pull requests for any improvements or bugs.