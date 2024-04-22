import os
import sys 
from typing import List, Tuple, Iterator, Dict

one_source_bundle = os.environ.get('ONE_SOURCE_BUNDLE')
osal_lib_path =  os.path.join(one_source_bundle ,'OSAL/OSALPython3Lib/release_dir')
sys.path.append(osal_lib_path)

from typing import List
from cached_property import cached_property
import OSALLib3
from OSALLib3.OSALClasses import RegisterNode, AddressMapNode, ComponentNode, FieldNode, SystemNode, HdlPath, HdlPathInfo, ResetNode
from OSALLib3.OSALFactory import OSALFactory
from OSALLib3.OSALDict import OSALDict
import re

# This function is used to construct a string value representation from individual slices.
def _insert_slice_bin_string_into_bin_string(value, slice_value, slice_msb, slice_lsb)->str:
    # It is assumed slices are processed in arbitrary order, as opposed to, for example,
    # in order from most-signficant to least-significant. Therefore, need to deal with more
    # complex string manipulations.

    slice_size = slice_msb - slice_lsb + 1

    # Truncate/extend the slice value to be exactly of slice_size length
    if (len(slice_value) > slice_size):
        slice_value = slice_value[-slice_size:]
    elif (len(slice_value) < slice_size):
        extend_bit = "x" if (slice_value[0] == "x") else "0"
        slice_value = extend_bit*(slice_size - len(slice_value)) + slice_value

    # Extend the result value string if needed, to ensure the slice's bit positions are present.
    if len(value) <= slice_msb:
        value = "0"*(slice_msb - len(value) + 1) + value
    assert(len(value) > slice_msb)

    # Replace the relevant bit positions with the slice value
    left_to_the_slice = value[:len(value) - slice_msb - 1]
    rigth_to_the_slice = value[len(value)-slice_lsb:]
    value = left_to_the_slice + slice_value + rigth_to_the_slice
    return value


