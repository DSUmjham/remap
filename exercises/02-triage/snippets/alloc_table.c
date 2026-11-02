void * alloc_table(uint param_1)

{
  void *pvVar1;
  
  pvVar1 = malloc((ulong)param_1 << 2);
  return pvVar1;
}

