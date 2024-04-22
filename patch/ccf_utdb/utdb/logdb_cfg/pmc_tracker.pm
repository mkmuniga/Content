sub get_pmc_settings
{
        my %headers = (
                'TIME' => {
                        'type' => 'BIGINT',
                },

        );

        my $override_header_sets ='#header,PMC,TIME:15,Power_Status:15,Cstate:20,CcfPwrDnControlFsm:30,CcfPwrUpControlFsm:30,CcfGvControlFsm:30,LlcCtrlFsm:30,MonitorCpFsm:30,PmcLockFsm:30,SleepLevelFsm:30,SantaConnectFsm:30,ResourceOwnFsm:30';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^pmc_tracker.log$', \&get_pmc_settings);