class PyRalField(FieldNode):  
    def __init__(self,d,**init_args)->None:
        """constructor to initialize PyRalField instance"""
        super().__init__(d,**init_args)
        self._desired = None 
        self._resolved_hdl_path = {}

    def get_full_name(self)->str:
        """function to get reg field object full name""" 
        if self.Parent == None:
            return self.Name
        else:
            return self.Parent.get_full_name()+"."+self.Name
    
    def set_value(self,value:int or hex)->None:
        """function to set field value"""
        size = (self.Msb - self.Lsb) + 1
        if not isinstance(value,int):
            value = int(value,16)
        self._desired = value & ((1<<size)-1)
    
    def get_value(self)->int:
        """function to get the last field value that was set/read, or the reset value as default"""
        if self._desired == None and self.Resets != None:
            # was not set/read yet, get the reset value
            self._desired = self.Resets[0].Value
        return self._desired
    
    def get_hdl_paths(self)->List[str]:
        if not self._resolved_hdl_path:
            if self.HdlPathInfo is None or self.HdlPathInfo.HdlPaths is None:
                return []
            top = PyRalDb()
            parent_path = self.Parent.get_parent_block().get_full_hdl_path()  # get the full hdl path of the register's parent block
            for path in self.HdlPathInfo.HdlPaths:
                signal = path.Signal
                if parent_path != "":
                    signal = parent_path + "." + signal
                default_logical_path_value = path.LogicalPathValue
                # Resolving user provided patterns in Hdlpath with corresponding values. 
                if top.config_dict != None:
                    for pattern,value in top.config_dict.items():   
                        if re.search(pattern, signal) :
                            signal = re.sub(pattern,value,signal)
                # Resolving HdlPath with default %Logical_Path% value. 
                if re.search('%.*.%', signal) and default_logical_path_value!=None: 
                    signal = re.sub('%.*.%',default_logical_path_value,signal)            
                if top.hdl_path_root != None and top.hdl_path_root != "":
                    signal = top.hdl_path_root+"."+signal
                # path Lsb/Msb should be relative to the register (not the field)
                path_lsb = path.get('Lsb',self.Lsb)
                path_msb = path.get('Msb',self.Msb)
                self._resolved_hdl_path[signal] = {'lsb' : path_lsb, 'msb' : path_msb}
        return self._resolved_hdl_path.keys()    

    def read(self,time:int,x_to_0=False)->int:
        """function to read register value based of time"""

        hdl_path = self.get_hdl_paths()
        if not hdl_path:
            raise ValueError(f"Could not read value of field: {self.get_full_name()}. No HDL Path is defined for this field")        

        if self.Parent._hdl_read_func == None:
            raise ValueError(f"Could not read value of field: {self.get_full_name()}. No value provider (e.g. a trace reader) exists for this field, possibly due to lack of data for the field or its hdl path: {self.get_hdl_paths()}")        

        value = 0 
        # This variable indicates whether at least one of attempts to retrieve an hdl-path's value
        # resulted in exception due X in the value. When this happens, the resultant value computed
        # by this function cannot be represented as integer anymore. In such case, the function
        # switches to constructing a binary string representation of the value, which is then
        # provided as part of the exception raised for the caller to handle.
        # The variable aggregates the individual exception objects caught when processing
        # individual hdl_paths, so that they can be returned to the caller with detailed info about
        # each faulty path.
        x_value_errors = []

        for path in hdl_path:
            path_props = self._resolved_hdl_path[path]
            # The offsets in path_props are relative to the whole register; here
            # they are adjusted to be relative to the field
            path_msb = path_props['msb'] - self.Lsb
            path_lsb = path_props['lsb'] - self.Lsb
            path_size = path_msb - path_lsb + 1

            try:
                path_value = self.Parent._hdl_read_func(path,time,x_to_0,self)
                path_value &= ((1 << path_size) - 1)                    

                if not x_value_errors:
                    # Constructing an integer result
                    value |= (path_value << path_lsb)
                else:
                    # Constructing a string result due to a previous error
                    value = _insert_slice_bin_string_into_bin_string(value, bin(path_value), path_msb, path_lsb)

            except PyRalXValueError as x_value_exc:
                if not x_value_errors:
                    # The first failure to get an integer value of an hdl-path.
                    # Switch to constructing a string representation of the overall value.
                    value = bin(value)[2:]

                # Store the exception. This serves as indication that string representation is being constructed now.
                assert(isinstance(x_value_exc.hdl_path_values, list) and x_value_exc.hdl_path_values)
                x_value_errors.extend(x_value_exc.hdl_path_values)
                # Insert the string value of the faulty hdl-path into the string at proper position.
                value = _insert_slice_bin_string_into_bin_string(value, x_value_exc.value_str, path_msb, path_lsb)

        if (x_value_errors):
            # Construct and raise a new exception
            new_exception = PyRalXValueError(
                f"Unknown value of '{self.get_full_name()}' at time {time}: {len(value)}'b{value}", 
                x_value_errors, value, time)
            raise new_exception

        self.set_value(value)
        return value

    def read_all(self,x_to_0=False)-> Tuple[int,int]:#(time,value):
        """ return an iterable of (time,value) tuples of all the field value change times and values """
        for time in self.get_value_change_times():
            yield (time, self.read(time, x_to_0))

    def get_value_change_times(self)-> List[int]:
        """ return a sorted unique list of times this field value has changed at """
        hdl_path = self.get_hdl_paths()
        if not hdl_path:
            raise ValueError(f"Could not read value change times of field: {self.get_full_name()}. No HDL Path is defined for this field")        

        if self.Parent._hdl_change_times_func == None:
            raise ValueError(f"Could not retrieve value change times for field: {self.get_full_name()}. No value provider (e.g. a trace reader) exists for this field, possibly due to lack of data for the field or its hdl path: {self.get_hdl_paths()}")

        value_change_times = set() # unique set of times
        for path in hdl_path:
            for time in self.Parent._hdl_change_times_func(path):
                value_change_times.add(time)

        return sorted(value_change_times)


