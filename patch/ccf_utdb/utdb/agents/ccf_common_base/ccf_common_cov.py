
from val_utdb_components import  val_utdb_cov, val_utdb_cg, val_utdb_cp, val_utdb_auto_cp
from val_utdb_report import VAL_UTDB_MSG

class ccf_base_cov(val_utdb_cov):
    pass

class ccf_cg(val_utdb_cg):

    def build_range_span(self, maximum, minimum=0, exclude_list=[]):
        range_span = [str(i) for i in range(maximum) if (i >= minimum)]
        for exclude in exclude_list:
            range_span.remove(exclude)
        return range_span

    def is_bin_in_cp_span(self, cp_name, bin_name, print_msg_if_not_found=False):
        cp_item = self.cp_list[cp_name]

        if print_msg_if_not_found:
            if bin_name in cp_item.span_list:
                return True
            else:
                VAL_UTDB_MSG(time=0, msg="COVERAGE INFO - for cp- {} bin {} is not existing in span- {}".format(cp_name, bin_name, cp_item.span_list))
        else:
            return bin_name in cp_item.span_list

class ccf_cp(val_utdb_cp):
    pass

class ccf_auto_cp(val_utdb_auto_cp):
    pass