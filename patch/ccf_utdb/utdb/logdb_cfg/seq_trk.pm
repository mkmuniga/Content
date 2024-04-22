sub get_seq_trk_settings
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

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^sequence_trk_uvm.log*$', \&get_seq_trk_settings);