class PyRalReg(RegisterNode):  
    def __init__(self,d,**init_args)->None:
        """constructor to initialize PyRalReg object instance"""
        super().__init__(d,**init_args)
        self._fields : Dict[str,PyRalField] = {}
        self._hdl_read_func = None
        self._hdl_change_times_func = None
        self._parent_block = None
        for field in self.Fields:
            self._fields[field.Name] = field
    
    def register_hdl_read_func(self,func_name:object)->None:
        """ function to register the hdl value read provider (e.g. jem) """
        self._hdl_read_func = func_name
       
    def register_hdl_change_times_func(self,func_name:object)->None:
        """ function to register the hdl value change times provider (e.g. jem), returns iterable of times"""
        self._hdl_change_times_func = func_name
        
    def get_parent_block(self):#-> PyRalCompBlock:
        """ function to return the parent component block because self.Parent may return the AddressMap """
        if self._parent_block == None:
            if isinstance(self.Parent,PyRalCompBlock):
                self._parent_block = self.Parent
            elif isinstance(self.Parent,AddressMapNode):
                self._parent_block = self.Parent.Parent
        return self._parent_block

    def get_full_name(self)->str:
        """function to get reg object full name. Can't use self.Parent because Parent is the AddressMap"""
        if self.get_parent_block() == None:
            return self.Name
        else:
            return self.get_parent_block().get_full_name()+"."+self.Name           
        
    def get_fields(self)->Iterator[PyRalField]:
        """function to get iterable on fields given a pyral reg object"""
        yield from self._fields.values()
    
    def get_field_by_name(self,fld_name:str)-> PyRalField:
        """function to get handle to PyRalField instance based on field name"""
        return self._fields.get(fld_name,None)

    def set_value(self,value:int or hex)->None:
        """function to set value for a given PyRalReg object"""
        if not isinstance(value,int):
            value = int(value,16)
        for field in self.Fields:
            field_lsb = field.Lsb
            field_msb = field.Msb
            size = (field_msb - field_lsb) + 1
            desired_value = ((value >> field_lsb) & ((1 << size) - 1))
            field.set_value(desired_value)

    def get_value(self)->int:
        """function to get the last register value that was set/read, or the reset value as default"""
        value=0
        for field in self.Fields:
            field_lsb = field.Lsb
            field_value = field.get_value()
            if field_value == None:
                return None
            value = value | (field_value << field_lsb)
        return value
       
    def get_hdl_paths(self)->List[str]:
        hdl_path = []
        for field in self.Fields:
            hdl_path.extend(field.get_hdl_paths())
        return hdl_path
    
    def read(self,time:int,x_to_0=False)->int:
        """function to read register value based of time"""
        value = 0 
        # This variable indicates whether at least one of attempts to retrieve an hdl-path's value
        # resulted in exception due X in the value. When this happens, the resultant value computed
        # by this function cannot be represented as integer anymore. In such case, the function
        # switches to constructing a binary string representation of the value, which is then
        # provided as part of the exception raised for the caller to handle.
        # The variable aggregates info from the individual exceptions caught when processing
        # individual hdl_paths, so that they can be returned to the caller with detailed info about
        # each faulty path.
        x_value_errors = []

        if self._hdl_read_func == None:
            raise ValueError(f"Could not read value of register: {self.get_full_name()}. No value provider (e.g. a trace reader) exists for this register, possibly due to lack of data for the register or its hdl path: {self.get_hdl_paths()}")

        for field in self.Fields:
            hdl_path = field.get_hdl_paths()
            if not hdl_path:
                raise ValueError(f"Could not read value of register: {self.get_full_name()}. No HDL Path is defined for the register's field {field.Name}")        
            
            for path in hdl_path:
                path_props = field._resolved_hdl_path[path]
                path_msb = path_props['msb']
                path_lsb = path_props['lsb']
                path_size = path_msb - path_lsb + 1

                try:
                    path_value = self._hdl_read_func(path,time,x_to_0,self)
                    path_value &= ((1 << path_size) - 1)                    

                    if not x_value_errors:
                        # Constructing an integer result
                        value |= (path_value << path_lsb)
                    else:
                        # Constructing a string result due to a previous error
                        value = _insert_slice_bin_string_into_bin_string(value, bin(path_value), path_msb, path_lsb)

                except PyRalXValueError as x_value_exc:
                    if not x_value_errors:
                        # The first failure to get an integer value of an hdl-path.
                        # Switch to constructing a string representation of the overall value.
                        value = bin(value)[2:]

                    # Store the exception. This serves as indication that string representation is being constructed now.
                    assert(isinstance(x_value_exc.hdl_path_values, list) and x_value_exc.hdl_path_values)
                    x_value_errors.extend(x_value_exc.hdl_path_values)
                    # Insert the string value of the faulty hdl-path into the string at proper position.
                    value = _insert_slice_bin_string_into_bin_string(value, x_value_exc.value_str, path_msb, path_lsb)

        if (x_value_errors):
            # Construct and raise a new exception
            new_exception = PyRalXValueError(
                f"Unknown value of '{self.get_full_name()}' at time {time}: {len(value)}'b{value}", 
                x_value_errors, value, time)
            raise new_exception

        self.set_value(value)
        return value

    def read_all(self,x_to_0=False)-> Tuple[int,int]:#(time,value)
        """ return an iterable of (time,value) tuples of all the register value change times and values """
        for time in self.get_value_change_times():
            yield (time, self.read(time, x_to_0))

    def get_value_change_times(self)-> List[int]:
        """ return a sorted unique list of times this register value has changed at """
        hdl_path = self.get_hdl_paths()
        if not hdl_path:
            raise ValueError(f"Could not read value change times of register: {self.get_full_name()}. No HDL Path is defined for the register")        
        
        if self._hdl_change_times_func == None:
            raise ValueError(f"Could not retrieve value change times for register: {self.get_full_name()}. No value provider (e.g. a trace reader) exists for this register, possibly due to lack of data for the register or its hdl path: {self.get_hdl_paths()}")

        value_change_times = set() # unique set of times
        for path in hdl_path:
            for time in self._hdl_change_times_func(path):
                value_change_times.add(time)

        return sorted(value_change_times)


