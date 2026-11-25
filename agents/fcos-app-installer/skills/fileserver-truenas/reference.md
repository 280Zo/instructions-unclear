# Facts the TrueNAS adapter relies on

Each fact comes from the official source linked under it, not from memory. Re-check a fact when its source changes, and add a new one here, with its link, when you start relying on it.

## Who may mount an NFS share

Documented: giving an NFS share a list of hosts or networks restricts access to the ones listed, and leaving the list empty allows all. Removing the host entry again lets every system reach the share. The Advanced Options hold Read-Only (prohibits writing), Maproot User and Maproot Group (map the root user's permissions and group to a chosen user and group) and Mapall User and Group (map every client). The adapter's `nfs_export` step therefore leaves an existing share's lists, Maproot and Read-Only settings alone, and only adds the VM's address to a Hosts list that already exists

Source: https://www.truenas.com/docs/scale/shares/nfs/addingnfsshares/ (sections "Adding NFS Share Networks and Hosts" and "Adjusting Access Permissions", read on the TrueNAS 28 development view of the page)
