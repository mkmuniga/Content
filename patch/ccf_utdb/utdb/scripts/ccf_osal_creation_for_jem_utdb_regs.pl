#! /usr/intel/bin/perl
use lib "$ENV{RTL_PROJ_BIN}/perllib";
use ToolConfig;
my $onesourcebundle = &ToolConfig::ToolConfig_get_tool_path('onesourcebundle');
my $security_sai = &ToolConfig::ToolConfig_get_tool_path('security_sai');
my $cfi_registers = &ToolConfig::ToolConfig_get_tool_path('cfi_registers');


my $exit_status = system("${onesourcebundle}/OSAL/Spec2Osal/bin/Spec2Osal -L $ENV{WORKAREA}/tools/onesource/ ${security_sai}/lnl_a0/CCF_OneSourceSecurityDefinitions/ ${cfi_registers} --content_domain ccf_top_val_ContentDomain -O $ENV{MODEL_ROOT}/target/ccf/gen/osal  --flag use_attributes='*.Name,*.Parent,ComponentNode.LogicalInterfaces,RegisterNode.BitWidth,FieldNode.Msb,FieldNode.Lsb,FieldNode.IndustryAccess,ResetNode.Value,LogicalInterfaceNode.Space,LogicalInterfaceNode.PortId,LogicalInterfaceNode.BaseAddress,SystemNode.-,AddressMapNode.-,PhysicalInterfaceNode.-,BarDefinitionNode.-,PortNode.-,SaiAgentNode.-,SaiAgentGroupNode.-,SaiPolicyNode.-'");
if($exit_status) {
        printf "ERROR osal file generation failed";
            exit 1;
}

#/p/hdk/rtl/cad/x86-64_linux44/dt/OneSourceBundle/21.31.3p2/OSAL/Spec2Osal/bin/Spec2Osal

