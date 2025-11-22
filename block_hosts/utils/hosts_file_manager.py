"""
Manages the hosts file by maintaining a managed section (for block_hosts modifications)
and preserving an unmanaged section (user's custom entries).

The managed section is marked with BEGIN/END markers, and the unmanaged section
is backed up before each modification to preserve user changes.
"""
from pathlib import Path
import logging

logger = logging.getLogger("root")

MANAGED_SECTION_START_MARKER = "# BEGIN BLOCK_HOSTS MANAGED SECTION"
MANAGED_SECTION_END_MARKER = "# END BLOCK_HOSTS MANAGED SECTION"


def get_backup_path(hosts_path: Path) -> Path:
    """Get the path for backing up the unmanaged section of the hosts file."""
    hosts_path = Path(hosts_path)
    backup_dir = hosts_path.parent / ".block_hosts_backup"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir / "unmanaged_section_backup.txt"


def read_hosts_file(hosts_path: Path) -> tuple[str, str]:
    """
    Read the hosts file and split it into unmanaged and managed sections.
    
    Returns:
        tuple: (unmanaged_section, managed_section)
               unmanaged_section: Everything outside the managed markers
               managed_section: Content between the markers (without markers)
    """
    hosts_path = Path(hosts_path)
    
    if not hosts_path.exists():
        logger.info(f"Hosts file does not exist at {hosts_path}, treating as empty")
        return "", ""
    
    content = hosts_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if MANAGED_SECTION_START_MARKER in line:
            start_idx = i
        elif MANAGED_SECTION_END_MARKER in line:
            end_idx = i
            break
    
    if start_idx is None and end_idx is None:
        # No managed section exists, entire file is unmanaged
        return content, ""
    
    if start_idx is not None and end_idx is None:
        # Start marker found but no end marker - treat everything after start as managed
        logger.warning("Found start marker but no end marker, treating rest as managed")
        unmanaged = "".join(lines[:start_idx])
        managed = "".join(lines[start_idx + 1:])
        return unmanaged, managed.rstrip()
    
    if start_idx is None and end_idx is not None:
        # End marker found but no start marker - treat everything before end as unmanaged
        logger.warning("Found end marker but no start marker, treating before end as unmanaged")
        unmanaged = "".join(lines[:end_idx])
        managed = ""
        return unmanaged, ""
    
    # Both markers found
    unmanaged_before = "".join(lines[:start_idx])
    unmanaged_after = "".join(lines[end_idx + 1:])
    unmanaged = unmanaged_before + unmanaged_after
    managed = "".join(lines[start_idx + 1:end_idx])
    
    return unmanaged, managed.rstrip()


def backup_unmanaged_section(unmanaged_section: str, hosts_path: Path) -> None:
    """Back up the unmanaged section to a file (overwriting previous backup)."""
    backup_path = get_backup_path(hosts_path)
    backup_path.write_text(unmanaged_section, encoding='utf-8')
    logger.info(f"Backed up unmanaged section to {backup_path}")


def build_hosts_file_content(unmanaged_section: str, managed_section: str) -> str:
    """
    Build the complete hosts file content from unmanaged and managed sections.
    
    Args:
        unmanaged_section: User's custom entries (preserved)
        managed_section: Content to place between markers (our block entries)
    
    Returns:
        Complete hosts file content with markers
    """
    parts = []
    
    if unmanaged_section.strip():
        parts.append(unmanaged_section.rstrip())
        parts.append("")  # Empty line separator
    
    parts.append(MANAGED_SECTION_START_MARKER)
    if managed_section.strip():
        parts.append(managed_section)
    parts.append(MANAGED_SECTION_END_MARKER)
    
    return "\n".join(parts) + "\n"


def remove_keywords_from_managed_section(keywords: list[str], hosts_path: Path, use_sudo: bool = False, sudo_script_path: Path = None) -> None:
    """
    Remove lines containing any of the given keywords from the managed section only.
    
    Args:
        keywords: List of keywords to search for (case insensitive)
        hosts_path: Path to the hosts file
        use_sudo: If True, use sudo to write the file (for Linux)
        sudo_script_path: Path to the sudo write script (required if use_sudo is True)
    """
    import subprocess
    import tempfile
    
    hosts_path = Path(hosts_path)
    unmanaged_section, managed_section = read_hosts_file(hosts_path)
    
    if not managed_section:
        logger.info("No managed section found, nothing to remove")
        return
    
    managed_lines = managed_section.splitlines()
    filtered_lines = []
    
    for line in managed_lines:
        line_lower = line.lower()
        should_keep = not any(keyword.lower() in line_lower for keyword in keywords)
        if should_keep:
            filtered_lines.append(line)
    
    new_managed_section = "\n".join(filtered_lines)
    backup_unmanaged_section(unmanaged_section, hosts_path)
    complete_content = build_hosts_file_content(unmanaged_section, new_managed_section)
    
    if use_sudo:
        if sudo_script_path is None:
            raise ValueError("sudo_script_path is required when use_sudo is True")
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            tmp_file_path = Path(tmp_file.name)
            tmp_file_path.write_text(complete_content, encoding='utf-8')
        command = ["sudo", str(sudo_script_path), str(tmp_file_path), str(hosts_path)]
        subprocess.run(command, check=True)
        tmp_file_path.unlink()
    else:
        hosts_path.write_text(complete_content, encoding='utf-8')
    
    logger.info(f"Removed keywords {keywords} from managed section")


def write_managed_section_to_hosts_file(managed_content: str, hosts_path: Path) -> None:
    """
    Write the managed section to the hosts file, preserving the unmanaged section.
    
    This function:
    1. Reads the current hosts file
    2. Extracts the unmanaged section
    3. Backs up the unmanaged section
    4. Writes the new content with managed section replaced
    """
    hosts_path = Path(hosts_path)
    
    unmanaged_section, _ = read_hosts_file(hosts_path)
    backup_unmanaged_section(unmanaged_section, hosts_path)
    
    complete_content = build_hosts_file_content(unmanaged_section, managed_content)
    hosts_path.write_text(complete_content, encoding='utf-8')
    logger.info(f"Wrote managed section to {hosts_path}")

