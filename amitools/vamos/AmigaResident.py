class AmigaResident:
  
  match_word = 0x4afc
  
  RTF_AUTOINIT = 1<<7
  
  NT_LIBRARY = 9
  
  INIT_BYTE_B = 0xa0
  INIT_BYTE_W = 0xe0
  INIT_WORD_B = 0x90
  INIT_WORD_W = 0xd0
  INIT_LONG_B = 0x80
  INIT_LONG_W = 0xc0
  INIT_END = 0
  
  # return array of resident structure addresses
  def find_residents(self, region, mem):
    addr = region.addr
    end = region.addr + region.size
    finds = []
    a = mem.access
    while addr < end:
      w = a.r16(addr)
      if w == self.match_word:
        ptr = a.r32(addr+2)
        if ptr == addr:
          # found a resident
          res = {
            'addr':addr,
            'flags':a.r8(addr+10),
            'version':a.r8(addr+11),
            'type':a.r8(addr+12),
            'pri':a.r8(addr+13),
            'name_ptr':a.r32(addr+14),
            'id_ptr':a.r32(addr+18),
            'init_ptr':a.r32(addr+22),
            'mem':mem
          }
          # eval values
          res['auto_init'] = res['flags'] & self.RTF_AUTOINIT == self.RTF_AUTOINIT
          res['name'] = a.r_cstr(res['name_ptr'])
          res['id'] = a.r_cstr(res['id_ptr'])
          
          finds.append(res)
          skip = a.r32(addr+6)
          addr = skip
        else:
          addr += 2
      else:
        addr += 2
    return finds
  
  # create a memory block with the auto init data
  def read_auto_init_data(self, res, all_mem):
    # make sure its auto init
    if not res['auto_init']:
      return False
    # read auto init params
    addr = res['init_ptr']
    mem = res['mem']
    a = all_mem.access
    res['dataSize'] = a.r32(addr)
    res['vectors_ptr'] = a.r32(addr+4)
    res['struct_ptr'] = a.r32(addr+8)
    res['init_code_ptr'] = a.r32(addr+12)
    
    # parse vectors, structs
    res['vectors'] = self.parse_vectors(res['vectors_ptr'], all_mem)
    res['struct'] = self.parse_struct(res['struct_ptr'], all_mem)
    
    return True
  
  def parse_struct(self, addr, mem):
    res = []
    if addr == 0:
      return res
    a = mem.access
    while True:
      cmd = a.r8(addr)
      print "%08x: %02x" % (addr,cmd)
      if cmd == self.INIT_END:
        break
      elif cmd == self.INIT_BYTE_B:
        off = a.r8(addr+1)
        val = a.r8(addr+2)
        addr += 4
        res.append((off,val,0))
      elif cmd == self.INIT_BYTE_W:
        off = a.r16(addr+2)
        val = a.r8(addr+4)
        addr += 6
        res.append((off,val,0))
      elif cmd == self.INIT_WORD_B:
        off = a.r8(addr+1)
        val = a.r16(addr+2)
        addr += 4
        res.append((off,val,1))
      elif cmd == self.INIT_WORD_W:
        off = a.r16(addr+2)
        val = a.r16(addr+4)
        addr += 6
        res.append((off,val,1))
      elif cmd == self.INIT_LONG_B:
        off = a.r8(addr+1)
        val = a.r32(addr+2)
        addr += 6
        res.append((off,val,2))
      elif cmd == self.INIT_LONG_W:
        off = a.r16(addr+2)
        val = a.r32(addr+4)
        addr += 8
      else:
        raise ValueError("Invalid parse_struct command: %02x" % cmd)
  
  def parse_vectors(self, addr, all_mem):
    a = all_mem.access
    is_word = (a.r16(addr) == 0xffff)
    vec = []
    # 16 bit offsets
    if is_word:
      base = addr
      addr += 2
      while True:
        off = a.r16(addr)
        addr += 2
        if off == 0xffff:
          break
        if off & 0x8000 == 0x8000:
          abs_addr = base + 0xfffe - off
        else:
          abs_addr = base + off
        vec.append(abs_addr)
    # 32 bit pointers
    else:
      while True:
        off = a.r32(addr)
        addr += 4
        if off == 0xffffffff:
          break
        vec.append(off)
    return vec

  # create memory block with jump vectors and pos size
  # store base_addr of library
  def setup_struct(self, res, mem, base_addr):
    structure = res['struct']
    for s in structure:
      addr = base_addr + s[0]
      mem.access.write_mem(s[2], addr, s[1])

  def init_lib(self, res, memlib, base_addr):
    a = memlib.access
    a.w_s("lib_Node.ln_Type", res['type'])
    a.w_s("lib_Node.ln_Pri", res['pri'])
    a.w_s("lib_Node.ln_Name", res['name_ptr'])
    a.w_s("lib_Flags", res['flags'])
    a.w_s("lib_NegSize", memlib.neg_size)
    a.w_s("lib_PosSize", memlib.pos_size)
    a.w_s("lib_Version", res['version'])
    a.w_s("lib_IdString", res['id_ptr'])
    self.setup_struct(res, memlib, base_addr)


