int add_checked(int param_1,int param_2)

{
  int iVar1;
  
  if ((param_1 < 0x3e9) && (param_2 < 0x3e9)) {
    iVar1 = param_1 + param_2;
  }
  else {
    iVar1 = -1;
  }
  return iVar1;
}

