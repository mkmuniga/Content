sub get_upi_settings
{
        my %headers = (
                'TIME' => {
                        'type' => 'BIGINT',
                },

                'ADDRESS' => {
                        'type' => 'BIGINT UNSIGNED',
                        'formatting' => '%012lX',
                        'null-value' => '-',
                },

        );

        my $override_header_sets ='#header,UPI_VC,TIME:15,TID:20,LID:20,PID:20,RTID:10,HTID:10,MSG_CLASS:10,MSG_TYPE:20,ADDRESS:10,DNID:10,SNID:10,HNID:10,CNID:10,RNID:10,BE:10,DATA3:15,DATA2:15,DATA1:15,DATA0:15,TUNNEL_DATA1:15,TUNNEL_DATA0:15,TUNNEL_TYPE:20';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^upi_vc.log*$', \&get_upi_settings);