class PyRalCompBlock(ComponentNode):
      """constructor to instantiate PyRalCompBlock instance""" 
      def __init__(self,d,**init_args) -> None:
          super().__init__(d,**init_args)
          self._regs = None
          self._hdl_path = ""


      def init_regs(self)-> None:
          self._regs : Dict[str,PyRalReg] = {}
          if self.AddressMaps:
              for addressmap in self.AddressMaps:
                  for register in addressmap.Registers:
                      self._regs[register.Name] = register
          
          if 'Registers' in self:
              for register in self['Registers']:
                  self._regs[register.Name] = register
      
      @property
      def regs(self)->Dict[str,PyRalReg]:
          if self._regs == None:
              self.init_regs()
          return self._regs    
      
      # Component block does not have child blocks. This API is added here for consistency with System block
      def get_blocks(self):
          return []

      def get_block_by_name(self,blk_name:str):#-> PyRalCompBlock
          """function to get block object by block name"""
          return self if (self.Name == blk_name) else None

      def get_reg_by_name(self,reg_name:str)-> PyRalReg:
          """function to get register object by register name"""
          return self.regs.get(reg_name,None)

      def get_full_name(self)->str:
          """function to get reg block full name"""
          if self.Parent == None:
              return self.Name
          else:
              return self.Parent.get_full_name()+"."+self.Name           
 
      def get_registers(self)->Iterator[PyRalReg]:
          """function to get an iterable on registers"""
          yield from self.regs.values()

      def set_hdl_path(self,path:str)->None:
          """path is a string representing this block's hdl_path"""
          self._hdl_path = path
      
      def get_full_hdl_path(self)->str:
          """returns the full hdl path of this block from the top block"""
          if self.Parent != None:
              parent_path = self.Parent.get_full_hdl_path()
              if parent_path != "":
                  if self._hdl_path != "":
                      return parent_path + "." + self._hdl_path
                  else:
                      return parent_path
          return self._hdl_path 
              

class PyRalSystemBlock(SystemNode):
      def __init__(self,d,**init_args)->None:
          """constructor to initialize PyRalSystemBlock instance"""
          super().__init__(d,**init_args)
          self._blocks : Dict = {}
          self._hdl_path = ""
         
          if 'Systems' in d: 
              for system in d['Systems']:
                  self._blocks[system.Name] = system
          if 'Components' in d:
              for component in d['Components']:
                  self._blocks[component.Name] = component
           
      def get_full_name(self)->str:
          """function to get reg block full name"""
          if self.Parent == None:
              return self.DefinitionName
          else:
              return self.Parent.get_full_name()+"."+self.Name           
    
      def get_block_by_name(self,blk_name:str):#->PyRalCompBlock or PySystemBlock
          """
          function to get a block object by name.
          The name can be a short block name or a hierarchical path relative to this block.
          In case of short block name, the first object found with matching name is returned. 
          The function Returns either PyRalSystemBlock or PyRalCompBlock object types
          """
          if self.Name == blk_name:
              return self        
          if blk_name in self._blocks:
              return self._blocks[blk_name]
          (subblk,sep,hier) = blk_name.partition(".")                     
          if hier == "":
              # search in all blocks
              for blk in self._blocks.values():
                  b = blk.get_block_by_name(blk_name)
                  # return the first matching block
                  if b != None:
                      return b
          else:
              # search in specific block
              if subblk in self._blocks:
                  return self._blocks[subblk].get_block_by_name(hier)              
          return None             
      
      def get_blocks(self):#->Iterator[PyRalCompBlock] or Iterator[PyRalSystemBlock]
          """returns an iterable of the local child blocks of this block"""
          yield from self._blocks.values()

      def get_reg_by_name(self,reg_name:str)-> PyRalReg:
          """
          function to get a register object by name.
          The name can be a short register name or a hierarchical path relative to this block.
          In case of short register name, the first object found with matching name is returned. 
          """
          (subblk,sep,hier) = reg_name.partition(".")                    
          if hier == "":
              # search in all blocks
              for blk in self._blocks.values():
                  rg = blk.get_reg_by_name(reg_name)
                  # return the first matching register
                  if rg != None:
                      return rg
          else:
              # search in specific block
              if subblk in self._blocks:
                  return self._blocks[subblk].get_reg_by_name(hier)         
          return None
      
      def get_registers(self)->Iterator[PyRalReg]:
          """returns an iterable of all the registers hierarchically under this block"""
          for block in self._blocks.values():
               yield from block.get_registers()

      def set_hdl_path(self,path:str)->None:
          """path is a string representing this block's hdl_path"""
          self._hdl_path = path
      
      def get_full_hdl_path(self)->str:
          """returns the full hdl path of this block from the top block"""
          if self.Parent != None:
              parent_path = self.Parent.get_full_hdl_path()
              if parent_path != "":
                  if self._hdl_path != "":
                      return parent_path + "." + self._hdl_path
                  else:
                      return parent_path
          return self._hdl_path 



