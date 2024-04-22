sub get_sm_settings
{
        my %headers = (
                'SIZE' => {
                        'type' => 'BIGINT',
                },

                'LOW_ADDRESS' => {
                        'type' => 'BIGINT UNSIGNED',
                        'formatting' => '%014lX',
                        'null-value' => '-',
                },
                 'HIGH_ADDRESS' => {
                        'type' => 'BIGINT UNSIGNED',
                        'formatting' => '%014lX',
                        'null-value' => '-',
                },


        );
        my $header_title_selector = '';
        my @header_title_selector_to_headers_set_name = ();
        my $merge_cells_headers_set_name_given = '';
        my @row_regular_expressions = ("(^DRAM|^MMIO|^REMAP_AREA)");
        my @merge_cells_row_regular_expressions = ();
    	my $skip_row_suffix_string = '';
    	my $skip_row_prefix_string = '';
	    my $column_separator ='';
        my $skip_row_regex_string = '';
        my $override_header_sets ='#header,SM,MEM_NAME:30,REGION_NAME:30,SUB_NAME:30,LOW_ADDRESS:30,HIGH_ADDRESS:30,SIZE:30';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^sm.log*$', \&get_sm_settings);

