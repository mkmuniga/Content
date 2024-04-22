sub get_cpurequest_settings
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
    my @header_title_selector_to_headers_set_name = ();
    my $merge_cells_headers_set_name_given = '';
    my @row_regular_expressions = ();
    my @merge_cells_row_regular_expressions = ();
    my $skip_row_prefix_string = '';
    my $skip_row_suffix_string = '';
    my $override_header_sets='#header,Common,TIME,UNIT|#header,ral_valid,SIGNAL_PATH,VALUE|#header,ral_invalid,SIGNAL_PATH';
    my $column_separator = '';
    my $skip_row_regex_string =  '';
    return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, 
           \@merge_cells_row_regular_expressions, $skip_row_prefix_string , $skip_row_suffix_string, $override_header_sets, $column_separator ,$skip_row_regex_string);
}


add_user_setting_entry('^ccf_val_utdb_ral.logdb$', \&get_cpurequest_settings);