#move mode to PyRalDb: mode="postprocess"
class PyRalDb:
    _instance = None
    def __new__(cls,*args,**kwargs)->None:
        """function to initialize PyRalDb as singleton"""
        if not cls._instance:
            cls._instance = object.__new__(cls,*args,**kwargs)
            cls._instance.top = None
            cls._instance.config_dict = None
            cls._instance.hdl_path_root = None
            cls._instance._osal_object = None
        return cls._instance    
    
    def __init__(self)->None:
        """ Constructor for initializing PyRalDb object """
        pass
        
    def config_hdlpath(self,config_dict:dict=None,hdl_path_root:str=None)->None:
        """config_dict provides patterns & values for `MACRO and %LOGICAL_PATH% replacement. hdl_path_root is the hdl_path of the top block instance"""
        self.config_dict = config_dict 
        self.hdl_path_root = hdl_path_root

    def build_regmodel(self,bson_path:str)->None:
        """ Builds regmodel based on bson_path provided by user and constructs py ral classes"""
        """ Returns either PyRalSystemBlock or PyRalCompBlock object types"""
        if self.top == None:
            self._build_ral_from_bjson(bson_path)
        return self.top
    
    def set_regmodel(self,top_block:PyRalSystemBlock or PyRalCompBlock)->None:
        self.top = top_block
                
    def get_regmodel(self)->PyRalSystemBlock or PyRalCompBlock:
        """ Returns pointer to top reg block"""
        """ Returns either PyRalSystemBlock or PyRalCompBlock object types"""
        return self.top
       
    def _create_reg(self,d:dict,**init_args)->PyRalReg:
        """ function to build pyral register node instances"""
        reg = PyRalReg(d,**init_args)
        return reg

    def _create_reg_field(self,d:dict,**init_args)->PyRalField:
        """ function to build pyral register field node instances"""
        field = PyRalField(d,**init_args)
        return field

    def _create_comp_block(self,d:dict,**init_args)->PyRalCompBlock:
        """ function to build component node instances"""
        comp = PyRalCompBlock(d,**init_args)
        return comp

    def _create_sys_block(self,d:dict,**init_args)->PyRalSystemBlock:
        """ function to build system node instances"""
        system = PyRalSystemBlock(d,**init_args)
        return system
    
    def _get_pyral_factory(self):
        factory = OSALFactory()
        factory.set_RegisterNode_creator(self._create_reg)
        factory.set_ComponentNode_creator(self._create_comp_block)
        factory.set_SystemNode_creator(self._create_sys_block)
        factory.set_FieldNode_creator(self._create_reg_field)
        return factory 
    
    def _build_ral_from_bjson(self,path:str)->None:
        """ Constructs ral hierarchy classes based on BJSON """
        factory = self._get_pyral_factory()
        #self._osal_object = OSALLib3.load(directory_path=path, factory=factory,partial_loading=True)
        self._osal_object = OSALLib3.load(directory_path=path, factory=factory)
        if self._osal_object.Top.Parent == None:
            self.top = self._osal_object.Top
    
            


"""" Value provider custom exception class """ 
class PyRalXValueError(Exception):
    def __init__(self, msg : str, hdl_path_values : List[Tuple[str,str]], value_str : str, timestamp : int = None)->None:
        self.msg = msg
        self.hdl_path_values = hdl_path_values
        self.value_str = value_str
        self.timestamp = timestamp

    def __str__(self)->str:
        return self.msg
       
