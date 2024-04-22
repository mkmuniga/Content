sub get_register_settings
{

    my %headers = (
        'TIME' => {
        'type' => 'BIGINT UNSIGNED',
        },

        'VALUE' => {
        'type' => 'BIGINT UNSIGNED',
        'formatting' => '%016lX',
        },
        
    );

    my $header_title_selector = 'TYPE';
    my $override_header_sets='#header,,TIME,UNIT,SIGNAL_PATH,TYPE,REG,FIELD,VALUE';
      return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, 
           \@merge_cells_row_regular_expressions, $skip_row_prefix_string , $skip_row_suffix_string, $override_header_sets, $column_separator ,$skip_row_regex_string);
}


add_user_setting_entry('^register_cbo_trk*$', \&get_register_settings);
