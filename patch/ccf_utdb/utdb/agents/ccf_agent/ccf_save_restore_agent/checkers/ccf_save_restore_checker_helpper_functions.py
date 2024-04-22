from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_defs import SaveRestoreTxn


def get_first_txn_after_time(txn_list, time):
    txns = [t for t in txn_list if t.time > time]
    if len(txns) == 0:
        return None
    return txns[0]

def get_save_restore_sr_command_pairs(time_ordered_sr_commands, all_save_restore_done_command):
    saves_by_group = {}
    list_of_save_restore_txn_pairs = []
    for sr_txn in time_ordered_sr_commands:
        if sr_txn.is_sr_command_save():
            for group in sr_txn.get_groups_from_sr_command():
                saves_by_group[group] = sr_txn
        else:
            restore_command = sr_txn
            for group in restore_command.get_groups_from_sr_command():
                save_command = saves_by_group[group]
                restore_done_txn = get_first_txn_after_time(all_save_restore_done_command, sr_txn.time)
                list_of_save_restore_txn_pairs.append(SaveRestoreTxn(save_command, restore_command, restore_done_txn, group))

    return list_of_save_restore_txn_pairs
